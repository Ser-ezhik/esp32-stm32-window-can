#include <Arduino.h>
#include <EEPROM.h>
#include <IWatchdog.h>
#include <SPI.h>
#include <WindowBusProtocol.h>

#include "BxCan.h"
#include "Cap1188Spi.h"
#include "CarrierStore.h"
#include "LocalLink.h"
#include "config.h"

using namespace windowbus;

namespace {

constexpr uint32_t CONFIG_MAGIC = 0x31474643u;  // CFG1
constexpr uint8_t CONFIG_VERSION = 2;

enum class Direction : uint8_t { None, Extend, Retract };

#pragma pack(push, 1)
struct NodeConfig {
  uint32_t magic;
  uint8_t version;
  uint8_t autoAdapt;
  uint8_t capEnabledMask;
  uint16_t revision;
  uint16_t maxCurrentMa[2];
  uint16_t zeroCurrentMa[2];
  uint16_t pwmOpenPermille[2];
  uint16_t pwmClosePermille[2];
  uint16_t lastOpenMs[2];
  uint16_t lastCloseMs[2];
  uint16_t minTravelMs;
  uint16_t endstopConfirmMs;
  uint32_t maxTravelMs;
  uint16_t crc;
};
#pragma pack(pop)

struct ActuatorRuntime {
  Direction direction = Direction::None;
  uint16_t currentMa = 0;
  uint16_t filteredCurrentMa = 0;
  uint16_t pwmPermille = 0;
  uint8_t flags = ACTUATOR_DIAG_OK;
  uint32_t startedAt = 0;
  uint32_t overCurrentSince = 0;
  uint32_t zeroCurrentSince = 0;
  uint32_t earlyZeroSince = 0;
  bool moving = false;
  bool finished = false;
};

HardwareSerial uartPort1(hw::UART1_RX, hw::UART1_TX);
HardwareSerial uartPort2(hw::UART2_RX, hw::UART2_TX);
HardwareSerial uartPort3(hw::UART3_RX, hw::UART3_TX);
LocalLink localLinks[3] = {LocalLink(uartPort1), LocalLink(uartPort2), LocalLink(uartPort3)};

BxCan canBus;
Cap1188Spi cap1188(hw::CAP_CS, hw::CAP_RESET);
CarrierStore carrierStore(hw::CABINET_EEPROM_CS);

BoardRole boardRole = BoardRole::Master;
CarrierIdentity carrier = {};
NodeConfig config = {};
ActuatorRuntime actuators[2];
LocalStatusPayload slaveStatus[3] = {};
LocalConfigPayload slaveConfigs[3] = {};
uint32_t slaveLastSeen[3] = {};
uint8_t slaveTxSequence[3] = {};

RunState runState = RunState::Boot;
Position position = Position::Unknown;
Fault fault = Fault::NotConfigured;
Command activeCommand = Command::None;
Command lastMovementCommand = Command::None;
uint8_t faultActuator = 0;
uint8_t bootId = 0;
uint8_t lastCommandSequence = 0xFF;
uint8_t reedMask = 0;
uint8_t capMask = 0;
uint32_t uidHash = 0;
uint32_t lastCommandAt = 0;
uint32_t armedUntil = 0;
uint32_t lastControlAt = 0;
uint32_t lastSensorAt = 0;
uint32_t lastStatusAt = 0;
uint32_t lastDiscoveryAt = 0;
bool carrierConfigured = false;
bool canOnline = false;
bool capOnline = false;
bool calibrationPendingApply = false;
PowerLossRecord powerLossRecord = {};
bool powerLossEventPending = false;
bool powerLossHandled = false;
uint32_t lastPowerEventAttempt = 0;

uint16_t configCrc(NodeConfig value) {
  value.crc = 0;
  return crc16(reinterpret_cast<const uint8_t *>(&value), sizeof(value));
}

void setDefaultConfig() {
  memset(&config, 0, sizeof(config));
  config.magic = CONFIG_MAGIC;
  config.version = CONFIG_VERSION;
  config.revision = 1;
  config.autoAdapt = 1;
  config.capEnabledMask = 0x07;
  for (uint8_t i = 0; i < 2; ++i) {
    config.maxCurrentMa[i] = hw::DEFAULT_MAX_CURRENT_MA;
    config.zeroCurrentMa[i] = hw::DEFAULT_ZERO_CURRENT_MA;
    config.pwmOpenPermille[i] = hw::DEFAULT_PWM_PERMILLE;
    config.pwmClosePermille[i] = hw::DEFAULT_PWM_PERMILLE;
  }
  config.minTravelMs = hw::DEFAULT_MIN_TRAVEL_MS;
  config.endstopConfirmMs = hw::ENDSTOP_CONFIRM_MS;
  config.maxTravelMs = hw::DEFAULT_MAX_TRAVEL_MS;
  config.crc = configCrc(config);
}

bool loadConfig() {
  EEPROM.get(0, config);
  if (config.magic != CONFIG_MAGIC || config.version != CONFIG_VERSION || config.crc != configCrc(config)) {
    setDefaultConfig();
    return false;
  }
  return true;
}

void saveConfig() {
  config.magic = CONFIG_MAGIC;
  config.version = CONFIG_VERSION;
  config.crc = configCrc(config);
  EEPROM.put(0, config);
}

uint32_t readUidHash() {
  const volatile uint32_t *uid = reinterpret_cast<const volatile uint32_t *>(UID_BASE);
  uint32_t hash = 2166136261u;
  for (uint8_t word = 0; word < 3; ++word) {
    uint32_t value = uid[word];
    for (uint8_t byte = 0; byte < 4; ++byte) {
      hash ^= static_cast<uint8_t>(value);
      hash *= 16777619u;
      value >>= 8;
    }
  }
  return hash;
}

BoardRole readBoardRole() {
  pinMode(hw::SLOT_ID0, INPUT_PULLUP);
  pinMode(hw::SLOT_ID1, INPUT_PULLUP);
  delay(2);
  const uint8_t value = (digitalRead(hw::SLOT_ID0) == LOW ? 1u : 0u) |
                        (digitalRead(hw::SLOT_ID1) == LOW ? 2u : 0u);
  return static_cast<BoardRole>(value);
}

uint8_t roleIndex() {
  return static_cast<uint8_t>(boardRole);
}

bool isMaster() {
  return boardRole == BoardRole::Master;
}

Direction commandDirection(Command command) {
  switch (command) {
    case Command::Open:
    case Command::CalibrateOpen:
      return Direction::Extend;
    case Command::Close:
    case Command::CalibrateClose:
      return Direction::Retract;
    default:
      return Direction::None;
  }
}

uint16_t commandPwm(uint8_t actuator, Command command) {
  if (command == Command::CalibrateOpen || command == Command::CalibrateClose) return hw::PWM_MAX;
  return commandDirection(command) == Direction::Extend
             ? config.pwmOpenPermille[actuator]
             : config.pwmClosePermille[actuator];
}

void writePwm(uint8_t index, uint16_t permille) {
  permille = min<uint16_t>(permille, hw::PWM_MAX);
  const uint32_t duty = (static_cast<uint32_t>(permille) * 1023u) / hw::PWM_MAX;
  analogWrite(hw::PWM_PINS[index], duty);
  actuators[index].pwmPermille = permille;
}

void stopActuator(uint8_t index) {
  writePwm(index, 0);
  digitalWrite(hw::INA_PINS[index], LOW);
  digitalWrite(hw::INB_PINS[index], LOW);
  actuators[index].moving = false;
  actuators[index].direction = Direction::None;
  actuators[index].flags &= static_cast<uint8_t>(~(ACTUATOR_MOVING | ACTUATOR_EXTEND));
}

void stopLocal() {
  for (uint8_t i = 0; i < 2; ++i) stopActuator(i);
}

void refreshCalibrationFlags() {
  for (uint8_t i = 0; i < 2; ++i) {
    if (config.lastOpenMs[i] != 0 && config.lastCloseMs[i] != 0) {
      actuators[i].flags |= ACTUATOR_CALIBRATED;
    } else {
      actuators[i].flags &= static_cast<uint8_t>(~ACTUATOR_CALIBRATED);
    }
  }
}

void startActuator(uint8_t index, Direction direction, uint16_t pwmPermille) {
  stopActuator(index);
  delay(hw::DIRECTION_DEADTIME_MS);
  digitalWrite(hw::INA_PINS[index], direction == Direction::Extend ? HIGH : LOW);
  digitalWrite(hw::INB_PINS[index], direction == Direction::Retract ? HIGH : LOW);
  actuators[index].direction = direction;
  actuators[index].startedAt = millis();
  actuators[index].overCurrentSince = 0;
  actuators[index].zeroCurrentSince = 0;
  actuators[index].earlyZeroSince = 0;
  actuators[index].moving = true;
  actuators[index].finished = false;
  actuators[index].flags = ACTUATOR_MOVING | ACTUATOR_DIAG_OK;
  if (config.lastOpenMs[index] != 0 && config.lastCloseMs[index] != 0) {
    actuators[index].flags |= ACTUATOR_CALIBRATED;
  }
  if (direction == Direction::Extend) actuators[index].flags |= ACTUATOR_EXTEND;
  writePwm(index, pwmPermille);
}

void sendStopToSlaves();
void configureReedInputs();

void setFault(Fault value, uint8_t actuator = 0) {
  stopLocal();
  if (isMaster()) sendStopToSlaves();
  fault = value;
  faultActuator = actuator;
  runState = RunState::Fault;
  activeCommand = Command::None;
}

void clearFault() {
  stopLocal();
  fault = carrierConfigured || !isMaster() ? Fault::None : Fault::NotConfigured;
  faultActuator = 0;
  runState = fault == Fault::None ? RunState::Safe : RunState::Fault;
  activeCommand = Command::None;
}

void applyConfigPayload(const LocalConfigPayload &payload) {
  carrier.reserved = payload.reedPolarityMask & 0x07u;
  configureReedInputs();
  config.revision = payload.revision;
  config.minTravelMs = payload.minTravelMs;
  config.endstopConfirmMs = payload.endstopConfirmMs;
  config.maxTravelMs = payload.maxTravelMs;
  for (uint8_t i = 0; i < 2; ++i) {
    config.maxCurrentMa[i] = payload.maxCurrentMa[i];
    config.zeroCurrentMa[i] = payload.zeroCurrentMa[i];
    config.pwmOpenPermille[i] = constrain(payload.pwmOpenPermille[i], hw::MIN_CALIBRATION_PWM_PERMILLE, hw::PWM_MAX);
    config.pwmClosePermille[i] = constrain(payload.pwmClosePermille[i], hw::MIN_CALIBRATION_PWM_PERMILLE, hw::PWM_MAX);
  }
  saveConfig();
}

LocalConfigPayload makeConfigPayload() {
  LocalConfigPayload payload = {};
  payload.revision = config.revision;
  payload.minTravelMs = config.minTravelMs;
  payload.endstopConfirmMs = config.endstopConfirmMs;
  payload.maxTravelMs = config.maxTravelMs;
  payload.reedPolarityMask = carrier.reserved & 0x07u;
  for (uint8_t i = 0; i < 2; ++i) {
    payload.maxCurrentMa[i] = config.maxCurrentMa[i];
    payload.zeroCurrentMa[i] = config.zeroCurrentMa[i];
    payload.pwmOpenPermille[i] = config.pwmOpenPermille[i];
    payload.pwmClosePermille[i] = config.pwmClosePermille[i];
  }
  return payload;
}

void forwardCommandToSlaves(Command command, uint8_t flags, uint16_t argument) {
  LocalCommandPayload payload = {
    static_cast<uint8_t>(command), flags, argument, config.revision
  };
  for (uint8_t i = 0; i < carrier.slaveCount; ++i) {
    localLinks[i].send(UartType::Command, ++slaveTxSequence[i], &payload, sizeof(payload));
  }
}

void sendStopToSlaves() {
  for (uint8_t i = 0; i < carrier.slaveCount; ++i) {
    localLinks[i].send(UartType::Stop, ++slaveTxSequence[i], nullptr, 0);
  }
}

void executeCommand(Command command, uint8_t flags, uint16_t argument, bool fromMaster) {
  const uint32_t now = millis();
  lastCommandAt = now;

  if (command == Command::ConfigureCap1188 && isMaster()) {
    config.capEnabledMask = static_cast<uint8_t>(argument);
    ++config.revision;
    saveConfig();
    if (capOnline) cap1188.setEnabledMask(config.capEnabledMask);
    capMask &= config.capEnabledMask;
    return;
  }

  if (command == Command::Stop) {
    stopLocal();
    if (isMaster()) sendStopToSlaves();
    activeCommand = Command::None;
    runState = RunState::Idle;
    return;
  }
  if (command == Command::ClearFault) {
    clearFault();
    if (isMaster()) forwardCommandToSlaves(command, flags, argument);
    return;
  }
  if (command == Command::ResetCalibration) {
    stopLocal();
    memset(config.lastOpenMs, 0, sizeof(config.lastOpenMs));
    memset(config.lastCloseMs, 0, sizeof(config.lastCloseMs));
    for (uint8_t i = 0; i < 2; ++i) {
      config.pwmOpenPermille[i] = hw::PWM_MAX;
      config.pwmClosePermille[i] = hw::PWM_MAX;
    }
    ++config.revision;
    saveConfig();
    if (isMaster()) {
      for (uint8_t slot = 0; slot < carrier.slaveCount; ++slot) {
        for (uint8_t i = 0; i < 2; ++i) {
          slaveConfigs[slot].pwmOpenPermille[i] = hw::PWM_MAX;
          slaveConfigs[slot].pwmClosePermille[i] = hw::PWM_MAX;
        }
        ++slaveConfigs[slot].revision;
      }
    }
    refreshCalibrationFlags();
    activeCommand = Command::None;
    runState = RunState::Idle;
    if (isMaster() && !fromMaster) forwardCommandToSlaves(command, flags, argument);
    return;
  }
  if (command == Command::Arm) {
    armedUntil = now + hw::COMMAND_ARM_WINDOW_MS;
    if (runState == RunState::Safe) runState = RunState::Idle;
    if (isMaster()) forwardCommandToSlaves(command, flags, argument);
    return;
  }

  const bool armed = static_cast<int32_t>(armedUntil - now) > 0 || (flags & COMMAND_FLAG_ARMED);
  if (!armed || fault != Fault::None || (isMaster() && !carrierConfigured)) return;

  const Direction direction = commandDirection(command);
  if (direction == Direction::None) return;
  if (activeCommand == command && (runState == RunState::Moving || runState == RunState::Calibrating)) return;

  activeCommand = command;
  lastMovementCommand = command;
  runState = (command == Command::CalibrateOpen || command == Command::CalibrateClose)
               ? RunState::Calibrating
               : RunState::Moving;
  calibrationPendingApply = runState == RunState::Calibrating;
  for (uint8_t i = 0; i < 2; ++i) startActuator(i, direction, commandPwm(i, command));
  if (isMaster() && !fromMaster) forwardCommandToSlaves(command, flags | COMMAND_FLAG_ARMED, argument);
}

void updateCurrent(uint8_t index) {
  const uint16_t raw = analogRead(hw::CURRENT_PINS[index]);
  const uint32_t ma = (static_cast<uint32_t>(raw) * hw::CURRENT_MA_PER_ADC_COUNT_NUM) /
                      hw::CURRENT_MA_PER_ADC_COUNT_DEN;
  actuators[index].currentMa = min<uint32_t>(ma, 65535u);
  if (actuators[index].filteredCurrentMa == 0) actuators[index].filteredCurrentMa = actuators[index].currentMa;
  else actuators[index].filteredCurrentMa = static_cast<uint16_t>(
    (static_cast<uint32_t>(actuators[index].filteredCurrentMa) * 7u + actuators[index].currentMa) / 8u);
}

void finishActuatorAtEndstop(uint8_t index, uint32_t now) {
  const uint32_t travel = now - actuators[index].startedAt;
  const uint16_t stored = static_cast<uint16_t>(min<uint32_t>(travel, 65535u));
  if (actuators[index].direction == Direction::Extend) config.lastOpenMs[index] = stored;
  else if (actuators[index].direction == Direction::Retract) config.lastCloseMs[index] = stored;
  actuators[index].flags |= ACTUATOR_ENDSTOP;
  refreshCalibrationFlags();
  actuators[index].finished = true;
  stopActuator(index);
}

void updateActuatorProtection(uint8_t index, uint32_t now) {
  auto &actuator = actuators[index];
  if (!actuator.moving) return;

  const bool diagOk = digitalRead(hw::DIAG_PINS[index]) == HIGH;
  if (diagOk) actuator.flags |= ACTUATOR_DIAG_OK;
  else {
    actuator.flags &= static_cast<uint8_t>(~ACTUATOR_DIAG_OK);
    setFault(Fault::DriverDiagnostic, index + 1);
    return;
  }

  if (actuator.filteredCurrentMa > config.maxCurrentMa[index]) {
    if (actuator.overCurrentSince == 0) actuator.overCurrentSince = now;
    if (now - actuator.overCurrentSince >= hw::OVERCURRENT_CONFIRM_MS) {
      actuator.flags |= ACTUATOR_OVERCURRENT;
      setFault(Fault::OverCurrent, index + 1);
      return;
    }
  } else {
    actuator.overCurrentSince = 0;
  }

  const uint32_t elapsed = now - actuator.startedAt;
  const bool zero = actuator.filteredCurrentMa <= config.zeroCurrentMa[index];
  if (zero) {
    if (actuator.zeroCurrentSince == 0) actuator.zeroCurrentSince = now;
  } else {
    actuator.zeroCurrentSince = 0;
    actuator.earlyZeroSince = 0;
  }

  if (elapsed >= config.minTravelMs && actuator.zeroCurrentSince != 0 &&
      now - actuator.zeroCurrentSince >= config.endstopConfirmMs) {
    finishActuatorAtEndstop(index, now);
    return;
  }

  if (elapsed >= hw::NO_CURRENT_STARTUP_MS && elapsed < config.minTravelMs && zero) {
    if (actuator.earlyZeroSince == 0) actuator.earlyZeroSince = now;
    if (now - actuator.earlyZeroSince >= config.endstopConfirmMs) {
      actuator.flags |= ACTUATOR_NO_CURRENT;
      setFault(Fault::NoCurrent, index + 1);
      return;
    }
  }

  if (elapsed >= config.maxTravelMs) setFault(Fault::MovementTimeout, index + 1);
}

bool localMovementFinished() {
  return !actuators[0].moving && !actuators[1].moving && actuators[0].finished && actuators[1].finished;
}

bool cabinetMovementFinished() {
  if (!localMovementFinished()) return false;
  if (!isMaster()) return true;
  for (uint8_t i = 0; i < carrier.slaveCount; ++i) {
    if (millis() - slaveLastSeen[i] > hw::SLAVE_TIMEOUT_MS) return false;
    if (slaveStatus[i].state == static_cast<uint8_t>(RunState::Moving) ||
        slaveStatus[i].state == static_cast<uint8_t>(RunState::Calibrating)) return false;
  }
  return true;
}

void sendConfigToSlave(uint8_t slot) {
  if (slot >= carrier.slaveCount) return;
  LocalConfigPayload payload = slaveConfigs[slot];
  payload.reedPolarityMask = static_cast<uint8_t>((carrier.reserved >> ((slot + 1u) * 3u)) & 0x07u);
  localLinks[slot].send(UartType::Config, ++slaveTxSequence[slot], &payload, sizeof(payload));
}

void handlePowerFailure() {
  if (!isMaster() || powerLossHandled || digitalRead(hw::POWER_GOOD) != LOW) return;
  powerLossHandled = true;

  PowerLossRecord record = {};
  record.uptimeMs = millis();
  record.sequence = static_cast<uint8_t>(powerLossRecord.sequence + 1u);
  record.runState = static_cast<uint8_t>(runState);
  record.command = static_cast<uint8_t>(activeCommand);
  record.fault = static_cast<uint8_t>(fault);
  record.actuator = faultActuator;

  stopLocal();
  sendStopToSlaves();
  digitalWrite(hw::CAP_CS, HIGH);
  if (carrierStore.savePowerLoss(record)) {
    powerLossRecord = record;
    powerLossRecord.pending = 1;
    powerLossEventPending = true;
  }
  setFault(Fault::LowSupply);
}

void sendPendingPowerEvent() {
  if (!isMaster() || !powerLossEventPending || !carrierConfigured || !canOnline ||
      digitalRead(hw::POWER_GOOD) == LOW || millis() - lastPowerEventAttempt < 1000) return;
  lastPowerEventAttempt = millis();
  const CanEventFrame event = {
    PROTOCOL_VERSION,
    powerLossRecord.sequence,
    static_cast<uint8_t>(Fault::PowerRecovered),
    powerLossRecord.actuator,
    powerLossRecord.uptimeMs,
  };
  if (canBus.send(CAN_EVENT_BASE + carrier.cabinetId, &event, sizeof(event)) &&
      carrierStore.acknowledgePowerLoss(powerLossRecord)) {
    powerLossRecord.pending = 0;
    powerLossEventPending = false;
    powerLossHandled = false;
  }
}

void applyCalibration() {
  uint16_t target = 0;
  const bool opening = activeCommand == Command::CalibrateOpen;
  for (uint8_t i = 0; i < 2; ++i) target = max(target, opening ? config.lastOpenMs[i] : config.lastCloseMs[i]);
  for (uint8_t slot = 0; slot < carrier.slaveCount; ++slot) {
    for (uint8_t i = 0; i < 2; ++i) target = max(target, slaveStatus[slot].lastTravelMs[i]);
  }
  if (target == 0) {
    setFault(Fault::CalibrationFailed);
    return;
  }

  for (uint8_t i = 0; i < 2; ++i) {
    const uint16_t measured = opening ? config.lastOpenMs[i] : config.lastCloseMs[i];
    uint16_t adjusted = static_cast<uint16_t>((static_cast<uint32_t>(hw::PWM_MAX) * measured) / target);
    adjusted = constrain(adjusted, hw::MIN_CALIBRATION_PWM_PERMILLE, hw::PWM_MAX);
    if (opening) config.pwmOpenPermille[i] = adjusted;
    else config.pwmClosePermille[i] = adjusted;
  }
  for (uint8_t slot = 0; slot < carrier.slaveCount; ++slot) {
    for (uint8_t i = 0; i < 2; ++i) {
      const uint16_t measured = slaveStatus[slot].lastTravelMs[i];
      uint16_t adjusted = static_cast<uint16_t>((static_cast<uint32_t>(hw::PWM_MAX) * measured) / target);
      adjusted = constrain(adjusted, hw::MIN_CALIBRATION_PWM_PERMILLE, hw::PWM_MAX);
      if (opening) slaveConfigs[slot].pwmOpenPermille[i] = adjusted;
      else slaveConfigs[slot].pwmClosePermille[i] = adjusted;
    }
    ++slaveConfigs[slot].revision;
  }
  ++config.revision;
  saveConfig();
  refreshCalibrationFlags();
  for (uint8_t slot = 0; slot < carrier.slaveCount; ++slot) sendConfigToSlave(slot);
}

void completeMovementIfReady() {
  if (!cabinetMovementFinished()) return;
  if (calibrationPendingApply && isMaster()) applyCalibration();
  calibrationPendingApply = false;
  if (fault != Fault::None) return;
  position = commandDirection(activeCommand) == Direction::Extend ? Position::Open : Position::Closed;
  activeCommand = Command::None;
  runState = RunState::Idle;
}

void configureReedInputs() {
  for (uint8_t i = 0; i < 3; ++i) {
    const bool activeHigh = carrierConfigured && (carrier.reserved & (1u << i)) != 0;
    pinMode(hw::REED_PINS[i], activeHigh ? INPUT_PULLDOWN : INPUT_PULLUP);
  }
}

uint8_t readLocalReeds() {
  uint8_t nextReeds = 0;
  for (uint8_t i = 0; i < 3; ++i) {
    const bool activeHigh = (carrier.reserved & (1u << i)) != 0;
    if ((digitalRead(hw::REED_PINS[i]) == HIGH) == activeHigh) nextReeds |= 1u << i;
  }
  return nextReeds;
}

void readMasterSensors() {
  reedMask = readLocalReeds();
  const bool doubleDoor = carrierConfigured &&
                          carrier.objectType == static_cast<uint8_t>(ObjectType::DoubleDoor);
  if (doubleDoor && carrier.slaveCount > 0 && millis() - slaveLastSeen[0] <= hw::SLAVE_TIMEOUT_MS) {
    reedMask |= static_cast<uint8_t>((slaveStatus[0].reedMask & 0x07u) << 3);
  }

  const bool leafAConflict = (reedMask & 0x03u) == 0x03u;
  const bool leafBConflict = doubleDoor && (reedMask & 0x18u) == 0x18u;
  if (leafAConflict || leafBConflict) {
    setFault(Fault::SensorConflict);
    return;
  }
  if (doubleDoor) {
    const bool bothOpen = (reedMask & 0x09u) == 0x09u;
    const bool bothClosed = (reedMask & 0x12u) == 0x12u;
    if (bothOpen) position = Position::Open;
    else if (bothClosed) position = Position::Closed;
    else position = Position::Intermediate;
  } else {
    if (reedMask & 0x01u) position = Position::Open;
    else if (reedMask & 0x02u) position = Position::Closed;
    else position = Position::Intermediate;
  }

  if (capOnline) capMask = cap1188.touched() & config.capEnabledMask;
  if (capMask != 0 && commandDirection(activeCommand) == Direction::Retract) {
    setFault(Fault::SafetyEdge);
  }
  if (digitalRead(hw::POWER_GOOD) == LOW) setFault(Fault::LowSupply);
}

LocalStatusPayload makeLocalStatus() {
  LocalStatusPayload status = {};
  status.slot = roleIndex();
  status.state = static_cast<uint8_t>(runState);
  status.target = static_cast<uint8_t>(activeCommand);
  status.fault = static_cast<uint8_t>(fault);
  status.faultActuator = faultActuator;
  status.bootId = bootId;
  status.reedMask = reedMask & 0x07u;
  for (uint8_t i = 0; i < 2; ++i) {
    status.currentMa[i] = actuators[i].filteredCurrentMa;
    status.pwm[i] = static_cast<uint8_t>(actuators[i].pwmPermille / 4u);
    status.actuatorFlags[i] = actuators[i].flags;
    status.lastTravelMs[i] = commandDirection(lastMovementCommand) == Direction::Retract
                               ? config.lastCloseMs[i]
                               : config.lastOpenMs[i];
  }
  return status;
}

void pollSlaveLink() {
  uint8_t payload[UART_MAX_PAYLOAD] = {};
  uint8_t length = 0;
  uint8_t sequence = 0;
  UartType type;
  while (localLinks[0].poll(type, sequence, payload, length)) {
    if (type == UartType::Stop) {
      executeCommand(Command::Stop, 0, 0, true);
    } else if (type == UartType::Command && length == sizeof(LocalCommandPayload)) {
      LocalCommandPayload command = {};
      memcpy(&command, payload, sizeof(command));
      executeCommand(static_cast<Command>(command.command), command.flags, command.argument, true);
    } else if (type == UartType::Config && length == sizeof(LocalConfigPayload)) {
      LocalConfigPayload incoming = {};
      memcpy(&incoming, payload, sizeof(incoming));
      applyConfigPayload(incoming);
      localLinks[0].send(UartType::ConfigAck, sequence, &config.revision, sizeof(config.revision));
    }
  }
}

void pollMasterLinks() {
  for (uint8_t slot = 0; slot < carrier.slaveCount; ++slot) {
    uint8_t payload[UART_MAX_PAYLOAD] = {};
    uint8_t length = 0;
    uint8_t sequence = 0;
    UartType type;
    while (localLinks[slot].poll(type, sequence, payload, length)) {
      if (type == UartType::Status && length == sizeof(LocalStatusPayload)) {
        const bool firstStatus = slaveLastSeen[slot] == 0;
        memcpy(&slaveStatus[slot], payload, sizeof(LocalStatusPayload));
        slaveLastSeen[slot] = millis();
        if (firstStatus) sendConfigToSlave(slot);
        if (slaveStatus[slot].fault != static_cast<uint8_t>(Fault::None) && fault == Fault::None) {
          setFault(static_cast<Fault>(slaveStatus[slot].fault), slot * 2 + slaveStatus[slot].faultActuator + 2);
        }
      }
    }
  }
}

void sendSlaveStatus() {
  static uint8_t sequence = 0;
  const LocalStatusPayload status = makeLocalStatus();
  localLinks[0].send(UartType::Status, ++sequence, &status, sizeof(status));
}

void sendDiscovery() {
  CanDiscoveryFrame response = {
    uidHash,
    static_cast<uint8_t>(carrierConfigured),
    carrierConfigured ? carrier.cabinetId : static_cast<uint8_t>(0xFF),
    roleIndex(),
    static_cast<uint8_t>(hw::FW_BUILD),
  };
  const uint16_t id = CAN_DISCOVERY_RESPONSE_BASE + (carrierConfigured ? carrier.cabinetId : 63u);
  canBus.send(id, &response, sizeof(response));
}

void sendProvisionResult(const CanProvisionFrame &request, ProvisionResult result,
                         uint16_t configRevision = 0) {
  const CanProvisionResultFrame response = {
    request.uidHash,
    request.cabinetId,
    static_cast<uint8_t>(result),
    configRevision,
  };
  canBus.send(CAN_PROVISION_RESPONSE, &response, sizeof(response));
}

void handleProvision(const CanProvisionFrame &request) {
  if (!isMaster() || request.uidHash != uidHash) return;
  if (runState == RunState::Moving || runState == RunState::Calibrating) {
    sendProvisionResult(request, ProvisionResult::Busy);
    return;
  }
  if (!validCabinetId(request.cabinetId) || request.slaveCount > 3 ||
      request.objectType > static_cast<uint8_t>(ObjectType::DoubleDoor)) {
    sendProvisionResult(request, ProvisionResult::InvalidRequest);
    return;
  }
  CarrierIdentity next = {};
  next.cabinetId = request.cabinetId;
  next.objectType = request.objectType;
  next.slaveCount = request.slaveCount;
  next.reserved = request.flags & 0x3Fu;
  if (carrierStore.save(next)) {
    carrierConfigured = carrierStore.load(carrier);
    if (carrierConfigured && carrier.cabinetId == request.cabinetId &&
        carrier.objectType == request.objectType && carrier.slaveCount == request.slaveCount &&
        carrier.reserved == (request.flags & 0x3Fu)) {
      configureReedInputs();
      clearFault();
      sendProvisionResult(request, ProvisionResult::Success, carrier.configRevision);
      sendDiscovery();
      return;
    }
  }
  sendProvisionResult(request, ProvisionResult::WriteVerifyFailed);
}

void pollCan() {
  CanMessage message;
  while (canBus.receive(message)) {
    if (message.id == CAN_DISCOVERY_REQUEST) {
      const uint32_t spread = uidHash & 0x3Fu;
      if (millis() - lastDiscoveryAt > 100 + spread * 2) {
        lastDiscoveryAt = millis();
        sendDiscovery();
      }
      continue;
    }
    if (message.id == CAN_PROVISION_REQUEST && message.length == sizeof(CanProvisionFrame)) {
      CanProvisionFrame request = {};
      memcpy(&request, message.data, sizeof(request));
      handleProvision(request);
      continue;
    }
    if (!carrierConfigured || message.id != CAN_COMMAND_BASE + carrier.cabinetId ||
        message.length != sizeof(CanCommandFrame)) continue;

    CanCommandFrame command = {};
    memcpy(&command, message.data, sizeof(command));
    if (command.version != PROTOCOL_VERSION) continue;
    lastCommandAt = millis();
    const Command value = static_cast<Command>(command.command);
    if (command.sequence != lastCommandSequence || value == Command::Arm || value == Command::Stop) {
      lastCommandSequence = command.sequence;
      executeCommand(value, command.flags, command.argument, false);
    } else {
      forwardCommandToSlaves(value, command.flags | COMMAND_FLAG_ARMED, command.argument);
    }
  }
}

void sendCanTelemetry() {
  if (!carrierConfigured || !canOnline) return;

  uint8_t slaveMask = 0;
  Fault aggregateFault = fault;
  uint8_t aggregateActuator = faultActuator;
  for (uint8_t i = 0; i < carrier.slaveCount; ++i) {
    if (millis() - slaveLastSeen[i] <= hw::SLAVE_TIMEOUT_MS) slaveMask |= 1u << i;
    else if (runState == RunState::Moving || runState == RunState::Calibrating) {
      aggregateFault = Fault::SlaveOffline;
      aggregateActuator = i * 2 + 3;
    }
  }

  CanStatusFrame status = {
    PROTOCOL_VERSION, bootId, static_cast<uint8_t>(runState), static_cast<uint8_t>(activeCommand),
    static_cast<uint8_t>(position), static_cast<uint8_t>(aggregateFault), aggregateActuator, slaveMask
  };
  canBus.send(CAN_STATUS_BASE + carrier.cabinetId, &status, sizeof(status));

  CanSensorFrame sensors = {
    PROTOCOL_VERSION, reedMask, capMask,
    static_cast<uint8_t>((capOnline ? 1u : 0u) |
                         (digitalRead(hw::POWER_GOOD) == HIGH ? 2u : 0u) |
                         ((capOnline && (cap1188.noiseFlags() & config.capEnabledMask)) ? 4u : 0u)),
    0, static_cast<uint16_t>(min<uint32_t>(millis() / 1000u, 65535u))
  };
  canBus.send(CAN_SENSORS_BASE + carrier.cabinetId, &sensors, sizeof(sensors));

  CanActuatorFrame local = {};
  for (uint8_t i = 0; i < 2; ++i) {
    local.currentMa[i] = actuators[i].filteredCurrentMa;
    local.pwm[i] = static_cast<uint8_t>(actuators[i].pwmPermille / 4u);
    local.flags[i] = actuators[i].flags;
  }
  canBus.send(CAN_ACTUATORS_BASE + carrier.cabinetId * 4u, &local, sizeof(local));

  for (uint8_t slot = 0; slot < carrier.slaveCount; ++slot) {
    if (millis() - slaveLastSeen[slot] > hw::SLAVE_TIMEOUT_MS) continue;
    CanActuatorFrame remote = {};
    for (uint8_t i = 0; i < 2; ++i) {
      remote.currentMa[i] = slaveStatus[slot].currentMa[i];
      remote.pwm[i] = slaveStatus[slot].pwm[i];
      remote.flags[i] = slaveStatus[slot].actuatorFlags[i];
    }
    canBus.send(CAN_ACTUATORS_BASE + carrier.cabinetId * 4u + slot + 1u, &remote, sizeof(remote));
  }
}

void initializePins() {
  analogReadResolution(12);
  analogWriteResolution(10);
  analogWriteFrequency(hw::PWM_FREQUENCY_HZ);
  for (uint8_t i = 0; i < 2; ++i) {
    pinMode(hw::PWM_PINS[i], OUTPUT);
    pinMode(hw::INA_PINS[i], OUTPUT);
    pinMode(hw::INB_PINS[i], OUTPUT);
    pinMode(hw::DIAG_PINS[i], INPUT_PULLUP);
    stopActuator(i);
  }
  pinMode(hw::POWER_GOOD, INPUT_PULLUP);
}

void initializeMaster() {
  pinMode(hw::CAP_IRQ, INPUT_PULLUP);
  carrierStore.begin();
  carrierConfigured = carrierStore.load(carrier);
  if (carrierStore.loadPowerLoss(powerLossRecord)) powerLossEventPending = powerLossRecord.pending != 0;
  else memset(&powerLossRecord, 0, sizeof(powerLossRecord));
  configureReedInputs();
  capOnline = cap1188.begin(config.capEnabledMask);
  const LocalConfigPayload defaults = makeConfigPayload();
  for (uint8_t i = 0; i < 3; ++i) slaveConfigs[i] = defaults;
  for (uint8_t i = 0; i < 3; ++i) localLinks[i].begin(hw::LOCAL_UART_BAUD);
  canOnline = canBus.begin(hw::CAN_BITRATE);
  clearFault();
  if (!carrierConfigured) setFault(Fault::NotConfigured);
  else if (!capOnline && carrier.objectType != static_cast<uint8_t>(ObjectType::Window)) {
    setFault(Fault::Cap1188Offline);
  }
}

void initializeSlave() {
  localLinks[0].begin(hw::LOCAL_UART_BAUD);
  carrierConfigured = true;
  configureReedInputs();
  clearFault();
}

}  // namespace

void setup() {
  bootId = static_cast<uint8_t>(micros() ^ readUidHash());
  uidHash = readUidHash();
  boardRole = readBoardRole();
  initializePins();
  loadConfig();
  if (isMaster()) initializeMaster();
  else initializeSlave();
  IWatchdog.begin(3000000);
}

void loop() {
  const uint32_t now = millis();
  IWatchdog.reload();

  if (isMaster() && digitalRead(hw::POWER_GOOD) == LOW) {
    handlePowerFailure();
    delay(1);
    return;
  }

  if (isMaster()) {
    pollCan();
    pollMasterLinks();
    sendPendingPowerEvent();
  } else {
    pollSlaveLink();
  }

  if (now - lastSensorAt >= hw::SENSOR_PERIOD_MS) {
    lastSensorAt = now;
    for (uint8_t i = 0; i < 2; ++i) updateCurrent(i);
    if (isMaster()) readMasterSensors();
    else reedMask = readLocalReeds();
  }

  if (now - lastControlAt >= hw::CONTROL_PERIOD_MS) {
    lastControlAt = now;
    for (uint8_t i = 0; i < 2; ++i) updateActuatorProtection(i, now);
    completeMovementIfReady();
    if ((runState == RunState::Moving || runState == RunState::Calibrating) &&
        now - lastCommandAt > hw::HEARTBEAT_TIMEOUT_MS) {
      setFault(Fault::CommunicationTimeout);
    }
  }

  const uint32_t statusPeriod = (runState == RunState::Moving || runState == RunState::Calibrating)
                                  ? hw::STATUS_PERIOD_MOVING_MS
                                  : hw::STATUS_PERIOD_IDLE_MS;
  if (now - lastStatusAt >= statusPeriod) {
    lastStatusAt = now;
    if (isMaster()) sendCanTelemetry();
    else sendSlaveStatus();
  }
}
