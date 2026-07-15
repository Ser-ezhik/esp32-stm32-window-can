# ACT-CARRIER-2CH v0.1 mechanical requirements

## Required size before layout

The target outline is provisionally **160 x 100 mm maximum**. This is a design
envelope, not a final PCB size. It provides two separated 45 x 55 mm thermal
zones for VNH5019A-E, a central STM32 socket zone and a connector edge.

The final outline is set only after the exact terminal blocks and the STM32 mini
module are measured. Do not order a PCB from this provisional envelope.

## Intended top-side arrangement

```text
  actuator 1 terminal       actuator 2 terminal
          |                         |
      [ VNH U1 ]               [ VNH U2 ]
      [ 470uF ]                [ 470uF ]

  power input  --  STM32 mini socket  --  MASTER / sensor headers
                      SWD nearby
```

The motor terminals and VNH packages are kept on one long board edge so their
high-current copper stays out of the sensor and CAN connector region.

## Copper and assembly constraints

- Four layer board, 1.6 mm FR-4, 2 oz copper on top and bottom.
- ENIG finish is preferred for MultiPowerSO-30 assembly and exposed-pad quality.
- VNH5019A-E requires stencil and reflow or professional hot-air assembly; it
  is not a reliable hand-solder-only package.
- Use M3 mounting holes in four corners plus at least two holes near the VNH
  thermal zones if the enclosure allows it.
- Keep a 5 mm component-free keepout around screw terminals for ferrules and a
  screwdriver.
- The board needs airflow or contact with a metal cabinet backplate only after
  a thermal test demonstrates the need; do not electrically bond any VNH slug
  to the enclosure.
