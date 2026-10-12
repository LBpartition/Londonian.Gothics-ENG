"""Pixel-accurate text fitting for the VWF renderer.

wrap(text, box) -> list of lines that each fit box.max_px, or raises FitError.
Never truncates: anything that cannot fit in box.max_lines is a FitError listing
the string so it goes to human review.
"""
from dataclasses import dataclass
import vwf_patch
import font_patch


class FitError(Exception):
    pass


@dataclass(frozen=True)
class Box:
    name: str
    max_px: int      # ink width allowed per line, measured in-emulator
    max_lines: int
    space_code: int  # glyph code used for spaces in this renderer


# DRESS MODE description box: pen starts x=50, original JP ink ends x=200,
# frame inner edge x=207 (measured from captures/route_dress, test04_dress).
DRESS_DESC = Box("dress_desc", 151, 2, 0xFFFE)
# Narrow-font layout: pen moved to (44,141), line step 12 -> 3 lines, ink x44..203
# (box interior x41..206, y137..182; measured captures/test05_dress).
DRESS_DESC_N = Box("dress_desc_narrow", 160, 3, 0xFFFE)
DRESS_NAME_N = Box("dress_name_narrow", 80, 1, 0xFFFE)  # list x=130, frame ~x214 (to verify)


class Metrics:
    def __init__(self, font, gap=1, space=4):
        self.left, self.adv = vwf_patch.metrics(font, gap, space)
        self.gap, self.space = gap, space

    HL = {"\x01": 0xFE02, "\x02": 0xFE00}   # highlight on/off markers (zero width)

    def codes(self, s, box):
        out, seg = [], ""
        for ch in s:
            if ch in self.HL:
                if seg: out += font_patch.enc_en(seg, box.space_code); seg = ""
                out.append(self.HL[ch])
            else:
                seg += ch
        if seg: out += font_patch.enc_en(seg, box.space_code)
        return out

    def adv_of(self, u):
        if u in (0xFE02, 0xFE00): return 0
        if u == 0xFFFE: return self.space
        return self.adv[u] if u < len(self.adv) else 14

    def width(self, s, box):
        """Ink width in px: all advances except the trailing gap of the last glyph."""
        u = self.codes(s, box)
        if not u: return 0
        w = sum(self.adv_of(x) for x in u)
        last = u[-1]
        trailing = self.gap if (last < len(self.adv) and self.adv[last] != 14) else 0
        return w - trailing


def wrap(text, box, m: Metrics):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = word if not cur else cur + " " + word
            if m.width(cand, box) <= box.max_px:
                cur = cand
                continue
            if cur:
                lines.append(cur); cur = ""
            # word alone too wide: split at character level (flagged by caller via return)
            while m.width(word, box) > box.max_px:
                i = len(word)
                while i > 1 and m.width(word[:i], box) > box.max_px: i -= 1
                lines.append(word[:i]); word = word[i:]
            cur = word
        lines.append(cur)
    for ln in lines:
        assert m.width(ln, box) <= box.max_px, ln
    if len(lines) > box.max_lines:
        raise FitError(f"[{box.name}] needs {len(lines)} lines (max {box.max_lines}): {text!r} -> {lines}")
    return lines


def fit(text, box, m):
    """Return the encoded glyph codes (with 0xFFFF line breaks) for text in box."""
    out = []
    for i, ln in enumerate(wrap(text, box, m)):
        if i: out.append(0xFFFF)
        out += m.codes(ln, box)
    return out

