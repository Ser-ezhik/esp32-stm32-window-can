# Terminal block selection

## Actuator outputs J2 and J3

Use a two-position, through-hole, vertical screw terminal with **5.08 mm pitch**.

**Primary part:** `Phoenix Contact MKDS 1,5/ 2-5,08`, order number `1715721`.
It is rated for 17.5 A, accepts a nominal 1.5 mm2 conductor and uses a screw
connection. This is comfortably above the 5 A actuator design current. [Phoenix
Contact data](https://www.phoenixcontact.com/en-gb/products/printed-circuit-board-terminal-mkds-15-2-508-1715721?type=pdf)

**Search terms for an available compatible substitute:**

```text
KF2EDG 5.08-2P straight screw terminal 15A 1.5mm2
DG301-5.08-02P vertical PCB screw terminal 15A
```

Only use an alternative if all of these match:

- 5.08 mm pin pitch;
- two positions, through-hole, vertical/straight cable entry;
- at least 10 A continuous rating per contact;
- accepts at least 1.0 mm2 stranded actuator wire;
- actual pin diameter and body outline checked against the carrier footprint
  before ordering PCB fabrication.

Use ferrules on stranded wires. Do not use 3.5 mm-pitch signal terminals,
spring terminals intended for Dupont wire, or pluggable header/socket pairs in
the actuator-current path.

## Carrier power input J1

Use the same 5.08 mm family in a four-position body: `MKDS 1,5/ 4-5,08` or a
dimensionally compatible `KF2EDG 5.08-4P` straight screw terminal. Pin order is
`FUSED_12V_CH1`, `GND`, `FUSED_12V_CH2`, `GND`. The two positive pins remain
separate all the way to U1 and U2 so the two 7.5 A fuses remain independent.

## Other low-current connectors

Use locking JST-XH or 3.81/5.08 mm screw terminals for logic, UART, sensors and
CAN. They are deliberately separate from motor terminals and are never rated as
actuator connectors.
