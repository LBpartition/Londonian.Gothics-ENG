r"""Full dialogue build: TEST06 base (UI VWF + DRESS MODE) + dialogue VWF +
all English text from tools-resources\_script_en.json (exact in-game lines) inserted into the ROM.

  python tools\full_build.py <out_dir> [name]

Strings without reviewed English stay Japanese. Writes <out_dir>\<name>.nds and <out_dir>\<name>_fit_report.tsv.
"""
import sys, io, json, glob, os, re, hashlib, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ndsbuild, sp_tool, textfit
import ui_patch as t6

W = Path(__file__).resolve().parent.parent
BOX = textfit.Box("dialogue", 166, 99, 0xFFFE)  # x44 w170; 3 lines/page, game auto-pages
KEEP_JP_CODES = (0xFD00, 0xFC00)  # inserted name / number: English guide text is static


import master


def norm(s):
    s = s.replace("{H}", "\x01").replace("{/H}", "\x02")   # highlight markup -> FE02/FE00
    s = re.sub(r'[ \t\r]*\n[ \t\r]*', '\n', s)   # keep forced line breaks
    return re.sub(r'[^\S\n]+', ' ', s).strip()


# Bottom-screen location plate (header name). JP longest = 7 glyphs x 12px; plate ~130px wide.
LOC_BOX = textfit.Box("location", 140, 1, 0xFFFE)


def main(out_dir, name="Patched_ROM", rc=None):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_t06"
    t6.DIALOGUE_VWF = True
    t6.ITEMS = True
    if rc:
        import add_patch_credits
        t6.TITLE = True
        add_patch_credits.LINES = add_patch_credits.default_lines(rc)
        print("title text", add_patch_credits.LINES)
    with contextlib.redirect_stdout(io.StringIO()) as so:
        t6.main(tmp)
    print(so.getvalue().split("fit-gate rejected", 1)[-1].strip())
    rom = (tmp / "TEST06-NarrowFont-DressMode.nds").read_bytes()
    for f in tmp.iterdir(): f.unlink()
    tmp.rmdir()
    ids = ndsbuild.file_ids_by_path(rom)
    m = textfit.Metrics(ndsbuild.get_file(rom, ids["data/font.NCGR"]), t6.GAP, t6.SPACE)
    rep = ["file\tidx\tstatus\tlines\ten"]
    changes, n_en, n_jp, n_fail = {}, 0, 0, 0
    files = {}
    for e in master.EN["dialogue"]: files.setdefault(e["file"], []).append(e)
    for fname in sorted(files):
        sid = ids["data/" + fname]
        d = ndsbuild.get_file(rom, sid)
        info = sp_tool.parse(d)
        new = [s for _, s in info["strings"]]
        for e in files[fname]:
            i, mtl = e["idx"], e["source"] == "mtl"
            en = norm(master.join(e["en"])) if e["en"] else None
            _t = os.environ.get("LG_TEST_LINE", "").split("|", 2)   # diagnostic override: file|idx|text
            if len(_t) == 3 and _t[0] == fname and _t[1] == str(i):
                en = norm(_t[2])
            if en is None:
                n_jp += 1; rep.append(f"{fname}\t{i}\tjp:untranslated\t\t"); continue
            if any(c in KEEP_JP_CODES for c in new[i]):
                n_jp += 1; rep.append(f"{fname}\t{i}\tjp:has-insert-code\t\t{en}"); continue
            try:
                lines = textfit.wrap(en, BOX, m)
                new[i] = textfit.fit(en, BOX, m)
                n_en += 1
                rep.append(f"{fname}\t{i}\t{'mtl' if mtl else 'ok' if len(lines) <= 3 else 'ok-multipage'}\t{len(lines)}\t{' / '.join(lines)}")
            except (textfit.FitError, KeyError) as ex:
                n_fail += 1; rep.append(f"{fname}\t{i}\tFAIL:{ex}\t\t{en}")
        changes[sid] = sp_tool.rebuild(d, info, new)
    import intro_patch
    import font_patch as FP, font_tools
    gt = font_tools.build_table()
    locs = {e["file"]: e["en"] for e in master.EN["locations"]}
    n_loc = 0
    for path, sid in ids.items():
        if not path.endswith(".sp"):
            continue
        fname = path[5:]
        d = changes.get(sid) or ndsbuild.get_file(rom, sid)
        jp = "".join(gt.get(v, "?") for v in sp_tool.get_name(d))
        en = locs.get(fname)
        if en is None:
            rep.append(f"{fname}\tname\tjp:location-untranslated\t\t{jp}"); continue
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
    import repack_contig; out = repack_contig.repack(t6.t1.ORIG.read_bytes(), out)   # keep arm7 right after arm9: arm7-at-ROM-end crashes nds-bootstrap (3DS)
    rp = out_dir / f"{name}.nds"
    rp.write_bytes(out)
    (out_dir / f"{name}_fit_report.tsv").write_text("\n".join(rep) + "\n", encoding="utf-8")
    h = hashlib.sha256(out).hexdigest().upper()
    print(rp, h)
    print(f"english {n_en}, kept japanese {n_jp}, fit failures {n_fail}, files {len(changes)}")
    return rp, h


if __name__ == "__main__":
    main(*sys.argv[1:])
