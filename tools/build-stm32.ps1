$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    arduino-cli compile `
        --fqbn 'STMicroelectronics:stm32:GenF1:pnum=GENERIC_F103C8TX,xserial=none,usb=none,opt=oslto,dbg=none,rtlib=nano' `
        --libraries libraries `
        --warnings all `
        --export-binaries `
        ArduinoIDE\STM32_Universal_Actuator_Node
}
finally {
    Pop-Location
}
