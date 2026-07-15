# DOOR-8CH connector selection

## CAP1188 and reed sensors

The current PCB placement uses direct-wire spring terminals from the Phoenix
Contact PT 1.5 family:

| Connection | PCB terminal | Pitch | Quantity per universal PCB |
| --- | --- | ---: | ---: |
| CAP1188 CS1...CS8 twisted pairs | `PT 1,5/2-3,5-H` | 3.5 mm | 8 |
| D-M9N / D-M9P three-wire sensors | `PT 1,5/3-3,5-H` | 3.5 mm | 6 |
| Dedicated logic 12 V input | `PT 1,5/2-3,5-H` | 3.5 mm | 1 |
| CAN trunk input, CANH/CANL/GND/SHIELD | `PT 1,5/4-3,5-H` | 3.5 mm | 1 |

These are fixed push-in terminals, so no mating plug is required. Lower-cost
`KF350-2P` and `KF350-3P` parts may have the same 3.5 mm electrical pitch, but
their body and wire-entry geometry must be compared with the 1:1 PCB print
before substitution.

The motor and fused channel-power terminals remain 5.08 mm pitch and require a
separate >=10 A/contact selection. Do not substitute the 3.5 mm sensor terminals
into a motor-current position.

## MP1584 module

The carrier footprint is marked `MP1584_Fixed5V_Module_22.3x17mm`. It has four
oversized solder pads for `IN+`, `IN-`, `OUT+`, and `OUT-`. Check the purchased
module against the 1:1 print before fabrication because low-cost boards sold
under the same MP1584 name do not guarantee identical pad centres.
