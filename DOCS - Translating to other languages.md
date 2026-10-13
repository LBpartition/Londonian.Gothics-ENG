# Translating Londonian Gothics to other languages

This guide explains how to make your own translation patch from the files in this repository.

**Contents**

1. [Setup](#1-setup)
2. [The text files](#2-the-text-files)
3. [Editing the text](#3-editing-the-text)
4. [Building and checking your patch](#4-building-and-checking-your-patch)
5. [The font: adding your own letters (`glyph_table.tsv`)](#5-the-font-adding-your-own-letters-glyph_tabletsv)
6. [Text drawn with a different font](#6-text-drawn-with-a-different-font)
7. [What each tool does](#7-what-each-tool-does)

---

## 1. Setup

You need **Windows** and **Python 3**, plus these Python packages:

```
pip install pillow keystone-engine ndspy
```

Put the untranslated Japanese ROM (game code **ALGJ**) here, with this exact name:

```
.WORK\tools-resources\JPN_ROM.nds
```

Then, from the `.WORK` folder, run this **once**:

```
python tools\extract_rom.py
```

This unpacks the ROM into `.WORK\extracted\`, which the build needs. It also writes a list of the ROM's files and a short report to `.WORK\out\Extracted-ROM-Report\` (for information only).

> All commands in this guide are run from the `.WORK` folder.
> All files you edit are in `.WORK\tools-resources\`.

---

## 2. The text files

| File | What it is | Edit it? |
|---|---|---|
| `script_en.json` | **All** text in the game, in playthrough order. This is what the build reads. | Yes (or edit `SCRIPT - FULL.txt` instead) |
| `SCRIPT - FULL.txt` | The same text as `script_en.json`, laid out as an easy-to-read script. | Yes |
| `glyph_table.tsv` | The font: which letters exist and what they look like. See [section 5](#5-the-font-adding-your-own-letters-glyph_tabletsv). | Only to add letters |
| `script_jp.json` | The original Japanese text, in the same order as `script_en.json`. | No, reference only |
| `ShadowRisae-Guide.txt` | The English GameFAQs guide the English translation is based on. | No, reference only |

`script_en.json` has these sections: **credits** (title screen), **intro**, **dialogue**, **locations**, **dresses**, **items** and **menu**.

---

## 3. Editing the text

Edit **either** `SCRIPT - FULL.txt` **or** `script_en.json`. Don't edit both at once: one overwrites the other (see [section 4](#4-building-and-checking-your-patch)).

### The golden rule

**Change the text only. Do not add, remove or reorder entries.**
Each entry is matched to its place in the game by its position.

### Formatting

| You write | In-game result |
|---|---|
| `{H}word{/H}` in `script_en.json`, `{word}` in `SCRIPT - FULL.txt` | *word* shown in red (highlighted) |
| Each separate line | A separate line on screen. Text is not re-wrapped for you. |
| lower or UPPER case | Always shown in CAPITALS (the game's font is capitals only) |

### Dialogue boxes

A dialogue box shows **3 lines**.

- **In `SCRIPT - FULL.txt`:** a `---` line starts a new box. You *can* add or remove `---` lines inside a dialogue entry to split its text over more or fewer boxes. A box with fewer than 3 lines is padded with blank lines automatically. This only changes how that entry's text is split into boxes, not the entries themselves.
- **In `script_en.json`:** every 3 lines is one box. Add blank lines `""` to pad a box so the next line starts in a new box.

### Title screen credits

The first section (`TITLE SCREEN CREDITS` in `SCRIPT - FULL.txt`, `credits` in `script_en.json`) is the text shown on the title screen's bottom screen. It is only added to the ROM when you pass a build number to the build (see [section 4](#4-building-and-checking-your-patch)).

- Up to **4 lines**, each must fit the screen width (the build stops if a line is too wide).
- These placeholders are filled in by the build:

| Placeholder | Replaced with |
|---|---|
| `<RC>` | The build number you pass to `full_build.py` (e.g. `1`) |
| `<HUMAN>` | % of entries whose `"source"` is not `mtl` |
| `<MTL>` | % of entries whose `"source"` is `mtl` |

### `"source"`

Every entry in `script_en.json` has a `"source"`: where its English came from (`shadowrisae` = the GameFAQs guide, `mtl` = machine translation). It doesn't change the game text, but it **is used for the `<HUMAN>` / `<MTL>` percentages** in the credits. The percentages count dialogue lines, intro paragraphs, dress and item names and descriptions, location names, character names and menu entries.

If the percentages don't make sense for your translation, either change the `"source"` values in `script_en.json` to match your own work, or just remove `<HUMAN>` / `<MTL>` from your credit lines.

---

## 4. Building and checking your patch

**Step 1 - only if you edited `SCRIPT - FULL.txt`:** copy your edits into `script_en.json`:

```
python tools\script_import.py
```

**Step 2 - build the ROM:**

```
python tools\full_build.py out Patched_ROM
```

To include the title screen credits, add a build number as a third argument (it replaces `<RC>`):

```
python tools\full_build.py out Patched_ROM 1
```

This creates:

- `out\Patched_ROM.nds` - your patched ROM
- `out\Patched_ROM_fit_report.tsv` - a check of every line. Any line marked **FAIL** is too wide for its box: shorten it or move a word to the next line, then build again. If a character is missing from the font, the build stops and names it (see [section 5](#5-the-font-adding-your-own-letters-glyph_tabletsv)).

**Step 3 - only if you edited `script_en.json` directly:** update `SCRIPT - FULL.txt` to match:

```
python tools\script_dump.py
```

> **Warning:** `script_dump.py` overwrites `SCRIPT - FULL.txt`, and `script_import.py` overwrites `script_en.json`. Run the one that matches the file you edited.

---

## 5. The font: adding your own letters (`glyph_table.tsv`)

### How the font works

The game draws text with a font of small pictures called **glyphs**. Each glyph is 16 × 16 pixels and has a number (its **id**). `glyph_table.tsv` lists every glyph:

- **Rows `0x000`-`0x246`** are the game's original Japanese glyphs. Don't change these, except the `en` column (see below).
- **Rows from `0x247`** are **CUSTOM** glyphs added for the English patch: the space, punctuation and the narrow A-Z capitals. The build draws them from this file into the game's font.

Open the file in a spreadsheet program or a text editor (it is tab-separated). The columns are:

| Column | Meaning |
|---|---|
| `id` | The glyph number, in hexadecimal. |
| `char` | What the glyph shows (for your reference). |
| `en` | The character you type in the script to get this glyph. Leave empty if it should not be typed. `<space>` = the space character. |
| `top` | CUSTOM only: the pixel row where the drawing starts (0 = very top). Capitals start at row `3`. |
| `pixels` | CUSTOM only: the drawing. Rows of pixels from the top down, separated by `/`. In each row, `.` = empty and `1`, `2`, `3` = ink (`1` = full ink, `2`/`3` = lighter shades used for smoothing). |
| `note` | A comment; ignored by the build. |

### Letters that are already available

```
A-Z  0-9  space  . , ' - ! ? & * : ; ( ) / " # % _ < > … £
```

Lower-case letters are not needed: everything is converted to capitals.

### Adding a new letter (e.g. `É`)

1. **Copy a similar CUSTOM row** and paste it as a new row at the very **end** of the file. For `É`, copy the row for `E` (`0x24F`).
2. **Set the `id`** to the next number after the last row. The last row is `0x272`, so your first new glyph is `0x273`, then `0x274`, and so on. The ids of CUSTOM rows must count up **without gaps**.
3. **Set `char` and `en`** to your character (`É`).
4. **Draw it** in the `pixels` column. Each row can be up to 16 characters wide, and `top` + the number of rows must not go past 16. Example for `É`, with two rows for the accent above the `E` and `top` moved up from `3` to `1`:

   ```
   id      char  en  top  pixels
   0x273   É     É   1    ..11.../...11.../11111/1..../1..../1..../1..../1111./1..../1..../1..../1..../11111
   ```

5. **Use it** in your script: type `É` (or `é`) anywhere in `script_en.json` or `SCRIPT - FULL.txt`.
6. **Build** (section 4) and check the letter in-game.

That's all. **You don't need to change any of the Python scripts.** The build automatically:

- draws your new glyphs into the game's font,
- works out each glyph's width from its pixels (so letters sit next to each other naturally),
- uses that width when checking whether lines fit (`Patched_ROM_fit_report.tsv`),
- uses your glyph wherever its character appears, including dialogue, locations, dresses, items and menus.

### Reusing an original glyph instead of drawing one

If one of the game's original glyphs (`0x000`-`0x246`) already looks like the character you need, type your character into that row's `en` column instead of drawing a new one. For example, the original `0x0EE` (`…`) is used this way. Each `en` character may only appear once in the whole file.

### Limits

- The game has room for glyph ids up to `0x2FF`, so you can add about 140 more glyphs.
- The game draws all text in capitals: `é` and `É` both become your `É` glyph.
- The **OPTION** labels (max 11 characters) and **YES / NO / END** (max 4 characters) use the game's original wide A-Z letters. Other characters there use your CUSTOM glyphs.

---

## 6. Text drawn with a different font

- **The intro story, the SAVE/LOAD prompts and the title screen credits** are drawn as pictures with the Windows *Georgia* font, not the game font (`tools\intro_patch.py`, `tools\save_load_patch.py`, `tools\add_patch_credits.py`). They still take their text from `script_en.json`, and `glyph_table.tsv` does not apply to them. Georgia covers Latin, Greek and Cyrillic letters. Other scripts need a different font set in those files.

---

## 7. What each tool does

You only run the **4 scripts** at the top. The rest are used by them automatically and must stay in the `tools` folder.

**Scripts you run:**

| File | Purpose |
|---|---|
| `extract_rom.py` | One-time setup: extracts the ROM into `.WORK\extracted\` |
| `script_import.py` | `SCRIPT - FULL.txt` -> `script_en.json` |
| `full_build.py` | Builds the patched ROM and `Patched_ROM_fit_report.tsv` |
| `script_dump.py` | `script_en.json` -> `SCRIPT - FULL.txt` |

**Used by the build:**

| File | Purpose |
|---|---|
| `master.py` | Loads `script_en.json` / `script_jp.json` |
| `font_patch.py` | Draws the CUSTOM glyphs from `glyph_table.tsv` into the font; maps your characters to glyphs |
| `font_tools.py` | Font helpers; reads the original glyph list from `glyph_table.tsv`; location of the Japanese ROM |
| `vwf_patch.py` | Variable-width text (each letter drawn at its own width) |
| `textfit.py` | Line width / fit checking |
| `sp_tool.py` | Reads and writes the game's dialogue script files (`.sp`) |
| `ui_patch.py` | Dress, item and menu text |
| `intro_patch.py` | Draws the intro story text (a picture) |
| `save_load_patch.py` | Draws the SAVE/LOAD prompts (also a picture) |
| `add_patch_credits.py` | Draws the title screen credits; works out the `<HUMAN>` / `<MTL>` percentages |
| `ndsbuild.py` | Rebuilds the ROM |
| `repack_contig.py` | ROM file layout that also runs on 3DS (nds-bootstrap) |
