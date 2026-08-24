# ESP32 CAN Master v0.1.0-alpha.12

Target: ESP32-S3 N16R8, Arduino-ESP32 core 3.0.7, PSRAM disabled.

This release recognizes STM32 fault code 14 (`ConfigStorage`) and displays it
as `ошибка памяти настроек`. Unknown fault values are shown as an unknown error
instead of being reported as no fault.
