# Translating Londonian Gothics to other languages

You need Windows, Python 3, and these Python packages:

```
pip install pillow keystone-engine ndspy
```

All commands below are run from the `.WORK` folder.
The files to edit are in `.WORK\tools-resources\`.

## 1. Add your ROM

Put the untranslated Japanese ROM (game code ALGJ) here, with this exact name:

```
.WORK\rom\JPN-original.nds
```

Then run once:

```
python tools\extract_rom.py
```

This extracts the ROM into `.WORK\extracted\` (needed by the build).

## 2. Files to edit (all in `.WORK\tools-resources\`)

### `SCRIPT - FULL.txt`
The same text as `script_en.json` as a plain readable script.
You can edit this instead of script_en.json (see step 3).

### `script_en.json`
ALL text in the game. Replace the English with your language.
**Change text only; do not add, remove or reorder entries.**

In `SCRIPT - FULL.txt` you *can* add or remove `---` lines inside a dialogue entry to add or remove text boxes: `---` starts a new box (a box with fewer than 3 lines is padded with blank lines). This only changes how that entry's text is split into boxes, not the entries themselves. Run `full_build.py` afterwards to check the fit.

Sections: intro, dialogue (in playthrough order), locations, dresses, items, menu.

- Text is stored as a list of the exact lines shown in-game.
- `{H}word{/H}` = word shown in red.
- Dialogue boxes show 3 lines; a blank line `""` pads a box so the next line starts in a new box.
- `"source"` only records where the English came from; you can ignore it.

### `glyph_table.tsv`
The font. Each character your text uses must be listed in the `en` column.
The game shows all text in capitals (your text is converted to upper case), so only capital letters are needed.
Accented capitals (e.g. É, Ü) are not in the font yet - add them as new CUSTOM rows at the end:

| Column | Value |
|---|---|
| `id` | next number after the last row (0x273, 0x274, ...) |
| `char` / `en` | the character |
| `top` | first pixel row of the glyph (3 = capital-letter top) |
| `pixels` | rows separated by `/`, `.` = empty, `1`-`3` = shade |

Copy an existing CUSTOM row (e.g. letter A) as a template.

### `script_jp.json`
Reference only. The original Japanese script, in the same order as the english script.

### `ShadowRisae-Guide.txt`
Reference only. The English GameFAQs guide the translation is based on.

## 3. Scripts to run

If you edited `SCRIPT - FULL.txt`, run script_import.py to import your edits to `script_en.json`:

```
python tools\script_import.py
```

After importing your edits, or if you edited the json directly; Build the patched ROM and check that all text fits:

```
python tools\full_build.py out MyTranslation
```

- `out\MyTranslation.nds` - the patched ROM
- `out\fit_report.tsv` - any line marked FAIL is too long for its box: shorten it or change its line breaks, then build again.

Regenerate `SCRIPT - FULL.txt` from `script_en.json` (to see your exact in-game line breaks, or after editing the JSON):

```
python tools\script_dump.py
```

## 4. Not in `script_en.json`

- **Title screen credit lines:** `tools\add_patch_credits.py` (`default_lines`). Pass a third argument to `full_build.py` (e.g. `python tools\full_build.py out MyTranslation 1`) to show them.
- **The intro and SAVE/LOAD prompts** are drawn as images with the Windows Georgia font (`tools\intro_patch.py`, `tools\save_load_patch.py`); they use the text from `script_en.json` but may need a different font for non-Latin scripts.

## 5. What each file in `.WORK\tools` does

You only run the 4 scripts named above. The rest are loaded by them automatically and must stay in the folder.

**Run by you:**

| File | Purpose |
|---|---|
| `extract_rom.py` | one-time setup: extracts the ROM into `.WORK\extracted\` |
| `full_build.py` | builds the patched ROM + `fit_report.tsv` |
| `script_import.py` | `SCRIPT - FULL.txt` -> `script_en.json` |
| `script_dump.py` | `script_en.json` -> `SCRIPT - FULL.txt` |

**Used by the build:**

| File | Purpose |
|---|---|
| `master.py` | loads `script_en.json` / `script_jp.json` |
| `font_patch.py` | adds the CUSTOM glyphs from `glyph_table.tsv` to the font |
| `glyph_table.py` | the original Japanese glyph list (`glyph_table.tsv`) |
| `font_tools.py` | font pixel helpers; location of the Japanese ROM |
| `vwf_patch.py` | variable-width text (letters drawn at their own width) |
| `textfit.py` | line wrapping / fit checking |
| `sp_tool.py` | reads/writes the game's dialogue script files (.sp) |
| `ui_patch.py` | dress, item and menu text |
| `intro_patch.py` | draws the intro story text (it is an image) |
| `save_load_patch.py` | draws the SAVE/LOAD prompts (also an image) |
| `add_patch_credits.py` | title screen credit lines |
| `ndsbuild.py` | rebuilds the ROM |
| `repack_contig.py` | ROM file layout that runs on 3DS (nds-bootstrap) |
