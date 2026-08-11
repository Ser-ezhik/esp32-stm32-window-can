# Electrical audit

Audit target: `kicad/UNIVERSAL-4CH-F103RC-IC.kicad_pcb`.

## Voltage domains

| Domain | Nominal voltage | Source | Loads |
| --- | ---: | --- | --- |
| Motor channel 1..4 | 12 V | Pin 1 of each J1..J4 harness | VNH5019A-E and local bulk capacitor |
| Logic input | 12 V | J230 through F230, D230 and D231 | MP1584 and TLV6700 |
| Logic rail | 5 V | Soldered MP1584 module | Reed sensors and hold-up diode |
| Hold-up rail | about 4.7 V | D280 from 5 V | C280 and AMS1117 input |
| Logic | 3.3 V | AMS1117 through R2301 | STM32, CAP1188, EEPROM and CAN module |

All fitted capacitor voltage ratings exceed their nominal rail. The 12 V
logic path uses 25 V or 50 V ceramics and a 50 V bulk capacitor. VNH channel
bulk capacitors are 35 V and local ceramics are 50 V. The 5 V and hold-up
rails use 10 V capacitors.

## Mandatory assembly conditions

- Fit the insulated wire from `C280+` to `J280B`. It is the designed connection
  between the isolated hold-up capacitor and the AMS1117 input. Without it the
  3.3 V rail is off.
- Supply motor power to pin 1 of every populated J1..J4 connector. These four
  motor feeds are separate from J230 and must be externally fused for 5 A per
  channel or less, selected to suit the actual actuator wiring.
- Fit R240 only at a physical end of the CAN trunk. Leave it DNP at intermediate
  nodes.
- Use 2 oz finished copper for the checked 5 A routing margin.

## Corrected issue

The former `S2_3V3` island feeding the channel 3 and 4 diagnostic pull-ups and
ADC clamps had no source. It is now merged and physically routed to `S1_3V3`.
The electrical audit fails if that legacy orphan net returns.

## Automated checks

```powershell
$py = 'C:\Users\Ezhik\AppData\Local\Programs\KiCad\10.0\bin\python.exe'
& $py tools\verify_universal4ch_f103rc_board.py hardware\UNIVERSAL-4CH-F103RC-IC\kicad\UNIVERSAL-4CH-F103RC-IC.kicad_pcb
& $py tools\audit_universal4ch_f103rc_electrical.py hardware\UNIVERSAL-4CH-F103RC-IC\kicad\UNIVERSAL-4CH-F103RC-IC.kicad_pcb
& $py tools\audit_universal4ch_power_width.py hardware\UNIVERSAL-4CH-F103RC-IC\kicad\UNIVERSAL-4CH-F103RC-IC.kicad_pcb
python tools\verify_universal4ch_f103rc_firmware.py
```
