#pragma once

#include <Arduino.h>
#include <WindowBusProtocol.h>

class LocalLink {
 public:
  explicit LocalLink(HardwareSerial &serial) : serial_(serial) {}

  void begin(uint32_t baud) {
    serial_.begin(baud);
    reset();
  }

  bool send(windowbus::UartType type, uint8_t sequence, const void *payload, uint8_t length) {
    if (length > windowbus::UART_MAX_PAYLOAD) return false;
    uint8_t header[4] = {
      windowbus::UART_SOF,
      static_cast<uint8_t>(type),
      length,
      sequence,
    };
    uint16_t crc = windowbus::crc16(header + 1, 3);
    if (payload != nullptr && length != 0) {
      crc = updateCrc(crc, static_cast<const uint8_t *>(payload), length);
    }

    serial_.write(header, sizeof(header));
    if (payload != nullptr && length != 0) {
      serial_.write(static_cast<const uint8_t *>(payload), length);
    }
    serial_.write(static_cast<uint8_t>(crc >> 8));
    serial_.write(static_cast<uint8_t>(crc));
    return true;
  }

  bool poll(windowbus::UartType &type, uint8_t &sequence, uint8_t *payload, uint8_t &length) {
    while (serial_.available()) {
      const uint8_t value = static_cast<uint8_t>(serial_.read());
      switch (state_) {
        case State::WaitSof:
          if (value == windowbus::UART_SOF) state_ = State::Type;
          break;
        case State::Type:
          type_ = value;
          state_ = State::Length;
          break;
        case State::Length:
          length_ = value;
          if (length_ > windowbus::UART_MAX_PAYLOAD) reset();
          else state_ = State::Sequence;
          break;
        case State::Sequence:
          sequence_ = value;
          index_ = 0;
          state_ = length_ == 0 ? State::CrcHigh : State::Payload;
          break;
        case State::Payload:
          payload_[index_++] = value;
          if (index_ >= length_) state_ = State::CrcHigh;
          break;
        case State::CrcHigh:
          receivedCrc_ = static_cast<uint16_t>(value) << 8;
          state_ = State::CrcLow;
          break;
        case State::CrcLow: {
          receivedCrc_ |= value;
          uint8_t header[3] = {type_, length_, sequence_};
          uint16_t expected = windowbus::crc16(header, sizeof(header));
          expected = updateCrc(expected, payload_, length_);
          if (expected == receivedCrc_) {
            type = static_cast<windowbus::UartType>(type_);
            sequence = sequence_;
            length = length_;
            if (payload != nullptr && length_ != 0) memcpy(payload, payload_, length_);
            reset();
            return true;
          }
          reset();
          break;
        }
      }
    }
    return false;
  }

 private:
  enum class State : uint8_t { WaitSof, Type, Length, Sequence, Payload, CrcHigh, CrcLow };

  HardwareSerial &serial_;
  State state_ = State::WaitSof;
  uint8_t type_ = 0;
  uint8_t length_ = 0;
  uint8_t sequence_ = 0;
  uint8_t index_ = 0;
  uint8_t payload_[windowbus::UART_MAX_PAYLOAD] = {};
  uint16_t receivedCrc_ = 0;

  void reset() {
    state_ = State::WaitSof;
    type_ = 0;
    length_ = 0;
    sequence_ = 0;
    index_ = 0;
    receivedCrc_ = 0;
  }

  static uint16_t updateCrc(uint16_t crc, const uint8_t *data, uint8_t length) {
    for (uint8_t i = 0; i < length; ++i) {
      crc ^= static_cast<uint16_t>(data[i]) << 8;
      for (uint8_t bit = 0; bit < 8; ++bit) {
        crc = (crc & 0x8000u) ? static_cast<uint16_t>((crc << 1) ^ 0x1021u)
                              : static_cast<uint16_t>(crc << 1);
      }
    }
    return crc;
  }
};
