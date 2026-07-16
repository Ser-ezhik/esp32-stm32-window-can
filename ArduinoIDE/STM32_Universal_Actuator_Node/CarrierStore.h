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

struct PowerLossRecord {
  uint32_t magic;
  uint32_t uptimeMs;
  uint16_t crc;
  uint8_t version;
  uint8_t pending;
  uint8_t sequence;
  uint8_t runState;
  uint8_t command;
  uint8_t fault;
  uint8_t actuator;
  uint8_t reserved;
};
#pragma pack(pop)

static_assert(sizeof(CarrierIdentity) == 14, "Carrier identity EEPROM layout changed");
static_assert(sizeof(PowerLossRecord) == 18, "Power-loss EEPROM layout changed");

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

    if (!writeBytes(IDENTITY_ADDRESS, reinterpret_cast<const uint8_t *>(&identity), sizeof(identity))) return false;
    CarrierIdentity verify = {};
    return load(verify) && memcmp(&identity, &verify, sizeof(identity)) == 0;
  }

  bool loadPowerLoss(PowerLossRecord &record) {
    readBytes(POWER_LOSS_ADDRESS, reinterpret_cast<uint8_t *>(&record), sizeof(record));
    if (record.magic != POWER_LOSS_MAGIC || record.version != POWER_LOSS_VERSION) return false;
    const uint16_t stored = record.crc;
    record.crc = 0;
    const uint16_t expected = windowbus::crc16(reinterpret_cast<const uint8_t *>(&record), sizeof(record));
    record.crc = stored;
    return stored == expected;
  }

  bool savePowerLoss(PowerLossRecord &record) {
    record.magic = POWER_LOSS_MAGIC;
    record.version = POWER_LOSS_VERSION;
    record.pending = 1;
    record.crc = 0;
    record.crc = windowbus::crc16(reinterpret_cast<const uint8_t *>(&record), sizeof(record));
    return writeBytes(POWER_LOSS_ADDRESS, reinterpret_cast<const uint8_t *>(&record), sizeof(record));
  }

  bool acknowledgePowerLoss(PowerLossRecord record) {
    record.pending = 0;
    record.crc = 0;
    record.crc = windowbus::crc16(reinterpret_cast<const uint8_t *>(&record), sizeof(record));
    return writeBytes(POWER_LOSS_ADDRESS, reinterpret_cast<const uint8_t *>(&record), sizeof(record));
  }

 private:
  static constexpr uint32_t MAGIC = 0x314E4957u;  // WIN1
  static constexpr uint8_t VERSION = 1;
  static constexpr uint16_t IDENTITY_ADDRESS = 0x0000;
  static constexpr uint16_t POWER_LOSS_ADDRESS = 0x0040;
  static constexpr uint32_t POWER_LOSS_MAGIC = 0x31525750u;  // PWR1
  static constexpr uint8_t POWER_LOSS_VERSION = 1;
  static constexpr uint8_t PAGE_SIZE = 64;
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

  bool writeBytes(uint16_t address, const uint8_t *data, size_t length) {
    while (length != 0) {
      const size_t pageRoom = PAGE_SIZE - (address % PAGE_SIZE);
      const size_t chunk = min(length, pageRoom);
      writeEnable();
      SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
      digitalWrite(cs_, LOW);
      SPI.transfer(0x02);
      SPI.transfer(static_cast<uint8_t>(address >> 8));
      SPI.transfer(static_cast<uint8_t>(address));
      for (size_t i = 0; i < chunk; ++i) SPI.transfer(data[i]);
      digitalWrite(cs_, HIGH);
      SPI.endTransaction();
      if (!waitReady()) return false;
      address += chunk;
      data += chunk;
      length -= chunk;
    }
    return true;
  }

  bool waitReady() {
    const uint32_t started = millis();
    while (readStatus() & 0x01) {
      if (millis() - started > 20) return false;
    }
    return true;
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
