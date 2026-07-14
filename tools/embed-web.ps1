$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root 'web\index.html'
$target = Join-Path $root 'ArduinoIDE\ESP32_CC1101_CAN_Master\WebUi.h'
$html = [System.IO.File]::ReadAllText($source, [System.Text.Encoding]::UTF8)
$header = @"
#pragma once

static const char WEB_UI_HTML[] PROGMEM = R"WINDOWUI(
$html
)WINDOWUI";
"@
[System.IO.File]::WriteAllText($target, $header, [System.Text.UTF8Encoding]::new($false))
