# ESP32 v1.8-rp2040-web-ota

Версия добавляет отдельную страницу обновления прошивок:

```text
/firmware
```

## Что есть на странице

- Обновление ESP32 защищенным файлом `.wota`.
- Ручной rollback ESP32 на предыдущий OTA-раздел.
- Обновление выбранной RP2040:
  - локальная RP2040 1 по UART;
  - локальная RP2040 2 по UART;
  - включенные RP2040 по RS-485.

## Важное по RP2040

Для RP2040 загружается не `.uf2`, а OTA app `.bin`, собранный под адрес `0x10040000`.

Подходящий файл из текущих релизов:

```text
firmware_releases/2026-07-08_v1.6_rp2040-ota-source-full-uf2/RP2040_RS485_Window_Node_4A_ota_v1.6.bin
```

Перед записью ESP32 проверяет, что файл похож на app-slot прошивку RP2040: stack pointer в RAM, reset vector в области `0x10040000..0x100BFFFF`.

## Файлы ESP32

- `ESP32_CC1101_RS485_Master_v1.8.wota` - для следующих web-обновлений ESP32.
- `ESP32_CC1101_RS485_Master_v1.8.bin` - OTA payload/первый переход со старой версии.
- `ESP32_CC1101_RS485_Master_v1.8.merged.bin` - полная USB/Serial прошивка.
