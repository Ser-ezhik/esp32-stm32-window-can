#pragma once

#include <Arduino.h>

struct CanMessage {
  uint16_t id = 0;
  uint8_t length = 0;
  uint8_t data[8] = {};
};

class BxCan {
 public:
  bool begin(uint32_t bitrate) {
    if (bitrate == 0) return false;

    RCC->APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN;
    RCC->APB1ENR |= RCC_APB1ENR_CAN1EN;

    // Default CAN mapping: PA11 RX with pull-up, PA12 TX alternate push-pull 50 MHz.
    GPIOA->CRH &= ~((0xFu << 12) | (0xFu << 16));
    GPIOA->CRH |= (0x8u << 12) | (0xBu << 16);
    GPIOA->ODR |= 1u << 11;
    AFIO->MAPR &= ~AFIO_MAPR_CAN_REMAP;

    CAN1->MCR = CAN_MCR_INRQ | CAN_MCR_ABOM | CAN_MCR_TXFP;
    if (!waitFor(&CAN1->MSR, CAN_MSR_INAK, true, 20)) return false;

    constexpr uint32_t timeQuanta = 18;
    const uint32_t pclk = HAL_RCC_GetPCLK1Freq();
    const uint32_t prescaler = pclk / (bitrate * timeQuanta);
    if (prescaler == 0 || prescaler > 1024 || pclk != bitrate * timeQuanta * prescaler) return false;

    // SJW=1 tq, BS1=13 tq, BS2=4 tq, sample point 77.8%.
    CAN1->BTR = ((prescaler - 1u) & 0x3FFu) | (12u << 16) | (3u << 20);

    CAN1->FMR |= CAN_FMR_FINIT;
    CAN1->FA1R &= ~1u;
    CAN1->FM1R &= ~1u;
    CAN1->FS1R |= 1u;
    CAN1->FFA1R &= ~1u;
    CAN1->sFilterRegister[0].FR1 = 0;
    CAN1->sFilterRegister[0].FR2 = 0;
    CAN1->FA1R |= 1u;
    CAN1->FMR &= ~CAN_FMR_FINIT;

    CAN1->MCR &= ~CAN_MCR_INRQ;
    return waitFor(&CAN1->MSR, CAN_MSR_INAK, false, 20);
  }

  bool send(uint16_t id, const void *payload, uint8_t length) {
    if (id > 0x7FF || length > 8) return false;

    uint8_t mailbox = 0xFF;
    const uint32_t tsr = CAN1->TSR;
    if (tsr & CAN_TSR_TME0) mailbox = 0;
    else if (tsr & CAN_TSR_TME1) mailbox = 1;
    else if (tsr & CAN_TSR_TME2) mailbox = 2;
    if (mailbox == 0xFF) return false;

    uint8_t bytes[8] = {};
    if (payload != nullptr && length != 0) memcpy(bytes, payload, length);
    CAN1->sTxMailBox[mailbox].TDTR = length;
    CAN1->sTxMailBox[mailbox].TDLR = pack32(bytes);
    CAN1->sTxMailBox[mailbox].TDHR = pack32(bytes + 4);
    CAN1->sTxMailBox[mailbox].TIR = (static_cast<uint32_t>(id) << 21) | CAN_TI0R_TXRQ;
    return true;
  }

  bool receive(CanMessage &message) {
    if ((CAN1->RF0R & CAN_RF0R_FMP0) == 0) return false;

    const auto &mailbox = CAN1->sFIFOMailBox[0];
    const uint32_t rir = mailbox.RIR;
    if (rir & CAN_RI0R_IDE) {
      CAN1->RF0R |= CAN_RF0R_RFOM0;
      return false;
    }

    message.id = static_cast<uint16_t>((rir >> 21) & 0x7FFu);
    message.length = static_cast<uint8_t>(mailbox.RDTR & 0x0Fu);
    unpack32(mailbox.RDLR, message.data);
    unpack32(mailbox.RDHR, message.data + 4);
    CAN1->RF0R |= CAN_RF0R_RFOM0;
    return true;
  }

  bool busOff() const {
    return (CAN1->ESR & CAN_ESR_BOFF) != 0;
  }

 private:
  static bool waitFor(volatile uint32_t *reg, uint32_t mask, bool set, uint32_t timeoutMs) {
    const uint32_t started = millis();
    while (((*reg & mask) != 0) != set) {
      if (millis() - started >= timeoutMs) return false;
    }
    return true;
  }

  static uint32_t pack32(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
  }

  static void unpack32(uint32_t value, uint8_t *p) {
    p[0] = static_cast<uint8_t>(value);
    p[1] = static_cast<uint8_t>(value >> 8);
    p[2] = static_cast<uint8_t>(value >> 16);
    p[3] = static_cast<uint8_t>(value >> 24);
  }
};
