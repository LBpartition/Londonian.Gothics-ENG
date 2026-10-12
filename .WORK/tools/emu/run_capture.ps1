param(
  [Parameter(Mandatory)] [string]$Rom,
  [Parameter(Mandatory)] [string]$Job,
  [Parameter(Mandatory)] [string]$OutDir,
  [int]$TimeoutSec = 300
)
$ErrorActionPreference = 'Stop'
$emu = 'C:\3DS\BizHawk\EmuHawk.exe'
New-Item -ItemType Directory -Force $OutDir | Out-Null
$env:BH_JOB = (Resolve-Path $Job).Path
$env:BH_OUT = (Resolve-Path $OutDir).Path
$lua = Join-Path $PSScriptRoot 'capture.lua'
$p = Start-Process $emu -ArgumentList "--lua=`"$lua`"", "`"$((Resolve-Path $Rom).Path)`"" -PassThru
if (-not $p.WaitForExit($TimeoutSec * 1000)) { Stop-Process -Id $p.Id; throw "Timed out after $TimeoutSec s" }
Get-Content (Join-Path $OutDir 'capture_log.txt')
