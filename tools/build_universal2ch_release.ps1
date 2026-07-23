param(
    [string]$Version = 'v1.0',
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

$kicadRoot = 'C:\Users\Ezhik\AppData\Local\Programs\KiCad\10.0'
$kicadCli = Join-Path $kicadRoot 'bin\kicad-cli.exe'
$kicadPython = Join-Path $kicadRoot 'bin\python.exe'
$project = Join-Path $ProjectRoot 'hardware\UNIVERSAL-2CH'
$board = Join-Path $project 'kicad\UNIVERSAL-2CH.kicad_pcb'
$flatSchematic = Join-Path $project 'kicad\UNIVERSAL-2CH.kicad_sch'
$multiSchematic = Join-Path $project 'kicad\UNIVERSAL-2CH-multisheet.kicad_sch'
$fabrication = Join-Path $project 'fabrication'
$release = Join-Path $fabrication $Version
$gerbers = Join-Path $release 'gerbers'
$zip = Join-Path $fabrication "UNIVERSAL-2CH_JLCPCB_Gerber_$Version.zip"

$resolvedFabrication = [IO.Path]::GetFullPath($fabrication)
$resolvedRelease = [IO.Path]::GetFullPath($release)
if (-not $resolvedRelease.StartsWith($resolvedFabrication + [IO.Path]::DirectorySeparatorChar)) {
    throw "Release directory escaped fabrication root: $resolvedRelease"
}
if (Test-Path -LiteralPath $release) {
    Remove-Item -LiteralPath $release -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $gerbers | Out-Null

& $kicadPython (Join-Path $ProjectRoot 'tools\export_universal2ch_placement.py')
if ($LASTEXITCODE) { throw 'Placement export failed' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
    (Join-Path $ProjectRoot 'tools\build_universal2ch_jlcpcb_bom.ps1') -ProjectRoot $ProjectRoot
if ($LASTEXITCODE) { throw 'BOM/CPL generation failed' }

& $kicadCli pcb drc --exit-code-violations -o (Join-Path $release "UNIVERSAL-2CH-drc-$Version.rpt") $board
if ($LASTEXITCODE) { throw 'PCB DRC failed' }
& $kicadCli sch erc --exit-code-violations -o (Join-Path $release "UNIVERSAL-2CH-flat-erc-$Version.rpt") $flatSchematic
if ($LASTEXITCODE) { throw 'Flat schematic ERC failed' }
& $kicadCli sch erc --exit-code-violations -o (Join-Path $release "UNIVERSAL-2CH-multisheet-erc-$Version.rpt") $multiSchematic
if ($LASTEXITCODE) { throw 'Multisheet schematic ERC failed' }

& $kicadCli pcb export gerbers --board-plot-params --check-zones -o $gerbers $board
if ($LASTEXITCODE) { throw 'Gerber export failed' }
& $kicadCli pcb export drill --format excellon --excellon-units mm --excellon-separate-th -o $gerbers $board
if ($LASTEXITCODE) { throw 'Drill export failed' }

$pcbaDir = Join-Path $fabrication 'pcba-jlcpcb-smd-only'
Copy-Item (Join-Path $pcbaDir 'UNIVERSAL-2CH_BOM_JLCPCB_SMD_ONLY.csv') $release
Copy-Item (Join-Path $pcbaDir 'UNIVERSAL-2CH_CPL_JLCPCB_SMD_ONLY.csv') $release
Copy-Item (Join-Path $pcbaDir 'UNIVERSAL-2CH_MANUAL_ASSEMBLY.csv') $release
Copy-Item (Join-Path $pcbaDir 'UNIVERSAL-2CH_PCBA_ORIENTATION_AUDIT.csv') $release

if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -Path (Join-Path $gerbers '*') -DestinationPath $zip -CompressionLevel Optimal

$hash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
Write-Host "Release: $release"
Write-Host "Gerber ZIP: $zip"
Write-Host "SHA-256: $hash"
