# Translating Londonian Gothics to other languages

This guide explains how to make your own translation patch from the files in this repository.

**Steps**

1. [Download or clone the repository](#1-download-or-clone-the-repository)
2. [Install the requirements and add the ROM](#2-install-the-requirements-and-add-the-rom)
3. [(Optional) Add your own letters: `EDIT and IMPORT - GLYPHS.txt`](#3-optional-add-your-own-letters-edit-and-import---glyphstxt)
4. [Translate the script: `EDIT and IMPORT - SCRIPT.txt`](#4-translate-the-script-edit-and-import---scripttxt)
5. [Build and test your patched ROM](#5-build-and-test-your-patched-rom)

**Reference**

- [The files in `tools-resources`](#the-files-in-tools-resources)
- [Text drawn with a different font](#text-drawn-with-a-different-font)
- [Editing `_import_script.json` / `_import_glyph_table.tsv` directly (advanced)](#editing-_import_scriptjson--_import_glyph_tabletsv-directly-advanced)
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

This unpacks the ROM into `.WORK\extracted\`, which the build needs. It also writes `.WORK\tools-resources\.script_jpn.json` (the original Japanese text, for reference; it isn't stored in the repository), and a list of the ROM's files and a short report to `.WORK\out\Extracted-ROM-Report\` (for information only).

---

## 3. (Optional) Add your own letters: `EDIT and IMPORT - GLYPHS.txt`

Skip this step if your language only needs the letters that are already there:

```
A-Z  a-z  0-9  space  . , ' - ! ? & * : ; ( ) / " # % _ < > … £
```

Lower-case letters are shown in dialogue, locations, dresses and items. Menus are always shown in capitals.

### How the font works

The game draws text with a font of small pictures called **glyphs**. Each glyph is 16 × 16 pixels and has a number (its **id**, in hexadecimal):

- **`0x000`-`0x246`** are the game's **ORIGINAL** Japanese glyphs. You can't redraw these, but you can reuse them (see below).
- **From `0x247`** are the **CUSTOM** glyphs added for the English patch: the space, punctuation, digits, the narrow A-Z capitals and the a-z lower-case letters. You can redraw these and add more.

Every glyph is in **`EDIT and IMPORT - GLYPHS.txt`**, drawn as a picture made of characters. Edit it, then import it (step 5 below).

### The preview: `EDIT and IMPORT - GLYPHS - PREVIEW.png`

To find a glyph quickly, open **`EDIT and IMPORT - GLYPHS - PREVIEW.png`**. It is a sheet of every glyph:

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

- **Up/down position matters.** The capitals and digits start on the 4th row (3 empty rows above) and are 11 rows tall, so keep new letters on the same rows. Accents can go in the empty rows above. Lower-case letters sit on the same bottom line (row 14): small letters like `a` start on row 8 (7 rows tall), tall ones like `b` start on row 4, and tails (`g j p q y`) use the last 2 rows.
- **Left/right position doesn't matter.** The build measures the inked columns of each glyph and spaces letters automatically. Just start at the left edge, like the existing letters.

### Adding a new letter (e.g. `É`)

1. **Copy a similar CUSTOM block** and paste it at the very **end** of the file. For `É`, copy the block for `E` (`0x24F`).
2. **Change the id** to the next number after the last glyph. The last glyph is `0x28D`, so your first new glyph is `0x28F`, then `0x28F`, and so on. CUSTOM ids must count up **without gaps**.
3. **Set `char:` and `en:`** to your character (`É`), and change the `note:`.
4. **Draw it.** For `É`, the `E` already starts on row 4, so just add the accent in the two rows above it:

   ```
   ==== 0x28F ==== (CUSTOM)
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

   It lists the glyphs you changed and redraws `EDIT and IMPORT - GLYPHS - PREVIEW.png`. If something is wrong (a gap in the ids, a character used twice, an unknown picture character, an ORIGINAL glyph redrawn) it stops with an error and changes nothing.
6. **Use it** in your script: type `É` anywhere in `EDIT and IMPORT - SCRIPT.txt`. (If you type `é` and there is no `é` glyph, the build uses `É` instead. Draw an `é` glyph too if you want a lower-case one.)

To **redraw an existing CUSTOM letter** (e.g. to change the style of `A`), just edit its picture and import.

**You don't need to change any of the Python scripts.** The build automatically draws your glyphs into the game's font, works out each glyph's width from its pixels, uses that width when checking whether lines fit, and uses your glyph wherever its character appears (dialogue, locations, dresses, items and menus).

### Reusing an original glyph instead of drawing one

If one of the game's original glyphs (`0x000`-`0x246`) already looks like the character you need, type your character on that glyph's `en:` line instead of drawing a new one, then import. For example, the original `0x0EE` (`…`) is used this way.

### Limits

- The game has room for glyph ids up to `0x2FF`, so you can add about 115 more glyphs.
- A lower-case letter with no glyph of its own is shown as its capital. Menus are always shown in capitals.
- The **OPTION** screen text (max 11 characters per line) and **YES / NO / END** (max 4 characters) use the game's original wide A-Z and 0-9 letters. Other characters there use your CUSTOM glyphs.
- The intro story, SAVE/LOAD prompts and title screen credits don't use these glyphs (see [Text drawn with a different font](#text-drawn-with-a-different-font)).

---

## 4. Translate the script: `EDIT and IMPORT - SCRIPT.txt`

**`EDIT and IMPORT - SCRIPT.txt`** contains **all** text in the game, in playthrough order: title screen credits, intro, dialogue, locations, dresses, items and menus. Replace the English with your translation, then import it:

```
python tools\script_import.py
```

It reports how many entries changed. For reference, the original Japanese is in `.script_jpn.json` (same order), and the GameFAQs guide the English is based on is in `.script_ShadowRisae_Guide.txt`.

### The golden rule

**Change the text only. Do not add, remove or reorder entries, and leave the section headings alone.**
Each entry is matched to its place in the game by its position.

### Formatting

| You write | In-game result |
|---|---|
| `{word}` | *word* shown in red (highlighted) |
| Each separate line | A separate line on screen. Text is not re-wrapped for you. |
| lower or UPPER case | Shown as typed (menus are always shown in CAPITALS) |

### Dialogue boxes

A dialogue box shows **3 lines**. A `---` line starts a new box. You *can* add or remove `---` lines inside a dialogue entry to split its text over more or fewer boxes. A box with fewer than 3 lines is padded with blank lines automatically. This only changes how that entry's text is split into boxes, not the entries themselves.

### Making text fit

Each line must fit the width of its box. Letters are drawn at their own width (an `I` is narrower than an `M`), so the limit is in pixels, not characters.

- **Check before testing:** every build writes `out\Patched_ROM_fit_report.tsv`, listing every line with **ok** / **FAIL**. Fix every **FAIL** line.
- **Dialogue too long?** Move words to the next line. If the box is full (3 lines), add a `---` line to continue in a new box. There's no limit on the number of boxes in an entry.
- **Names, dresses, items, locations and menus** can't get extra boxes, so use shorter wording or abbreviations.
- **OPTION screen:** every line of `MENU TEXT (OPTION screen)` is on that screen, including the text the Japanese game already showed in English (OPTION, BGM, BACK, ON, OFF). The volume levels `1`-`5` and the arrows `<` `>` are placed one by one by the game, so keep them to a single character.
- **SAVE / LOAD screens:** the words after `SAVED` (`SAVE`, `LOAD`, `SUCCESS`, `ERROR`, …) were already English in the Japanese game and appear on the save screen. Max 11 characters per line.
- **Repeated lines:** if a line (e.g. *Knock, Knock, Knock*) is shown more than once in a scene, each time it's shown has its own entry, so you can translate each one separately.
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

Every entry in `_import_script.json` has a `"source"`: where its English came from (`shadowrisae` = the GameFAQs guide, `mtl` = machine translation, `original` = already in English in the Japanese game). It doesn't change the game text, but it **is used for the `<HUMAN>` / `<MTL>` percentages**. The percentages count dialogue lines, intro paragraphs, dress and item names and descriptions, location names, character names and menu entries (`original` entries are not counted). If they don't make sense for your translation, either change the `"source"` values in `_import_script.json` to match your own work, or just remove `<HUMAN>` / `<MTL>` from your credit lines.

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

If a character in your script isn't in the font, the build stops and names it: add it in [step 3](#3-optional-add-your-own-letters-edit-and-import---glyphstxt).

**Typical loop:** edit `EDIT and IMPORT - SCRIPT.txt` → `python tools\script_import.py` → `python tools\full_build.py out Patched_ROM 1` → test → repeat.

---

## The files in `tools-resources`

File names tell you what each file is for:

- **`EDIT and IMPORT - ...`**: the files you edit.
- **`_import_...`**: what the build reads; written by the import scripts.
- **`.`** at the start: reference files and your ROM (`.script_jpn.json` and `.ROM_JPN.nds` are not in the repository).

| File | What it is | Edit it? |
|---|---|---|
| `EDIT and IMPORT - SCRIPT.txt` | All text in the game, laid out as an easy-to-read script. | **Yes** ([step 4](#4-translate-the-script-edit-and-import---scripttxt)) |
| `EDIT and IMPORT - GLYPHS.txt` | Every glyph of the font, drawn as an easy-to-edit 16 × 16 picture. | **Yes**, to add or redraw letters ([step 3](#3-optional-add-your-own-letters-edit-and-import---glyphstxt)) |
| `EDIT and IMPORT - GLYPHS - PREVIEW.png` | A picture of every glyph with its id and character. Redrawn by `glyph_import.py` / `glyph_dump.py`. | No, reference only |
| `_import_script.json` | The text the build actually reads. Written by `script_import.py`. | No (advanced: see below) |
| `_import_glyph_table.tsv` | The font table the build actually reads. Written by `glyph_import.py`. | No (advanced: see below) |
| `.script_jpn.json` | The original Japanese text, in the same order as `_import_script.json`. Created by `extract_rom.py` (not in the repository). | No, reference only |
| `.script_ShadowRisae_Guide.txt` | The English GameFAQs guide the English translation is based on. | No, reference only |
| `.ROM_JPN.nds` | The Japanese ROM you add in step 2 (not included in the repository). | No |

---

## Text drawn with a different font

**The intro story, the SAVE/LOAD prompts and the title screen credits** are drawn as pictures with the Windows *Georgia* font, not the game font (`tools\intro_patch.py`, `tools\save_load_patch.py`, `tools\add_patch_credits.py`). You still translate them in `EDIT and IMPORT - SCRIPT.txt` like everything else, but the glyphs from step 3 don't apply to them: any letter Georgia has works without adding glyphs. Georgia covers Latin, Greek and Cyrillic letters. Other scripts need a different font set in those files.

---

## Editing `_import_script.json` / `_import_glyph_table.tsv` directly (advanced)

You can edit the files the build reads instead of the `EDIT and IMPORT` files, but **don't edit both at once**: importing overwrites `_import_script.json` / `_import_glyph_table.tsv`, and the dump scripts overwrite the `EDIT and IMPORT` files.

- **`_import_script.json`** has the sections **credits**, **intro**, **dialogue**, **locations**, **dresses**, **items** and **menu**. Highlights are written `{H}word{/H}`, and in dialogue every 3 lines is one box (add blank `""` lines to pad a box). Afterwards, run `python tools\script_dump.py` to update `EDIT and IMPORT - SCRIPT.txt`.
- **`_import_glyph_table.tsv`** is tab-separated, one row per glyph: `id`, `char`, `en`, `note`, and for CUSTOM glyphs only, `top` (the first picture row, 0 = very top) and `pixels` (the picture, cropped to the inked rows, rows separated by `/`, `.` = empty). Afterwards, run `python tools\glyph_dump.py` to update `EDIT and IMPORT - GLYPHS.txt` and `EDIT and IMPORT - GLYPHS - PREVIEW.png`.

---

## What each tool does

You only run the **scripts** at the top. The rest are used by them automatically and must stay in the `tools` folder.

**Scripts you run:**

| File | Purpose |
|---|---|
| `extract_rom.py` | One-time setup: extracts the ROM into `.WORK\extracted\` and writes `.script_jpn.json` |
| `glyph_import.py` | `EDIT and IMPORT - GLYPHS.txt` -> `_import_glyph_table.tsv` (and redraws `EDIT and IMPORT - GLYPHS - PREVIEW.png`) |
| `script_import.py` | `EDIT and IMPORT - SCRIPT.txt` -> `_import_script.json` |
| `full_build.py` | Builds the patched ROM and `Patched_ROM_fit_report.tsv` |
| `glyph_dump.py` | `_import_glyph_table.tsv` -> `EDIT and IMPORT - GLYPHS.txt` and `EDIT and IMPORT - GLYPHS - PREVIEW.png` (advanced) |
| `script_dump.py` | `_import_script.json` -> `EDIT and IMPORT - SCRIPT.txt` (advanced) |

**Used by the build:**

| File | Purpose |
|---|---|
| `master.py` | Loads `_import_script.json` / `.script_jpn.json` |
| `jpn_script.py` | Writes `.script_jpn.json` from the extracted ROM (run by `extract_rom.py`) |
| `font_patch.py` | Draws the CUSTOM glyphs from `_import_glyph_table.tsv` into the font; maps your characters to glyphs |
| `font_tools.py` | Font helpers; reads the original glyph list from `_import_glyph_table.tsv`; location of the Japanese ROM |
| `vwf_patch.py` | Variable-width text (each letter drawn at its own width) |
| `textfit.py` | Line width / fit checking |
| `sp_tool.py` | Reads and writes the game's dialogue script files (`.sp`) |
| `ui_patch.py` | Dress, item and menu text |
| `intro_patch.py` | Draws the intro story text (a picture) |
| `save_load_patch.py` | Draws the SAVE/LOAD prompts (also a picture) |
| `add_patch_credits.py` | Draws the title screen credits; works out the `<HUMAN>` / `<MTL>` percentages |
| `ndsbuild.py` | Rebuilds the ROM |
| `repack_contig.py` | ROM file layout that also runs on 3DS (nds-bootstrap) |
