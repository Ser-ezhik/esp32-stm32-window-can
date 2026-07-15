param(
  [int]$Port = 8766,
  [string]$WebRoot = (Join-Path $PSScriptRoot "..\web")
)

$objects = @(
  @{ id = 0; cabinetId = 1; name = "Double door"; type = 2; actuatorCount = 8; online = $true; state = 2; position = 2; fault = 0 },
  @{ id = 1; cabinetId = 2; name = "Single door 1"; type = 1; actuatorCount = 4; online = $true; state = 3; position = 3; fault = 0 },
  @{ id = 2; cabinetId = 3; name = "Single door 2"; type = 1; actuatorCount = 4; online = $true; state = 2; position = 1; fault = 0 },
  @{ id = 3; cabinetId = 4; name = "Single door 3"; type = 1; actuatorCount = 4; online = $false; state = 1; position = 0; fault = 0 },
  @{ id = 4; cabinetId = 5; name = "Window"; type = 0; actuatorCount = 2; online = $true; state = 5; position = 3; fault = 7 }
)

function Send-Response($Response, [string]$ContentType, [byte[]]$Body, [int]$Status = 200) {
  $Response.StatusCode = $Status
  $Response.ContentType = $ContentType
  $Response.ContentLength64 = $Body.Length
  $Response.OutputStream.Write($Body, 0, $Body.Length)
  $Response.Close()
}

function Send-Json($Response, $Value) {
  $json = $Value | ConvertTo-Json -Depth 8 -Compress
  Send-Response $Response "application/json; charset=utf-8" ([Text.Encoding]::UTF8.GetBytes($json))
}

$listener = [Net.HttpListener]::new()
$listener.Prefixes.Add("http://127.0.0.1:$Port/")
$listener.Start()

while ($listener.IsListening) {
  $context = $listener.GetContext()
  $request = $context.Request
  $response = $context.Response
  $path = $request.Url.AbsolutePath

  if ($path -eq "/" -or $path -eq "/index.html") {
    $body = [IO.File]::ReadAllBytes((Join-Path $WebRoot "index.html"))
    Send-Response $response "text/html; charset=utf-8" $body
  } elseif ($path -eq "/api/objects") {
    Send-Json $response @{ objects = $objects }
  } elseif ($path -eq "/api/object") {
    $id = [int]$request.QueryString["id"]
    $item = $objects | Where-Object { $_.id -eq $id } | Select-Object -First 1
    $actuators = for ($i = 0; $i -lt $item.actuatorCount; $i++) {
      @{ online = $true; current = 1180 + $i * 170; pwm = 100 - $i * 3; direction = "stop"; calibrated = $i -lt 6 }
    }
    $detail = @{} + $item
    $detail.reeds = if ($id -eq 0) { 2 } else { 0 }
    $detail.cap = if ($id -eq 4) { 1 } else { 0 }
    $detail.capEnabledMask = if ($id -eq 0) { 63 } else { 7 }
    $detail.capNoise = $id -eq 1
    $detail.powerGood = $true
    $detail.maxCurrent = 2370
    $detail.actuators = $actuators
    Send-Json $response $detail
  } elseif ($path -eq "/api/remotes") {
    Send-Json $response @{ learning = $false; remotes = @(
      @{ index = 0; code = "A1B2C3"; name = "Open double door"; action = "open"; targetMask = "0000000000000001" },
      @{ index = 1; code = "D4E5F6"; name = "Stop all"; action = "stop"; targetMask = "000000000000001F" }
    ) }
  } elseif ($path -eq "/api/events") {
    Send-Json $response @{ events = @(
      @{ time = "12 s"; object = "Window"; text = "safety edge" },
      @{ time = "4 s"; object = "System"; text = "ESP32 started" }
    ) }
  } elseif ($path -eq "/api/settings") {
    Send-Json $response @{ systemName = "Door test bench"; canRate = 500000; firmware = "0.1.0-alpha.2" }
  } elseif ($path -eq "/api/discovery") {
    Send-Json $response @{ nodes = @(@{ uid = "12AB34CD"; configured = $true; cabinetId = 1; firmware = 2 }) }
  } elseif ($request.HttpMethod -eq "POST") {
    Send-Json $response @{ ok = $true }
  } else {
    Send-Json $response @{ error = "not_found" }
  }
}
