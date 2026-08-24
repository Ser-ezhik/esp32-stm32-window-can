#pragma once

#include <Arduino.h>
#include <SPI.h>

class Cap1188Spi {
 public:
  Cap1188Spi(PinName chipSelect, PinName resetPin)
      : cs_(chipSelect), reset_(resetPin) {}

  bool begin(uint8_t enabledMask) {
    pinMode(cs_, OUTPUT);
    digitalWrite(cs_, HIGH);
    pinMode(reset_, OUTPUT);
    digitalWrite(reset_, HIGH);
    delay(2);
    digitalWrite(reset_, LOW);
    delay(20);
    SPI.begin();

    resetInterface();
    const uint8_t productId = readRegister(0xFD);
    online_ = productId == 0x50;
    if (!online_) return false;

    setEnabledMask(enabledMask);
    return true;
  }

  bool online() const { return online_; }

  uint8_t touched() {
    if (!online_) return 0;
    const uint8_t value = readRegister(0x03);
    clearInterrupt();
    return value;
  }

  uint8_t noiseFlags() {
    return online_ ? readRegister(0x0A) : 0;
  }

  void setEnabledMask(uint8_t mask) {
    if (!online_) return;
    writeRegister(0x21, mask);  // Sensor Input Enable.
    writeRegister(0x27, mask);  // Interrupt Enable.
    if (mask != 0) writeRegister(0x26, mask);  // Recalibrate enabled inputs.
    clearInterrupt();
  }

  void clearInterrupt() {
    const uint8_t mainControl = readRegister(0x00);
    writeRegister(0x00, mainControl & static_cast<uint8_t>(~0x01u));
  }

  uint8_t readRegister(uint8_t address) {
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
    digitalWrite(cs_, LOW);
    SPI.transfer(0x7D);
    SPI.transfer(address);
    SPI.transfer(0x7F);  // First byte after a new command is invalid.
    const uint8_t value = SPI.transfer(0x7F);
    digitalWrite(cs_, HIGH);
    SPI.endTransaction();
    return value;
  }

  void writeRegister(uint8_t address, uint8_t value) {
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
    digitalWrite(cs_, LOW);
    SPI.transfer(0x7D);
    SPI.transfer(address);
    SPI.transfer(0x7E);
    SPI.transfer(value);
    digitalWrite(cs_, HIGH);
    SPI.endTransaction();
  }

 private:
  PinName cs_;
  PinName reset_;
  bool online_ = false;

  void resetInterface() {
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
    digitalWrite(cs_, LOW);
    SPI.transfer(0x7A);
    SPI.transfer(0x7A);
    digitalWrite(cs_, HIGH);
    SPI.endTransaction();
  }
};
