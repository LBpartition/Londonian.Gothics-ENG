# Build and publish tmp_b\Full.nds as a fresh OUTPUTS\<timestamp>-RC1 folder with correct created/modified times.
param([string]$Note = "")
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot)
# Always build fresh and publish exactly what this build produced.
Push-Location (Join-Path $root '.WORK'); $env:PYTHONIOENCODING = 'utf-8'
Remove-Item tmp_b\*.nds -ErrorAction SilentlyContinue
python tools\full_build.py tmp_b Full 1
if ($LASTEXITCODE -ne 0 -or -not (Test-Path tmp_b\Full.nds)) { Pop-Location; throw 'build failed' }
$fails = @(Import-Csv tmp_b\fit_report.tsv -Delimiter "`t" | Where-Object { $_.status -like 'FAIL*' }).Count
Pop-Location
if ($fails) { throw "$fails fit failures - not publishing" }
$now = Get-Date
$ts = $now.ToString('yyyy.MM.dd-HH.mm.ss')
$new = Join-Path $root "OUTPUTS\$ts-RC1"
$old = Get-ChildItem (Join-Path $root 'OUTPUTS') -Directory | Where-Object Name -like '*-RC1' | Where-Object FullName -ne $new
New-Item -ItemType Directory $new | Out-Null
$rom = Join-Path $new 'Londonian Gothics - Lolita in the Labyrinth [ENG-RC1].nds'
[IO.File]::WriteAllBytes($rom, [IO.File]::ReadAllBytes((Join-Path $root '.WORK\tmp_b\Full.nds')))
[IO.File]::WriteAllBytes((Join-Path $new 'fit_report.tsv'), [IO.File]::ReadAllBytes((Join-Path $root '.WORK\tmp_b\fit_report.tsv')))
foreach ($p in @($rom, (Join-Path $new 'fit_report.tsv'), $new)) {
    $i = Get-Item -LiteralPath $p; $i.CreationTime = $now; $i.LastWriteTime = $now
}
$old | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
Push-Location (Join-Path $root '.WORK'); $env:PYTHONIOENCODING = 'utf-8'; python tools\script_dump.py; Pop-Location
$h = (Get-FileHash -LiteralPath $rom).Hash
$n = Join-Path $root 'DOCS\!~HARDWARE TEST NOTES.txt'
$t = [IO.File]::ReadAllText($n) -replace '\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d-RC1', "$ts-RC1" -replace '\(SHA256 [0-9A-F]{8}\.\.\.\)', "(SHA256 $($h.Substring(0,8))...)"
[IO.File]::WriteAllText($n, $t)
Add-Content (Join-Path $root 'pipeline.txt') "`r`n[$ts] $Note Published $ts-RC1 SHA256 $h"
"$ts-RC1 $h"
