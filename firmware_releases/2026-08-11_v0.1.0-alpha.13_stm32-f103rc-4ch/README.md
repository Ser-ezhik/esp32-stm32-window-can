# STM32F103RCT6 integrated four-channel release

Version: `0.1.0-alpha.13-4ch-f103rc`

Build: `13`

Target: `UNIVERSAL-4CH-F103RC-IC`

FQBN: `STMicroelectronics:stm32:GenF1:pnum=GENERIC_F103RCTX,xserial=none,usb=none,opt=oslto,dbg=none,rtlib=nano`

This is a separate target from the replaceable two-channel STM32F103C8 module.
It controls four local VNH5019A-E channels and publishes two classic-CAN
actuator frames. It has no physical UART slave links.

Compiled size:

- Flash: 23,860 bytes of 262,144 bytes (9%).
- Static RAM: 3,524 bytes of 49,152 bytes (7%).

Checks completed before archiving:

- board DRC: 0 violations, 0 unconnected pads;
- complete pad/net and voltage-domain contract: PASS;
- all 12 high-current route audits at the 5 A design-check current: PASS;
- firmware-to-PCB pin contract: PASS;
- Arduino CLI build: PASS without warnings.

SHA-256:

- BIN: `7EA8EE3D4E9C5F47C622403C826FDCAFDD5F19F0E488F271283F9F851294BB22`
- HEX: `A87915F0AACCCEDA6D89DD2A92827B5749BFF7203E899065920B1E9CDA1B4F75`
