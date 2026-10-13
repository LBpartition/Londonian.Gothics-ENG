# Translating Londonian Gothics to other languages

This guide explains how to make your own translation patch from the files in this repository.

**Contents**

1. [Setup](#1-setup)
2. [The text files](#2-the-text-files)
3. [Editing the text](#3-editing-the-text)
4. [Building and checking your patch](#4-building-and-checking-your-patch)
5. [The font: adding your own letters (`GLYPHS - FULL.txt`)](#5-the-font-adding-your-own-letters-glyphs---fulltxt)
6. [Text drawn with a different font](#6-text-drawn-with-a-different-font)
7. [What each tool does](#7-what-each-tool-does)

---

## 1. Setup

First, get a copy of this repository. Either:

- **Download it:** [latest source code (ZIP)](https://github.com/LBpartition/Londonian.Gothics-ENG/archive/refs/heads/main.zip), then unzip it, or
- **Clone it with Git:**

  ```
  git clone https://github.com/LBpartition/Londonian.Gothics-ENG.git
  ```

You also need **Windows** and **Python 3**, plus these Python packages:

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
| `glyph_table.tsv` | The font: which letters exist and what they look like. See [section 5](#5-the-font-adding-your-own-letters-glyphs---fulltxt). This is what the build reads. | Only to add letters (or edit `GLYPHS - FULL.txt` instead) |
| `GLYPHS - FULL.txt` | The same font as `glyph_table.tsv`, with every glyph drawn as an easy-to-edit 16 × 16 picture. | Yes, to add or redraw letters |
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

**Also only if you edited `GLYPHS - FULL.txt`:** copy your glyphs into `glyph_table.tsv`:

```
python tools\glyph_import.py
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
- `out\Patched_ROM_fit_report.tsv` - a check of every line. Any line marked **FAIL** is too wide for its box: shorten it or move a word to the next line, then build again. If a character is missing from the font, the build stops and names it (see [section 5](#5-the-font-adding-your-own-letters-glyphs---fulltxt)).

**Step 3 - only if you edited `script_en.json` directly:** update `SCRIPT - FULL.txt` to match:

```
python tools\script_dump.py
```

(Likewise, if you edited `glyph_table.tsv` directly, run `python tools\glyph_dump.py` to update `GLYPHS - FULL.txt`.)

> **Warning:** `script_dump.py` overwrites `SCRIPT - FULL.txt`, and `script_import.py` overwrites `script_en.json`. The same goes for `glyph_dump.py` (`GLYPHS - FULL.txt`) and `glyph_import.py` (`glyph_table.tsv`). Run the one that matches the file you edited.

---

## 5. The font: adding your own letters (`GLYPHS - FULL.txt`)

### How the font works

The game draws text with a font of small pictures called **glyphs**. Each glyph is 16 ? 16 pixels and has a number (its **id**, in hexadecimal):

- **`0x000`-`0x246`** are the game's **ORIGINAL** Japanese glyphs. You can't redraw these, but you can reuse them (see below).
- **From `0x247`** are the **CUSTOM** glyphs added for the English patch: the space, punctuation, digits and the narrow A-Z capitals. The build draws them into the game's font. You can redraw these and add more.

The font is stored in `glyph_table.tsv` (what the build reads). To make it easy to edit, the same font is also in **`GLYPHS - FULL.txt`**, with every glyph drawn as a picture. Edit `GLYPHS - FULL.txt`, then run `python tools\glyph_import.py` to copy your changes into `glyph_table.tsv`.

> `GLYPHS - FULL.txt` comes with the repository. If you ever need to recreate it from `glyph_table.tsv`, run `python tools\glyph_dump.py` (this overwrites `GLYPHS - FULL.txt`).

### What a glyph looks like in `GLYPHS - FULL.txt`

Each glyph is one block. Here is the CUSTOM digit `9`:

```
==== 0x26F ==== (CUSTOM)
char: 9
en: 9
note: CUSTOM: digit 9
................
................
................
.111............
1...1...........
1...1...........
1...1...........
1...1...........
1...1...........
.1111...........
....1...........
....1...........
1...1...........
.111............
................
................
```

| Line | Meaning |
|---|---|
| `==== 0x26F ====` | The glyph id. `(CUSTOM)` / `(ORIGINAL)` is just a label. |
| `char:` | What the glyph shows (for your reference). |
| `en:` | The character you type in the script to get this glyph. Leave empty if it should not be typed. `<space>` = the space character. Each character may only be used once in the whole file. |
| `note:` | A comment; ignored by the build. |
| 16 rows of 16 | The picture. `.` = empty. `1` = full ink, `2` and `3` = lighter shades used to smooth edges. (Some original glyphs also use `4`-`9` and `A`-`E`.) |

The picture is the whole 16 ? 16 cell:

- **Up/down position matters.** The capitals and digits start on the 4th row (3 empty rows above) and are 11 rows tall, so keep new letters on the same rows. Accents can go in the empty rows above.
- **Left/right position doesn't matter.** The build measures the inked columns of each glyph and spaces letters automatically. Just start at the left edge, like the existing letters.

### Letters that are already available

```
A-Z  0-9  space  . , ' - ! ? & * : ; ( ) / " # % _ < > ? ?
```

Lower-case letters are not needed: everything is converted to capitals.

### Adding a new letter (e.g. `?`)

1. **Copy a similar CUSTOM block** and paste it at the very **end** of `GLYPHS - FULL.txt`. For `?`, copy the block for `E` (`0x24F`).
2. **Change the id** to the next number after the last glyph. The last glyph is `0x272`, so your first new glyph is `0x273`, then `0x274`, and so on. CUSTOM ids must count up **without gaps**.
3. **Set `char:` and `en:`** to your character (`?`), and change the `note:`.
4. **Draw it.** For `?`, the `E` already starts on row 4, so just add the accent in the two rows above it:

   ```
   ==== 0x273 ==== (CUSTOM)
   char: ?
   en: ?
   note: CUSTOM: E acute
   ................
   ...11...........
   ..11............
   11111...........
   1...............
   1...............
   1...............
   1...............
   1111............
   1...............
   1...............
   1...............
   1...............
   11111...........
   ................
   ................
   ```

5. **Import it** into `glyph_table.tsv`:

   ```
   python tools\glyph_import.py
   ```

   It lists the glyphs you changed. If something is wrong (a gap in the ids, a character used twice, an unknown picture character, an ORIGINAL glyph redrawn) it stops with an error and changes nothing.
6. **Use it** in your script: type `?` (or `?`) anywhere in `script_en.json` or `SCRIPT - FULL.txt`.
7. **Build** (section 4) and check the letter in-game.

To **redraw an existing CUSTOM letter** (e.g. to change the style of `A`), just edit its picture and run step 5.

That's all. **You don't need to change any of the Python scripts.** The build automatically:

- draws your new glyphs into the game's font,
- works out each glyph's width from its pixels (so letters sit next to each other naturally),
- uses that width when checking whether lines fit (`Patched_ROM_fit_report.tsv`),
- uses your glyph wherever its character appears, including dialogue, locations, dresses, items and menus.

### Editing `glyph_table.tsv` directly (advanced)

`glyph_table.tsv` is tab-separated, with one row per glyph: `id`, `char`, `en`, `note`, and for CUSTOM glyphs only, `top` (the first picture row, 0 = very top) and `pixels` (the picture, cropped to the inked rows, rows separated by `/`). `glyph_import.py` writes this format for you. If you edit the TSV directly, run `python tools\glyph_dump.py` afterwards to update `GLYPHS - FULL.txt`.

### Reusing an original glyph instead of drawing one

If one of the game's original glyphs (`0x000`-`0x246`) already looks like the character you need, type your character on that glyph's `en:` line in `GLYPHS - FULL.txt` instead of drawing a new one (then run `glyph_import.py`). For example, the original `0x0EE` (`…`) is used this way. Each `en` character may only appear once in the whole file.

### Limits

- The game has room for glyph ids up to `0x2FF`, so you can add about 140 more glyphs.
- The game draws all text in capitals: `é` and `É` both become your `É` glyph.
- The **OPTION** labels (max 11 characters) and **YES / NO / END** (max 4 characters) use the game's original wide A-Z letters. Other characters there use your CUSTOM glyphs.

---

## 6. Text drawn with a different font

- **The intro story, the SAVE/LOAD prompts and the title screen credits** are drawn as pictures with the Windows *Georgia* font, not the game font (`tools\intro_patch.py`, `tools\save_load_patch.py`, `tools\add_patch_credits.py`). They still take their text from `script_en.json`, and `glyph_table.tsv` does not apply to them. Georgia covers Latin, Greek and Cyrillic letters. Other scripts need a different font set in those files.

---

## 7. What each tool does

You only run the **scripts** at the top. The rest are used by them automatically and must stay in the `tools` folder.

**Scripts you run:**

| File | Purpose |
|---|---|
| `extract_rom.py` | One-time setup: extracts the ROM into `.WORK\extracted\` |
| `script_import.py` | `SCRIPT - FULL.txt` -> `script_en.json` |
| `glyph_import.py` | `GLYPHS - FULL.txt` -> `glyph_table.tsv` |
| `full_build.py` | Builds the patched ROM and `Patched_ROM_fit_report.tsv` |
| `script_dump.py` | `script_en.json` -> `SCRIPT - FULL.txt` |
| `glyph_dump.py` | `glyph_table.tsv` -> `GLYPHS - FULL.txt` |

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
