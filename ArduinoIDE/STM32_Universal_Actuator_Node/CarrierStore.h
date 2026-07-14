#pragma once

#include <Arduino.h>
#include <SPI.h>
#include <WindowBusProtocol.h>

#pragma pack(push, 1)
struct CarrierIdentity {
  uint32_t magic;
  uint8_t version;
  uint8_t cabinetId;
  uint8_t objectType;
  uint8_t slaveCount;
  uint16_t configRevision;
  uint16_t reserved;
  uint16_t crc;
};
#pragma pack(pop)

class CarrierStore {
 public:
  explicit CarrierStore(PinName chipSelect) : cs_(chipSelect) {}

  void begin() {
    pinMode(cs_, OUTPUT);
    digitalWrite(cs_, HIGH);
    SPI.begin();
  }

  bool load(CarrierIdentity &identity) {
    readBytes(0, reinterpret_cast<uint8_t *>(&identity), sizeof(identity));
    if (identity.magic != MAGIC || identity.version != VERSION) return false;
    if (!windowbus::validCabinetId(identity.cabinetId) || identity.slaveCount > 3) return false;
    const uint16_t stored = identity.crc;
    identity.crc = 0;
    const uint16_t expected = windowbus::crc16(reinterpret_cast<const uint8_t *>(&identity), sizeof(identity));
    identity.crc = stored;
    return stored == expected;
  }

  bool save(CarrierIdentity identity) {
    if (!windowbus::validCabinetId(identity.cabinetId) || identity.slaveCount > 3) return false;
    identity.magic = MAGIC;
    identity.version = VERSION;
    identity.crc = 0;
    identity.crc = windowbus::crc16(reinterpret_cast<const uint8_t *>(&identity), sizeof(identity));

    writeEnable();
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
    digitalWrite(cs_, LOW);
    SPI.transfer(0x02);
    SPI.transfer(0x00);
    SPI.transfer(0x00);
    const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&identity);
    for (size_t i = 0; i < sizeof(identity); ++i) SPI.transfer(bytes[i]);
    digitalWrite(cs_, HIGH);
    SPI.endTransaction();

    const uint32_t started = millis();
    while (readStatus() & 0x01) {
      if (millis() - started > 20) return false;
    }
    CarrierIdentity verify = {};
    return load(verify) && memcmp(&identity, &verify, sizeof(identity)) == 0;
  }

 private:
  static constexpr uint32_t MAGIC = 0x314E4957u;  // WIN1
  static constexpr uint8_t VERSION = 1;
  PinName cs_;

  void readBytes(uint16_t address, uint8_t *data, size_t length) {
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
    digitalWrite(cs_, LOW);
    SPI.transfer(0x03);
    SPI.transfer(static_cast<uint8_t>(address >> 8));
    SPI.transfer(static_cast<uint8_t>(address));
    for (size_t i = 0; i < length; ++i) data[i] = SPI.transfer(0xFF);
    digitalWrite(cs_, HIGH);
    SPI.endTransaction();
  }

  void writeEnable() {
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
    digitalWrite(cs_, LOW);
    SPI.transfer(0x06);
    digitalWrite(cs_, HIGH);
    SPI.endTransaction();
  }

  uint8_t readStatus() {
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
    digitalWrite(cs_, LOW);
    SPI.transfer(0x05);
    const uint8_t value = SPI.transfer(0xFF);
    digitalWrite(cs_, HIGH);
    SPI.endTransaction();
    return value;
  }
};
