# Translating Londonian Gothics to other languages

This guide explains how to make your own translation patch from the files in this repository.

**Steps**

1. [Download or clone the repository](#1-download-or-clone-the-repository)
2. [Install the requirements and add the ROM](#2-install-the-requirements-and-add-the-rom)
3. [(Optional) Add your own letters: `GLYPHS - EDIT and IMPORT.txt`](#3-optional-add-your-own-letters-glyphs---edit-and-importtxt)
4. [Translate the script: `SCRIPT - EDIT and IMPORT.txt`](#4-translate-the-script-script---edit-and-importtxt)
5. [Build and test your patched ROM](#5-build-and-test-your-patched-rom)

**Reference**

- [The files in `tools-resources`](#the-files-in-tools-resources)
- [Text drawn with a different font](#text-drawn-with-a-different-font)
- [Editing `_script_en.json` / `_glyph_table.tsv` directly (advanced)](#editing-_script_enjson--_glyph_tabletsv-directly-advanced)
- [What each tool does](#what-each-tool-does)

> All commands in this guide are run from the `.WORK` folder.
> All files you edit are in `.WORK\tools-resources\`.

---

## 1. Download or clone the repository

Either:

- **Download it:** [latest source code (ZIP)](https://github.com/LBpartition/Londonian.Gothics-ENG/archive/refs/heads/main.zip), then unzip it, or
- **Clone it with Git:**

  ```
  git clone https://github.com/LBpartition/Londonian.Gothics-ENG.git
  ```

---

## 2. Install the requirements and add the ROM

You need **Windows** and **[Python 3](https://www.python.org/downloads/)**. Then, from the repository folder (the one containing `requirements.txt`), install the Python packages:

```
pip install -r requirements.txt
```

Put the untranslated Japanese ROM (game code **ALGJ**) here, with this exact name:

```
.WORK\tools-resources\.ROM_JPN.nds
```

Then, from the `.WORK` folder, run this **once**:

```
python tools\extract_rom.py
```

This unpacks the ROM into `.WORK\extracted\`, which the build needs. It also writes a list of the ROM's files and a short report to `.WORK\out\Extracted-ROM-Report\` (for information only).

---

## 3. (Optional) Add your own letters: `GLYPHS - EDIT and IMPORT.txt`

Skip this step if your language only needs the letters that are already there:

```
A-Z  0-9  space  . , ' - ! ? & * : ; ( ) / " # % _ < > … £
```

Lower-case letters are not needed: everything is shown in capitals.

### How the font works

The game draws text with a font of small pictures called **glyphs**. Each glyph is 16 × 16 pixels and has a number (its **id**, in hexadecimal):

- **`0x000`-`0x246`** are the game's **ORIGINAL** Japanese glyphs. You can't redraw these, but you can reuse them (see below).
- **From `0x247`** are the **CUSTOM** glyphs added for the English patch: the space, punctuation, digits and the narrow A-Z capitals. You can redraw these and add more.

Every glyph is in **`GLYPHS - EDIT and IMPORT.txt`**, drawn as a picture made of characters. Edit it, then import it (step 5 below).

### The preview: `GLYPHS - PREVIEW.png`

To find a glyph quickly, open **`GLYPHS - PREVIEW.png`**. It is a sheet of every glyph:

- the **id** under each glyph (ORIGINAL in grey, CUSTOM in red boxes),
- the character you type to get it, in **blue** (or, if it can't be typed, what it shows, in black).

It is redrawn every time you import, so after importing you can open it to check your new letters.

### What a glyph looks like

Each glyph is one block. Here is the CUSTOM digit `9`:

```
==== 0x26F ==== (CUSTOM)
char: 9
en: 9
note: CUSTOM: digit 9

-----------------------------------------



 111
1   1
1   1
1   1
1   1
1   1
 1111
    1
    1
1   1
 111



-----------------------------------------
```

| Line | Meaning |
|---|---|
| `==== 0x26F ====` | The glyph id. `(CUSTOM)` / `(ORIGINAL)` is just a label. |
| `char:` | What the glyph shows (for your reference). |
| `en:` | The character you type in the script to get this glyph. Leave empty if it should not be typed. `<space>` = the space character. Each character may only be used once in the whole file. |
| `note:` | A comment; ignored by the build. |
| Between the `-----` lines | The picture: 16 rows, up to 16 characters wide. A space = empty (`.` also works). `1` = full ink, `2` and `3` = lighter shades used to smooth edges. (Some original glyphs also use `4`-`9` and `A`-`E`.) |

The picture is the whole 16 × 16 cell:

- **Up/down position matters.** The capitals and digits start on the 4th row (3 empty rows above) and are 11 rows tall, so keep new letters on the same rows. Accents can go in the empty rows above.
- **Left/right position doesn't matter.** The build measures the inked columns of each glyph and spaces letters automatically. Just start at the left edge, like the existing letters.

### Adding a new letter (e.g. `É`)

1. **Copy a similar CUSTOM block** and paste it at the very **end** of the file. For `É`, copy the block for `E` (`0x24F`).
2. **Change the id** to the next number after the last glyph. The last glyph is `0x272`, so your first new glyph is `0x273`, then `0x274`, and so on. CUSTOM ids must count up **without gaps**.
3. **Set `char:` and `en:`** to your character (`É`), and change the `note:`.
4. **Draw it.** For `É`, the `E` already starts on row 4, so just add the accent in the two rows above it:

   ```
   ==== 0x273 ==== (CUSTOM)
   char: É
   en: É
   note: CUSTOM: E acute

   -----------------------------------------

      11
     11
   11111
   1
   1
   1
   1
   1111
   1
   1
   1
   1
   11111



   -----------------------------------------
   ```

5. **Import it:**

   ```
   python tools\glyph_import.py
   ```

   It lists the glyphs you changed and redraws `GLYPHS - PREVIEW.png`. If something is wrong (a gap in the ids, a character used twice, an unknown picture character, an ORIGINAL glyph redrawn) it stops with an error and changes nothing.
6. **Use it** in your script: type `É` (or `é`) anywhere in `SCRIPT - EDIT and IMPORT.txt`.

To **redraw an existing CUSTOM letter** (e.g. to change the style of `A`), just edit its picture and import.

**You don't need to change any of the Python scripts.** The build automatically draws your glyphs into the game's font, works out each glyph's width from its pixels, uses that width when checking whether lines fit, and uses your glyph wherever its character appears (dialogue, locations, dresses, items and menus).

### Reusing an original glyph instead of drawing one

If one of the game's original glyphs (`0x000`-`0x246`) already looks like the character you need, type your character on that glyph's `en:` line instead of drawing a new one, then import. For example, the original `0x0EE` (`…`) is used this way.

### Limits

- The game has room for glyph ids up to `0x2FF`, so you can add about 140 more glyphs.
- The game draws all text in capitals: `é` and `É` both become your `É` glyph.
- The **OPTION** labels (max 11 characters) and **YES / NO / END** (max 4 characters) use the game's original wide A-Z letters. Other characters there use your CUSTOM glyphs.
- The intro story, SAVE/LOAD prompts and title screen credits don't use these glyphs (see [Text drawn with a different font](#text-drawn-with-a-different-font)).

---

## 4. Translate the script: `SCRIPT - EDIT and IMPORT.txt`

**`SCRIPT - EDIT and IMPORT.txt`** contains **all** text in the game, in playthrough order: title screen credits, intro, dialogue, locations, dresses, items and menus. Replace the English with your translation, then import it:

```
python tools\script_import.py
```

It reports how many entries changed. For reference, the original Japanese is in `_script_jp.json` (same order), and the GameFAQs guide the English is based on is in `.ShadowRisae_Guide.txt`.

### The golden rule

**Change the text only. Do not add, remove or reorder entries, and leave the section headings alone.**
Each entry is matched to its place in the game by its position.

### Formatting

| You write | In-game result |
|---|---|
| `{word}` | *word* shown in red (highlighted) |
| Each separate line | A separate line on screen. Text is not re-wrapped for you. |
| lower or UPPER case | Always shown in CAPITALS (the game's font is capitals only) |

### Dialogue boxes

A dialogue box shows **3 lines**. A `---` line starts a new box. You *can* add or remove `---` lines inside a dialogue entry to split its text over more or fewer boxes. A box with fewer than 3 lines is padded with blank lines automatically. This only changes how that entry's text is split into boxes, not the entries themselves.

### Making text fit

Each line must fit the width of its box. Letters are drawn at their own width (an `I` is narrower than an `M`), so the limit is in pixels, not characters.

- **Check before testing:** every build writes `out\Patched_ROM_fit_report.tsv`, listing every line with **ok** / **FAIL**. Fix every **FAIL** line.
- **Dialogue too long?** Move words to the next line. If the box is full (3 lines), add a `---` line to continue in a new box. There's no limit on the number of boxes in an entry.
- **Names, dresses, items, locations and menus** can't get extra boxes, so use shorter wording or abbreviations.
- Lines are never wrapped automatically: what you see in the file is what appears on screen.

### Title screen credits

The first section, `TITLE SCREEN CREDITS`, is the text shown on the title screen's bottom screen. It is only added to the ROM when you pass a build number to the build (see [step 5](#5-build-and-test-your-patched-rom)).

- Up to **4 lines**, each must fit the screen width (the build stops if a line is too wide).
- These placeholders are filled in by the build:

| Placeholder | Replaced with |
|---|---|
| `<RC>` | The build number you pass to `full_build.py` (e.g. `1`) |
| `<HUMAN>` | % of entries whose `"source"` is not `mtl` |
| `<MTL>` | % of entries whose `"source"` is `mtl` |

Every entry in `_script_en.json` has a `"source"`: where its English came from (`shadowrisae` = the GameFAQs guide, `mtl` = machine translation). It doesn't change the game text, but it **is used for the `<HUMAN>` / `<MTL>` percentages**. The percentages count dialogue lines, intro paragraphs, dress and item names and descriptions, location names, character names and menu entries. If they don't make sense for your translation, either change the `"source"` values in `_script_en.json` to match your own work, or just remove `<HUMAN>` / `<MTL>` from your credit lines.

---

## 5. Build and test your patched ROM

First make sure you've imported your edits (`glyph_import.py` if you changed the glyphs, `script_import.py` for the script). Then build:

```
python tools\full_build.py out Patched_ROM
```

To include the title screen credits, add a build number as a third argument (it replaces `<RC>`):

```
python tools\full_build.py out Patched_ROM 1
```

This creates:

- `out\Patched_ROM.nds` - your patched ROM. Test it in an emulator (e.g. melonDS or DeSmuME) or on hardware.
- `out\Patched_ROM_fit_report.tsv` - a check of every line. Any line marked **FAIL** is too wide for its box: shorten it or move a word to the next line, import and build again.

If a character in your script isn't in the font, the build stops and names it: add it in [step 3](#3-optional-add-your-own-letters-glyphs---edit-and-importtxt).

**Typical loop:** edit `SCRIPT - EDIT and IMPORT.txt` → `python tools\script_import.py` → `python tools\full_build.py out Patched_ROM 1` → test → repeat.

---

## The files in `tools-resources`

| File | What it is | Edit it? |
|---|---|---|
| `SCRIPT - EDIT and IMPORT.txt` | All text in the game, laid out as an easy-to-read script. | **Yes** ([step 4](#4-translate-the-script-script---edit-and-importtxt)) |
| `GLYPHS - EDIT and IMPORT.txt` | Every glyph of the font, drawn as an easy-to-edit 16 × 16 picture. | **Yes**, to add or redraw letters ([step 3](#3-optional-add-your-own-letters-glyphs---edit-and-importtxt)) |
| `GLYPHS - PREVIEW.png` | A picture of every glyph with its id and character. Redrawn by `glyph_import.py` / `glyph_dump.py`. | No, reference only |
| `_script_en.json` | The text the build actually reads. Written by `script_import.py`. | No (advanced: see below) |
| `_glyph_table.tsv` | The font table the build actually reads. Written by `glyph_import.py`. | No (advanced: see below) |
| `_script_jp.json` | The original Japanese text, in the same order as `_script_en.json`. | No, reference only |
| `.ShadowRisae_Guide.txt` | The English GameFAQs guide the English translation is based on. | No, reference only |
| `.ROM_JPN.nds` | The Japanese ROM you add in step 2 (not included in the repository). | No |

---

## Text drawn with a different font

**The intro story, the SAVE/LOAD prompts and the title screen credits** are drawn as pictures with the Windows *Georgia* font, not the game font (`tools\intro_patch.py`, `tools\save_load_patch.py`, `tools\add_patch_credits.py`). You still translate them in `SCRIPT - EDIT and IMPORT.txt` like everything else, but the glyphs from step 3 don't apply to them: any letter Georgia has works without adding glyphs. Georgia covers Latin, Greek and Cyrillic letters. Other scripts need a different font set in those files.

---

## Editing `_script_en.json` / `_glyph_table.tsv` directly (advanced)

You can edit the files the build reads instead of the `EDIT and IMPORT` files, but **don't edit both at once**: importing overwrites `_script_en.json` / `_glyph_table.tsv`, and the dump scripts overwrite the `EDIT and IMPORT` files.

- **`_script_en.json`** has the sections **credits**, **intro**, **dialogue**, **locations**, **dresses**, **items** and **menu**. Highlights are written `{H}word{/H}`, and in dialogue every 3 lines is one box (add blank `""` lines to pad a box). Afterwards, run `python tools\script_dump.py` to update `SCRIPT - EDIT and IMPORT.txt`.
- **`_glyph_table.tsv`** is tab-separated, one row per glyph: `id`, `char`, `en`, `note`, and for CUSTOM glyphs only, `top` (the first picture row, 0 = very top) and `pixels` (the picture, cropped to the inked rows, rows separated by `/`, `.` = empty). Afterwards, run `python tools\glyph_dump.py` to update `GLYPHS - EDIT and IMPORT.txt` and `GLYPHS - PREVIEW.png`.

---

## What each tool does

You only run the **scripts** at the top. The rest are used by them automatically and must stay in the `tools` folder.

**Scripts you run:**

| File | Purpose |
|---|---|
| `extract_rom.py` | One-time setup: extracts the ROM into `.WORK\extracted\` |
| `glyph_import.py` | `GLYPHS - EDIT and IMPORT.txt` -> `_glyph_table.tsv` (and redraws `GLYPHS - PREVIEW.png`) |
| `script_import.py` | `SCRIPT - EDIT and IMPORT.txt` -> `_script_en.json` |
| `full_build.py` | Builds the patched ROM and `Patched_ROM_fit_report.tsv` |
| `glyph_dump.py` | `_glyph_table.tsv` -> `GLYPHS - EDIT and IMPORT.txt` and `GLYPHS - PREVIEW.png` (advanced) |
| `script_dump.py` | `_script_en.json` -> `SCRIPT - EDIT and IMPORT.txt` (advanced) |

**Used by the build:**

| File | Purpose |
|---|---|
| `master.py` | Loads `_script_en.json` / `_script_jp.json` |
| `font_patch.py` | Draws the CUSTOM glyphs from `_glyph_table.tsv` into the font; maps your characters to glyphs |
| `font_tools.py` | Font helpers; reads the original glyph list from `_glyph_table.tsv`; location of the Japanese ROM |
| `vwf_patch.py` | Variable-width text (each letter drawn at its own width) |
| `textfit.py` | Line width / fit checking |
| `sp_tool.py` | Reads and writes the game's dialogue script files (`.sp`) |
| `ui_patch.py` | Dress, item and menu text |
| `intro_patch.py` | Draws the intro story text (a picture) |
| `save_load_patch.py` | Draws the SAVE/LOAD prompts (also a picture) |
| `add_patch_credits.py` | Draws the title screen credits; works out the `<HUMAN>` / `<MTL>` percentages |
| `ndsbuild.py` | Rebuilds the ROM |
| `repack_contig.py` | ROM file layout that also runs on 3DS (nds-bootstrap) |
