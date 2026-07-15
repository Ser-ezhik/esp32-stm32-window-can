#pragma once

#include <stdint.h>
#include <string.h>

namespace windowbus {

constexpr uint8_t PROTOCOL_VERSION = 1;
constexpr uint8_t MAX_CABINETS = 64;
constexpr uint8_t MAX_ACTUATORS_PER_BOARD = 2;
constexpr uint8_t MAX_SLAVES_PER_CABINET = 3;
constexpr uint8_t MAX_ACTUATORS_PER_CABINET = 8;

constexpr uint16_t CAN_COMMAND_BASE = 0x100;
constexpr uint16_t CAN_STATUS_BASE = 0x180;
constexpr uint16_t CAN_SENSORS_BASE = 0x200;
constexpr uint16_t CAN_ACTUATORS_BASE = 0x280;
constexpr uint16_t CAN_EVENT_BASE = 0x380;
constexpr uint16_t CAN_CONFIG_BASE = 0x3C0;
constexpr uint16_t CAN_DISCOVERY_REQUEST = 0x700;
constexpr uint16_t CAN_DISCOVERY_RESPONSE_BASE = 0x740;
constexpr uint16_t CAN_PROVISION_REQUEST = 0x7C0;

constexpr uint8_t UART_SOF = 0xA5;
constexpr uint8_t UART_MAX_PAYLOAD = 32;

enum class BoardRole : uint8_t {
  Master = 0,
  Slave1 = 1,
  Slave2 = 2,
  Slave3 = 3,
};

enum class ObjectType : uint8_t {
  Window = 0,
  SingleDoor = 1,
  DoubleDoor = 2,
};

enum class Command : uint8_t {
  None = 0,
  Open = 1,
  Close = 2,
  Vent = 3,
  Stop = 4,
  Arm = 5,
  ClearFault = 6,
  CalibrateOpen = 7,
  CalibrateClose = 8,
  CalibrateFull = 9,
  ServiceExtend = 10,
  ServiceRetract = 11,
  ResetCalibration = 12,
  ConfigureCap1188 = 13,
};

enum class RunState : uint8_t {
  Boot = 0,
  Safe = 1,
  Idle = 2,
  Moving = 3,
  Calibrating = 4,
  Fault = 5,
  Recovering = 6,
};

enum class Position : uint8_t {
  Unknown = 0,
  Open = 1,
  Closed = 2,
  Intermediate = 3,
  Vent = 4,
};

enum class Fault : uint8_t {
  None = 0,
  NotConfigured = 1,
  CommunicationTimeout = 2,
  OverCurrent = 3,
  NoCurrent = 4,
  MovementTimeout = 5,
  DriverDiagnostic = 6,
  SafetyEdge = 7,
  SensorConflict = 8,
  LowSupply = 9,
  SlaveOffline = 10,
  CalibrationFailed = 11,
  PowerRecovered = 12,
  Cap1188Offline = 13,
};

enum class UartType : uint8_t {
  Hello = 1,
  Command = 2,
  Status = 3,
  Config = 4,
  ConfigAck = 5,
  Stop = 6,
};

enum CommandFlags : uint8_t {
  COMMAND_FLAG_ARMED = 1u << 0,
  COMMAND_FLAG_SERVICE = 1u << 1,
  COMMAND_FLAG_AUTO_ADAPT = 1u << 2,
};

enum ActuatorFlags : uint8_t {
  ACTUATOR_MOVING = 1u << 0,
  ACTUATOR_EXTEND = 1u << 1,
  ACTUATOR_DIAG_OK = 1u << 2,
  ACTUATOR_ENDSTOP = 1u << 3,
  ACTUATOR_OVERCURRENT = 1u << 4,
  ACTUATOR_NO_CURRENT = 1u << 5,
  ACTUATOR_CALIBRATED = 1u << 6,
};

#pragma pack(push, 1)

struct CanCommandFrame {
  uint8_t version;
  uint8_t sequence;
  uint8_t command;
  uint8_t flags;
  uint16_t argument;
  uint16_t configRevision;
};

struct CanStatusFrame {
  uint8_t version;
  uint8_t bootId;
  uint8_t state;
  uint8_t target;
  uint8_t position;
  uint8_t fault;
  uint8_t faultActuator;
  uint8_t slaveMask;
};

struct CanSensorFrame {
  uint8_t version;
  uint8_t reedMask;
  uint8_t capMask;
  uint8_t flags;
  uint16_t supplyMv;
  uint16_t uptimeSeconds;
};

struct CanActuatorFrame {
  uint16_t currentMa[2];
  uint8_t pwm[2];
  uint8_t flags[2];
};

struct CanEventFrame {
  uint8_t version;
  uint8_t sequence;
  uint8_t event;
  uint8_t actuator;
  uint32_t detail;
};

struct CanDiscoveryFrame {
  uint32_t uidHash;
  uint8_t configured;
  uint8_t cabinetId;
  uint8_t role;
  uint8_t firmwareBuild;
};

struct CanProvisionFrame {
  uint32_t uidHash;
  uint8_t cabinetId;
  uint8_t objectType;
  uint8_t slaveCount;
  uint8_t flags;
};

struct LocalCommandPayload {
  uint8_t command;
  uint8_t flags;
  uint16_t argument;
  uint16_t configRevision;
};

struct LocalStatusPayload {
  uint8_t slot;
  uint8_t state;
  uint8_t target;
  uint8_t fault;
  uint8_t faultActuator;
  uint8_t bootId;
  uint16_t currentMa[2];
  uint8_t pwm[2];
  uint8_t actuatorFlags[2];
  uint16_t lastTravelMs[2];
};

struct LocalConfigPayload {
  uint16_t revision;
  uint16_t maxCurrentMa[2];
  uint16_t zeroCurrentMa[2];
  uint16_t pwmOpenPermille[2];
  uint16_t pwmClosePermille[2];
  uint16_t minTravelMs;
  uint16_t endstopConfirmMs;
  uint32_t maxTravelMs;
};

#pragma pack(pop)

static_assert(sizeof(CanCommandFrame) == 8, "CAN command must fit one classic CAN frame");
static_assert(sizeof(CanStatusFrame) == 8, "CAN status must fit one classic CAN frame");
static_assert(sizeof(CanSensorFrame) == 8, "CAN sensor frame must fit one classic CAN frame");
static_assert(sizeof(CanActuatorFrame) == 8, "CAN actuator frame must fit one classic CAN frame");
static_assert(sizeof(CanEventFrame) == 8, "CAN event frame must fit one classic CAN frame");
static_assert(sizeof(CanDiscoveryFrame) == 8, "CAN discovery frame must fit one classic CAN frame");
static_assert(sizeof(CanProvisionFrame) == 8, "CAN provision frame must fit one classic CAN frame");

inline uint16_t crc16(const uint8_t *data, size_t length) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < length; ++i) {
    crc ^= static_cast<uint16_t>(data[i]) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x8000u) ? static_cast<uint16_t>((crc << 1) ^ 0x1021u)
                            : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

template <typename T>
inline void clear(T &value) {
  memset(&value, 0, sizeof(value));
}

inline bool validCabinetId(uint8_t id) {
  return id < MAX_CABINETS;
}

}  // namespace windowbus
