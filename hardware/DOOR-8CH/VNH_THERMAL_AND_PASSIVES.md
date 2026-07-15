# VNH5019 thermal zones and mandatory passive parts

## Complete circuit per VNH5019A-E

Every populated VNH position has all of these fitted parts. None are optional
for normal operation.

| Function | Parts per VNH | Values |
| --- | ---: | --- |
| MCU input safe state | 3 pull-downs | 10 kOhm on PWM, INA, INB |
| MCU input protection | 3 series resistors | 100 Ohm on PWM, INA, INB |
| Bridge enable / fault readback | 1 pull-up | 4.7 kOhm to 3.3 V, shared by ENA/DIAGA and ENB/DIAGB |
| Current-sense enable | 1 pull-down | 10 kOhm from CS_DIS to GND |
| Current-sense load | 1 resistor | 1.00 kOhm, 1% from CS to GND |
| Current-sense divider | 2 resistors | 68 kOhm and 100 kOhm, 1% |
| ADC anti-noise filter | 1 resistor + 1 capacitor | 1 kOhm + 100 nF at PA0/PA1 |
| VNH local power decoupling | 1 electrolytic + 1 ceramic | 470 uF / 35 V low-ESR + 100 nF / 50 V X7R |

The capacitor pair is placed directly beside the VNH power pins. The CS divider
and ADC filter sit in the low-noise area near the corresponding STM32 socket.
Every component reference and value is present in the future KiCad schematic;
no firmware pull-up is used as a substitute for these safety parts.

## Thermal and heatsink footprint

Every VNH position receives:

- three large copper areas under the three exposed MultiPowerSO-30 slugs;
- dense thermal-via arrays from each slug area to the internal copper layers;
- a 30 x 30 mm component keepout around the package top;
- two non-plated M3 mounting holes outside the copper keepout, one pair per VNH;
- silkscreen polarity/insulation warning beside each heatsink area.

The holes accept a small 20 x 20 x 10 mm finned aluminium heatsink or a custom
bracket. Fit a heatsink after thermal testing, or fit it from the first build
when the cabinet has poor airflow.

## Electrical isolation rule

The VNH5019 exposed thermal slugs are not a common ground pad: they correspond
to `VCC`, `OUTA` and `OUTB`. A metal heatsink must therefore never touch the
package directly or bridge any slug copper areas.

Use one electrically insulating, thermally conductive pad (silicone/Sil-Pad or
Kapton thermal pad, 0.2 to 0.5 mm) between the VNH package and the heatsink.
Use nylon screws and spacers, or a mechanically isolated bracket. Check with a
multimeter that the heatsink has no continuity to VCC, OUTA, OUTB or GND before
powering the board.

The source for the exposed-pad electrical functions and thermal layout is the
[ST VNH5019A-E data sheet](https://www.st.com/resource/en/datasheet/vnh5019a-e.pdf).
