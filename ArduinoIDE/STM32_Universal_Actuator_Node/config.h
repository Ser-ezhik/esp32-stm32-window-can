#pragma once

#include <Arduino.h>

namespace hw {

constexpr char FW_VERSION[] = "0.1.0-alpha.3";
constexpr uint32_t FW_BUILD = 3;

constexpr uint8_t ACTUATOR_COUNT = 2;
constexpr uint8_t SLAVE_COUNT = 3;

// Slot identity is provided by the cabinet carrier, not by the replaceable module.
constexpr PinName SLOT_ID0 = PC_14;
constexpr PinName SLOT_ID1 = PC_15;

// VNH5019A-E current sense inputs.
constexpr PinName CURRENT_PINS[ACTUATOR_COUNT] = {PA_0, PA_1};

// Two hardware PWM outputs from TIM1.
constexpr PinName PWM_PINS[ACTUATOR_COUNT] = {PA_8, PA_9};
constexpr PinName INA_PINS[ACTUATOR_COUNT] = {PB_14, PB_3};
constexpr PinName INB_PINS[ACTUATOR_COUNT] = {PB_15, PB_4};
constexpr PinName DIAG_PINS[ACTUATOR_COUNT] = {PB_5, PB_12};

// Master-only peripherals.
constexpr PinName REED_PINS[3] = {PB_0, PB_1, PB_8};
constexpr PinName CAP_CS = PA_4;
constexpr PinName CAP_IRQ = PB_13;
constexpr PinName CAP_RESET = PB_9;
constexpr PinName CABINET_EEPROM_CS = PA_15;
// Open-drain output from a 12 V supervisor/comparator on the carrier, low = supply bad.
constexpr PinName POWER_GOOD = PC_13;

// CAN uses the default bxCAN mapping: PA11 RX, PA12 TX.
constexpr PinName CAN_RX = PA_11;
constexpr PinName CAN_TX = PA_12;

// Master has three direct point-to-point UART links. Every slave uses PB6/PB7 upstream.
constexpr PinName UART1_RX = PB_7;
constexpr PinName UART1_TX = PB_6;
constexpr PinName UART2_RX = PA_3;
constexpr PinName UART2_TX = PA_2;
constexpr PinName UART3_RX = PB_11;
constexpr PinName UART3_TX = PB_10;

constexpr uint32_t LOCAL_UART_BAUD = 250000;
constexpr uint32_t CAN_BITRATE = 500000;
constexpr uint32_t PWM_FREQUENCY_HZ = 20000;
constexpr uint16_t PWM_MAX = 1000;

constexpr uint32_t CONTROL_PERIOD_MS = 5;
constexpr uint32_t SENSOR_PERIOD_MS = 10;
constexpr uint32_t STATUS_PERIOD_MOVING_MS = 100;
constexpr uint32_t STATUS_PERIOD_IDLE_MS = 1000;
constexpr uint32_t HEARTBEAT_TIMEOUT_MS = 300;
constexpr uint32_t SLAVE_TIMEOUT_MS = 400;
constexpr uint32_t COMMAND_ARM_WINDOW_MS = 1000;
constexpr uint32_t DIRECTION_DEADTIME_MS = 30;
constexpr uint32_t OVERCURRENT_CONFIRM_MS = 60;
constexpr uint32_t NO_CURRENT_STARTUP_MS = 700;
constexpr uint32_t ENDSTOP_CONFIRM_MS = 250;
constexpr uint32_t DEFAULT_MAX_TRAVEL_MS = 45000;
constexpr uint32_t DEFAULT_MIN_TRAVEL_MS = 1500;
constexpr uint16_t DEFAULT_MAX_CURRENT_MA = 8000;
constexpr uint16_t DEFAULT_ZERO_CURRENT_MA = 100;
constexpr uint16_t DEFAULT_PWM_PERMILLE = 1000;
constexpr uint16_t MIN_CALIBRATION_PWM_PERMILLE = 600;
constexpr uint16_t LOW_SUPPLY_MV = 9500;

// Calibrate this value for the custom VNH5019A-E CS circuit and ADC divider.
constexpr uint32_t CURRENT_MA_PER_ADC_COUNT_NUM = 20;
constexpr uint32_t CURRENT_MA_PER_ADC_COUNT_DEN = 1;

}  // namespace hw
