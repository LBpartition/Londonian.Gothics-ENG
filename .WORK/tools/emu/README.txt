Scripted BizHawk capture harness (BizHawk 2.11.1 at C:\3DS\BizHawk, melonDS core)

Usage:
  .\run_capture.ps1 -Rom <rom.nds> -Job <job.txt> -OutDir <folder> [-TimeoutSec 300]

Job commands (one per line, # comments):
  wait <frames>
  press <Button[+Button]> [frames]   e.g. press A, press Start, press Up+B 4
  touch <x> <y> [frames]             bottom-screen coordinates
  shot <name>                        -> <OutDir>\<name>_f<frame>.png (256x384, top over bottom)
  savestate <path> / loadstate <path>
  exit

Screenshots come from the emulator framebuffer (not the desktop), so resolution,
orientation and timing are exact. A capture_log.txt is written to OutDir.
Verified 2026-10-10: smoke test booted the JPN ROM, 3 shots, 784 frames in ~20 s.
