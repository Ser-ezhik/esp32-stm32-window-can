param(
    [string]$Version = 'v1.0-audited',
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$kicadRoot = 'C:\Program Files\KiCad\10.0'
$kicadCli = Join-Path $kicadRoot 'bin\kicad-cli.exe'
$kicadPython = Join-Path $kicadRoot 'bin\python.exe'
$project = Join-Path $ProjectRoot 'hardware\UNIVERSAL-2CH-F103-IC'
$board = Join-Path $project 'kicad\UNIVERSAL-2CH-F103-IC.kicad_pcb'
$fabrication = Join-Path $project 'fabrication'
$release = Join-Path $fabrication $Version
$gerbers = Join-Path $release 'gerbers'
$zip = Join-Path $release 'UNIVERSAL-2CH-F103-IC_GERBER.zip'
$stencilGerbers = Join-Path $release 'stencil-gerbers'
$stencilZip = Join-Path $release 'UNIVERSAL-2CH-F103-IC_STENCIL_GERBER.zip'

if (Test-Path -LiteralPath $release) { throw 'Release already exists; choose a new version.' }
New-Item -ItemType Directory -Force -Path $gerbers | Out-Null
New-Item -ItemType Directory -Force -Path $stencilGerbers | Out-Null
Get-ChildItem -LiteralPath $stencilGerbers -File | Remove-Item -Force

$previousReleaseVersion = $env:UNIVERSAL_2CH_RELEASE_VERSION
$env:UNIVERSAL_2CH_RELEASE_VERSION = $Version
& $kicadPython (Join-Path $ProjectRoot 'tools\export_universal2ch_f103_ic_pcba.py')
$env:UNIVERSAL_2CH_RELEASE_VERSION = $previousReleaseVersion
if ($LASTEXITCODE) { throw 'BOM/CPL export failed' }

& $kicadCli pcb drc --exit-code-violations `
    -o (Join-Path $release 'UNIVERSAL-2CH-F103-IC_DRC.rpt') $board
if ($LASTEXITCODE) { throw 'PCB DRC failed' }

& $kicadCli pcb export gerbers --board-plot-params --check-zones -o $gerbers $board
if ($LASTEXITCODE) { throw 'Gerber export failed' }
& $kicadCli pcb export drill --format excellon --excellon-units mm `
    --excellon-separate-th -o $gerbers $board
if ($LASTEXITCODE) { throw 'Drill export failed' }

$requiredGerbers = @(
    'UNIVERSAL-2CH-F103-IC-F_Cu.gbr',
    'UNIVERSAL-2CH-F103-IC-B_Cu.gbr',
    'UNIVERSAL-2CH-F103-IC-F_Mask.gbr',
    'UNIVERSAL-2CH-F103-IC-B_Mask.gbr',
    'UNIVERSAL-2CH-F103-IC-Edge_Cuts.gbr'
)
foreach ($requiredGerber in $requiredGerbers) {
    if (-not (Test-Path -LiteralPath (Join-Path $gerbers $requiredGerber))) {
        throw "Required fabrication layer is missing: $requiredGerber"
    }
}

if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -Path (Join-Path $gerbers '*') -DestinationPath $zip -CompressionLevel Optimal

& $kicadPython (Join-Path $ProjectRoot 'tools\export_stencil_gerbers.py') `
    $board $stencilGerbers
if ($LASTEXITCODE) { throw 'Stencil Gerber export failed' }
if (Test-Path -LiteralPath $stencilZip) { Remove-Item -LiteralPath $stencilZip -Force }
Compress-Archive -Path (Join-Path $stencilGerbers '*') `
    -DestinationPath $stencilZip -CompressionLevel Optimal

$hash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
Write-Host "Release: $release"
Write-Host "Gerber ZIP: $zip"
Write-Host "Stencil ZIP: $stencilZip"
Write-Host "SHA-256: $hash"
