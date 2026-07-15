"""Generate default 25LC256 carrier EEPROM images for the DOOR-8CH project."""

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "firmware_releases" / "carrier_eeprom" / "default_project"

MAGIC = 0x314E4957  # WIN1
VERSION = 1
IMAGE_SIZE = 32768

OBJECT_WINDOW = 0
OBJECT_SINGLE_DOOR = 1
OBJECT_DOUBLE_DOOR = 2


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def carrier_record(cabinet_id: int, object_type: int, slave_count: int, reed_mask: int) -> bytes:
    if not 0 <= cabinet_id <= 63:
        raise ValueError("cabinet_id must be 0..63")
    if not 0 <= reed_mask <= 0x3F:
        raise ValueError("reed_mask must be 0..63")
    header_without_crc = struct.pack(
        "<IBBBBHH",
        MAGIC,
        VERSION,
        cabinet_id,
        object_type,
        slave_count,
        1,
        reed_mask,
    )
    header_with_zero_crc = header_without_crc + b"\x00\x00"
    return header_without_crc + struct.pack("<H", crc16(header_with_zero_crc))


def write_image(filename: str, cabinet_id: int, object_type: int, slave_count: int, reed_mask: int = 0) -> str:
    image = bytearray([0xFF] * IMAGE_SIZE)
    record = carrier_record(cabinet_id, object_type, slave_count, reed_mask)
    image[: len(record)] = record
    path = OUT / filename
    path.write_bytes(image)
    return f"{filename}: {record.hex(' ').upper()}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        write_image("cabinet_01_double_door.bin", 1, OBJECT_DOUBLE_DOOR, 3),
        write_image("cabinet_02_single_door_1.bin", 2, OBJECT_SINGLE_DOOR, 1),
        write_image("cabinet_03_single_door_2.bin", 3, OBJECT_SINGLE_DOOR, 1),
        write_image("cabinet_04_single_door_3.bin", 4, OBJECT_SINGLE_DOOR, 1),
        write_image("cabinet_05_window.bin", 5, OBJECT_WINDOW, 0),
    ]
    (OUT / "README.txt").write_text(
        "Default 25LC256 images for DOOR-8CH carrier EEPROM.\n"
        "First 14 bytes are the CarrierIdentity record; the rest is 0xFF.\n\n"
        + "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
