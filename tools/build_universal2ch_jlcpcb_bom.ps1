param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

$fabrication = Join-Path $ProjectRoot 'hardware\UNIVERSAL-2CH\fabrication'
$inputDir = Join-Path $fabrication 'pcba-raw'
$outputDir = Join-Path $fabrication 'pcba-jlcpcb-smd-only'
$inputBom = Join-Path $inputDir 'UNIVERSAL-2CH_BOM_SMD_ONLY_raw.csv'
$inputCpl = Join-Path $inputDir 'UNIVERSAL-2CH_CPL_SMD_ONLY_raw.csv'
$outputBom = Join-Path $outputDir 'UNIVERSAL-2CH_BOM_JLCPCB_SMD_ONLY.csv'
$outputCpl = Join-Path $outputDir 'UNIVERSAL-2CH_CPL_JLCPCB_SMD_ONLY.csv'
$manualBom = Join-Path $outputDir 'UNIVERSAL-2CH_MANUAL_ASSEMBLY.csv'
$orientationAudit = Join-Path $outputDir 'UNIVERSAL-2CH_PCBA_ORIENTATION_AUDIT.csv'

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

function Resolve-Part {
    param($Row, [string]$Reference)

    $comment = $Row.Comment
    $footprint = $Row.Footprint

    if ($footprint -eq 'C_0603_1608Metric') {
        return @{ Comment = '100nF 50V X7R; YAGEO CC0603KRX7R9BB104'; Lcsc = 'C14663' }
    }
    if ($Reference -eq 'C231') {
        return @{ Comment = '1uF 50V X7R 1206; CCTC TCC1206X7R105M500FT'; Lcsc = 'C5448921' }
    }
    if ($Reference -in @('C234', 'C236', 'C238')) {
        return @{ Comment = '10uF 25V X7R 1206; YAGEO CC1206KKX7R8BB106'; Lcsc = 'C70462' }
    }
    switch ($Reference) {
        'D230' { return @{ Comment = 'SS54 5A 40V SMB; LGE SS54'; Lcsc = 'C432139' } }
        'D231' { return @{ Comment = 'SMBJ16A 600W unidirectional SMB; LGE SMBJ16A'; Lcsc = 'C713715' } }
        'D240' { return @{ Comment = '24V bidirectional CAN ESD SOD-323; Yint ESD24VD3B'; Lcsc = 'C484324' } }
        'D241' { return @{ Comment = '24V bidirectional CAN ESD SOD-323; Yint ESD24VD3B'; Lcsc = 'C484324' } }
        'L240' { return @{ Comment = 'CAN common-mode choke 100uH 1812; TDK ACT45B-101-2P-TL003'; Lcsc = 'C88056' } }
        'U230' { return @{ Comment = 'AMS1117-3.3 SOT-223'; Lcsc = 'C6186' } }
        'U250' { return @{ Comment = '25LC256-I/SN SPI EEPROM SOIC-8'; Lcsc = 'C84670' } }
        'U270' { return @{ Comment = 'TLV6700DDCR power monitor TSOT-23-6'; Lcsc = 'C2868382' } }
    }

    if ($Reference -match '^D(11|12)01$') {
        return @{ Comment = 'BAT54S dual series Schottky SOT-23; Nexperia BAT54S,215'; Lcsc = 'C47546' }
    }
    if ($footprint -eq 'R_0603_1608Metric') {
        if ($comment -match '^100R') { return @{ Comment = '100R 1% 0603; UNI-ROYAL 0603WAF1000T5E'; Lcsc = 'C22775' } }
        if ($comment -match '^1K(?: |_)') { return @{ Comment = '1K 1% 0603; UNI-ROYAL 0603WAF1001T5E'; Lcsc = 'C21190' } }
        if ($comment -match '^4K7') { return @{ Comment = '4.7K 1% 0603; UNI-ROYAL 0603WAF4701T5E'; Lcsc = 'C23162' } }
        if ($comment -match '^10K') { return @{ Comment = '10K 1% 0603; UNI-ROYAL 0603WAF1002T5E'; Lcsc = 'C25804' } }
        if ($comment -match '^47K') { return @{ Comment = '47K 1% 0603; UNI-ROYAL 0603WAF4702T5E'; Lcsc = 'C25819' } }
        if ($comment -match '^0R') { return @{ Comment = '0R 0603; UNI-ROYAL 0603WAF0000T5E'; Lcsc = 'C21189' } }
        if ($comment -match '^226K') { return @{ Comment = '226K 1% 0603; FH RS-03K2263FT'; Lcsc = 'C321793' } }
    }

    throw "No verified LCSC mapping for $Reference ($comment, $footprint)"
}

$expanded = foreach ($row in (Import-Csv $inputBom)) {
    foreach ($reference in ($row.Designator -split ',')) {
        $part = Resolve-Part -Row $row -Reference $reference
        [pscustomobject]@{
            Reference = $reference
            Comment = $part.Comment
            Footprint = $row.Footprint
            Lcsc = $part.Lcsc
        }
    }
}

$bom = $expanded |
    Group-Object Lcsc, Footprint, Comment |
    ForEach-Object {
        $refs = $_.Group.Reference | Sort-Object { [regex]::Replace($_, '\d+', { param($m) $m.Value.PadLeft(8, '0') }) }
        [pscustomobject]@{
            Comment = $_.Group[0].Comment
            Designator = $refs -join ','
            Footprint = $_.Group[0].Footprint
            'LCSC Part #' = $_.Group[0].Lcsc
        }
    } |
    Sort-Object Designator

function Get-RotationCorrection {
    param([string]$Reference, [string]$Footprint)
    if ($Reference -in @('D230', 'D231')) { return 180.0 }
    if ($Footprint -match '^SOT-223') { return 180.0 }
    if ($Footprint -match '^SOT-23') { return 180.0 }
    if ($Footprint -match '^TSOT-23') { return 180.0 }
    if ($Footprint -match '^SOIC-8_') { return 270.0 }
    return 0.0
}

function Format-InvariantNumber {
    param([double]$Value, [string]$Format = 'F1')
    return $Value.ToString($Format, [System.Globalization.CultureInfo]::InvariantCulture)
}

$assemblyReferences = [System.Collections.Generic.HashSet[string]]::new([string[]]$expanded.Reference)
$partsByReference = @{}
foreach ($part in $expanded) { $partsByReference[$part.Reference] = $part }

$auditRows = @()
$cpl = Import-Csv $inputCpl |
    Where-Object { $assemblyReferences.Contains($_.Designator) } |
    ForEach-Object {
        $part = $partsByReference[$_.Designator]
        $baseRotation = [double]$_.Rotation
        $correction = Get-RotationCorrection -Reference $_.Designator -Footprint $part.Footprint
        $finalRotation = ($baseRotation + $correction) % 360.0
        if ($correction -ne 0.0) {
            $auditRows += [pscustomobject]@{
                Reference = $_.Designator
                Footprint = $part.Footprint
                BaseRotation = Format-InvariantNumber $baseRotation
                JlcCorrection = Format-InvariantNumber $correction '+0.0;-0.0;0.0'
                FinalRotation = Format-InvariantNumber $finalRotation
            }
        }
        [pscustomobject]@{
            Designator = $_.Designator
            'Mid X' = $_.'Mid X'
            'Mid Y' = $_.'Mid Y'
            Layer = $_.Layer
            Rotation = Format-InvariantNumber $finalRotation
        }
    }

$bom | Export-Csv -Path $outputBom -NoTypeInformation -Encoding utf8
$cpl | Export-Csv -Path $outputCpl -NoTypeInformation -Encoding utf8
$auditRows | Export-Csv -Path $orientationAudit -NoTypeInformation -Encoding utf8
Copy-Item (Join-Path $inputDir 'UNIVERSAL-2CH_MANUAL_ASSEMBLY_raw.csv') $manualBom -Force

$bomRefs = [System.Collections.Generic.HashSet[string]]::new([string[]]$expanded.Reference)
$cplRefs = [System.Collections.Generic.HashSet[string]]::new([string[]]$cpl.Designator)
$missingFromCpl = $bomRefs.Where({ -not $cplRefs.Contains($_) })
$missingFromBom = $cplRefs.Where({ -not $bomRefs.Contains($_) })
if ($missingFromCpl.Count -or $missingFromBom.Count) {
    throw "BOM/CPL mismatch. Missing from CPL: $($missingFromCpl -join ','); missing from BOM: $($missingFromBom -join ',')"
}
if ($cpl | Where-Object Layer -ne 'Top') {
    throw 'SMD-only assembly contains a non-top component.'
}

Write-Host "Generated $($bom.Count) BOM lines and $($cpl.Count) top-side placements."
Write-Host $outputBom
Write-Host $outputCpl
Write-Host $manualBom
Write-Host $orientationAudit
