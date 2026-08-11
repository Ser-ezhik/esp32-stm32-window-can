#pragma once

#include <Arduino.h>

namespace hw {

constexpr char FW_VERSION[] = "0.1.0-alpha.13-4ch-f103rc";
constexpr uint32_t FW_BUILD = 13;

constexpr uint8_t ACTUATOR_COUNT = 4;
constexpr uint8_t PHYSICAL_SLAVE_COUNT = 0;
constexpr uint8_t REQUIRED_LOGICAL_SLAVE_COUNT = 1;
constexpr uint8_t LOGICAL_SLAVE_MASK = 0x01;

constexpr PinName CURRENT_PINS[ACTUATOR_COUNT] = {PA_0, PA_1, PA_2, PA_3};
constexpr PinName PWM_PINS[ACTUATOR_COUNT] = {PA_8, PA_9, PA_10, PA_11};
constexpr PinName INA_PINS[ACTUATOR_COUNT] = {PB_0, PB_10, PB_12, PB_14};
constexpr PinName INB_PINS[ACTUATOR_COUNT] = {PB_1, PB_11, PB_13, PB_15};
constexpr PinName DIAG_PINS[ACTUATOR_COUNT] = {PC_6, PC_7, PC_8, PC_9};

constexpr PinName REED_PINS[3] = {PC_0, PC_1, PC_2};
constexpr PinName CAP_CS = PA_4;
constexpr PinName CAP_IRQ = PC_5;
constexpr PinName CAP_RESET = PC_10;
constexpr PinName CABINET_EEPROM_CS = PC_4;
constexpr PinName POWER_GOOD = PC_3;

// bxCAN is remapped from PA11/PA12 to PB8/PB9. PA11 remains TIM1_CH4.
constexpr PinName CAN_RX = PB_8;
constexpr PinName CAN_TX = PB_9;

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
constexpr uint16_t DEFAULT_MAX_CURRENT_MA = 5000;
constexpr uint16_t DEFAULT_ZERO_CURRENT_MA = 100;
constexpr uint16_t DEFAULT_PWM_PERMILLE = 1000;
constexpr uint16_t MIN_CALIBRATION_PWM_PERMILLE = 600;
constexpr uint16_t LOW_SUPPLY_MV = 9500;

// Starting value for K0=7110, 1 kohm CS load and a 3.3 V/12-bit ADC.
// The 10 kohm ADC resistor is series protection, not a voltage divider.
constexpr uint32_t CURRENT_MA_PER_ADC_COUNT_NUM = 57;
constexpr uint32_t CURRENT_MA_PER_ADC_COUNT_DEN = 10;

}  // namespace hw
