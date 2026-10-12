r"""Full dialogue build: TEST06 base (UI VWF + DRESS MODE) + dialogue VWF +
every reviewed guide line from phase7\final\*.json inserted into the .sp scripts.

  python tools\full_build.py <out_dir> [name]

Strings without reviewed English stay Japanese. Writes <out_dir>\fit_report.tsv.
"""
import sys, io, json, glob, os, re, hashlib, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, sp_tool, textfit
import test06_build as t6

W = Path(__file__).resolve().parent.parent
BOX = textfit.Box("dialogue", 166, 99, 0xFFFE)  # x44 w170; 3 lines/page, game auto-pages
KEEP_JP_CODES = (0xFD00, 0xFC00)  # inserted name / number: English guide text is static


from highlight import highlight, JPM
import layout


def norm(s):
    s = s.replace("{H}", "\x01").replace("{/H}", "\x02")   # highlight markup -> FE02/FE00
    s = re.sub(r'[ \t\r]*\n[ \t\r]*', '\n', s)   # keep forced line breaks
    return re.sub(r'[^\S\n]+', ' ', s).strip()


GUIDE = (W / "ref_guide.txt").read_text(encoding="utf-8", errors="replace")
GUIDE_WS = " ".join(GUIDE.split())
# Bottom-screen location plate (header name). JP longest = 7 glyphs x 12px; plate ~130px wide.
LOC_BOX = textfit.Box("location", 140, 1, 0xFFFE)


def main(out_dir, name="FULL-Dialogue", rc=None):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_t06"
    t6.DIALOGUE_VWF = True
    t6.ITEMS = True
    if rc:
        import title_text
        t6.TITLE = True
        title_text.LINES = title_text.default_lines(rc)
        print("title text", title_text.LINES)
    with contextlib.redirect_stdout(io.StringIO()) as so:
        t6.main(tmp)
    print(so.getvalue().split("fit-gate rejected", 1)[-1].strip())
    rom = (tmp / "TEST06-NarrowFont-DressMode.nds").read_bytes()
    for f in tmp.iterdir(): f.unlink()
    tmp.rmdir()
    ids = ndsbuild.file_ids_by_path(rom)
    m = textfit.Metrics(ndsbuild.get_file(rom, ids["data/font.NCGR"]), t6.GAP, t6.SPACE)
    APPROVED = {tuple(l.split("\t")[:2]): l.rstrip("\n").split("\t", 2)[2]
                for l in open(W / "phase10" / "approved.tsv", encoding="utf-8")}   # user-approved MTL
    rep = ["file\tidx\tstatus\tlines\ten"]
    changes, n_en, n_jp, n_fail = {}, 0, 0, 0
    for p in sorted(glob.glob(str(W / "phase7" / "final" / "*.json"))):
        fname = os.path.basename(p)[:-5]
        sid = ids["data/" + fname]
        d = ndsbuild.get_file(rom, sid)
        info = sp_tool.parse(d)
        new = [s for _, s in info["strings"]]
        for e in json.load(open(p, encoding="utf-8")):
            i, en = e["idx"], e.get("en")
            note = e.get("note") or ""
            if en is None and note.lower().startswith("sfx:"):
                t = note.split(":", 1)[1].strip()
                if "/" + t + "/" in GUIDE:   # verbatim guide /action/ line only
                    en = t
            elif en is None and note.startswith("diary text (guide"):
                t = note.split("):", 1)[1].strip()
                if " ".join(t.split()) in GUIDE_WS:   # verbatim guide text only
                    en = t
            elif en is None and note.startswith("diary date heading (guide '"):
                t = note.split("'")[1]
                if t in GUIDE:
                    en = t
            mtl = en is None and (fname, str(i)) in APPROVED
            if mtl:
                en = APPROVED[(fname, str(i))]
            _t = os.environ.get("LG_TEST_LINE", "").split("|", 2)   # diagnostic override: file|idx|text
            if len(_t) == 3 and _t[0] == fname and _t[1] == str(i):
                en = _t[2]
            if f"{fname}|{i}" in layout.OV["dialogue"]:
                en = layout.OV["dialogue"][f"{fname}|{i}"]
            elif en is not None and "\n" not in en:
                en = layout.auto_break(norm(en), BOX, m)
            if en is not None and "{H}" not in en:
                en = highlight(en, JPM.get((fname, i), ""))
            if en is None:
                n_jp += 1; rep.append(f"{fname}\t{i}\tjp:{e.get('note','')}\t\t"); continue
            if any(c in KEEP_JP_CODES for c in new[i]):
                n_jp += 1; rep.append(f"{fname}\t{i}\tjp:has-insert-code\t\t{en}"); continue
            try:
                lines = textfit.wrap(norm(en), BOX, m)
                new[i] = textfit.fit(norm(en), BOX, m)
                n_en += 1
                rep.append(f"{fname}\t{i}\t{'mtl' if mtl else 'ok' if len(lines) <= 3 else 'ok-multipage'}\t{len(lines)}\t{' / '.join(lines)}")
            except (textfit.FitError, KeyError) as ex:
                n_fail += 1; rep.append(f"{fname}\t{i}\tFAIL:{ex}\t\t{en}")
        changes[sid] = sp_tool.rebuild(d, info, new)
    import intro_patch
    import font_patch as FP, glyph_table
    gt = glyph_table.build()
    locs = json.load(open(W / "phase7" / "locations.json", encoding="utf-8"))
    n_loc = 0
    for path, sid in ids.items():
        if not path.endswith(".sp"):
            continue
        fname = path[5:]
        d = changes.get(sid) or ndsbuild.get_file(rom, sid)
        jp = "".join(gt.get(v, "?") for v in sp_tool.get_name(d))
        en = locs.get(fname)
        if en is None and jp.startswith("\u5730\u4e0b") and jp.endswith("\u968e"):
            en = "Labyrinth B" + jp[2:-1] + "F"
        if en is None:
            rep.append(f"{fname}\tname\tjp:location-not-in-guide\t\t{jp}"); continue
        en = en.replace("|", " ")
        if m.width(en, LOC_BOX) > LOC_BOX.max_px:
            n_fail += 1; rep.append(f"{fname}\tname\tFAIL:width {m.width(en, LOC_BOX)}px\t\t{en}"); continue
        codes = m.codes(en, LOC_BOX)
        changes[sid] = sp_tool.set_name(d, codes)
        n_loc += 1
        rep.append(f"{fname}\tname\tok\t\t{en}")
    print("location names", n_loc)
    iid = ids[intro_patch.FILE]
    changes[iid], _ = intro_patch.patch(ndsbuild.get_file(rom, iid),
                                        ndsbuild.get_file(rom, ids["data/title_roll_full_16.NCLR"]))
    import save_load_patch
    sl = ids[save_load_patch.FILE]
    changes[sl] = save_load_patch.patch(ndsbuild.get_file(rom, sl))
    out = ndsbuild.build(rom, changes, log=lambda *_: None)
    import repack_contig; out = repack_contig.repack((Path(__file__).resolve().parents[2] / '.REFS/JPN-original.nds').read_bytes(), out)   # keep arm7 right after arm9: arm7-at-ROM-end crashes nds-bootstrap (3DS)
    rp = out_dir / f"{name}.nds"
    rp.write_bytes(out)
    (out_dir / "fit_report.tsv").write_text("\n".join(rep) + "\n", encoding="utf-8")
    h = hashlib.sha256(out).hexdigest().upper()
    print(rp, h)
    print(f"english {n_en}, kept japanese {n_jp}, fit failures {n_fail}, files {len(changes)}")
    return rp, h


if __name__ == "__main__":
    main(*sys.argv[1:])
