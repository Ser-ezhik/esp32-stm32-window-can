#include <Arduino.h>
#include <ELECHOUSE_CC1101_SRC_DRV.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <WebServer.h>
#include <WiFi.h>
#include <driver/twai.h>
#include <WindowBusProtocol.h>

#include "WebUi.h"

using namespace windowbus;

namespace {

constexpr char FW_VERSION[] = "0.1.0-alpha.5";
constexpr uint8_t FW_BUILD = 5;

constexpr int PIN_RF_SCK = 12;
constexpr int PIN_RF_MISO = 13;
constexpr int PIN_RF_MOSI = 11;
constexpr int PIN_RF_CS = 10;
constexpr int PIN_RF_GDO0 = 4;
constexpr int PIN_RF_GDO2 = 5;
constexpr int PIN_LEARN_BUTTON = 9;
constexpr int PIN_CAN_RX = 38;
constexpr int PIN_CAN_TX = 39;

constexpr char WEB_USER[] = "admin";
constexpr char WEB_PASSWORD[] = "admin12345";
constexpr char SETUP_AP_PASSWORD[] = "12345678";
constexpr uint32_t WIFI_CONNECT_TIMEOUT_MS = 15000;
constexpr uint32_t CAN_HEARTBEAT_MS = 100;
constexpr uint32_t OBJECT_OFFLINE_MS = 3000;
constexpr uint32_t COMMAND_MAX_MS = 60000;
constexpr uint8_t EVENT_COUNT = 48;
constexpr uint8_t REMOTE_COUNT = 36;
constexpr uint8_t DISCOVERY_COUNT = 24;
constexpr uint8_t NAME_LENGTH = 32;

constexpr float RF_FREQUENCY_MHZ = 433.92f;
constexpr float RF_DATA_RATE_KBPS = 19.2f;
constexpr uint32_t RF_IDLE_FRAME_US = 18000;
constexpr uint32_t RF_DEBOUNCE_MS = 250;
constexpr size_t RF_MAX_PULSES = 180;
constexpr uint32_t RF_SHORT_MIN_US = 180;
constexpr uint32_t RF_SHORT_MAX_US = 560;
constexpr uint32_t RF_LONG_MIN_US = 650;
constexpr uint32_t RF_LONG_MAX_US = 1300;
constexpr uint32_t RF_SYNC_MIN_US = 5000;
constexpr uint32_t RF_SYNC_MAX_US = 14000;
constexpr uint8_t RF_EXPECTED_BITS = 24;
constexpr uint32_t LEARN_TIMEOUT_MS = 30000;
constexpr uint32_t LEARN_BUTTON_LONG_MS = 5000;

#pragma pack(push, 1)
struct ObjectConfig {
  uint8_t enabled;
  uint8_t id;
  uint8_t cabinetId;
  uint8_t type;
  uint8_t actuatorCount;
  uint8_t slaveCount;
  char name[NAME_LENGTH];
  uint8_t capEnabledMask;
};

struct RemoteRecord {
  uint32_t code;
  uint64_t targetMask;
  uint8_t command;
  uint8_t enabled;
  char name[NAME_LENGTH];
};
#pragma pack(pop)

struct ActuatorRuntime {
  uint16_t currentMa = 0;
  uint8_t pwmRaw = 0;
  uint8_t flags = 0;
  bool online = false;
};

struct ObjectRuntime {
  bool online = false;
  uint8_t state = static_cast<uint8_t>(RunState::Boot);
  uint8_t target = static_cast<uint8_t>(Command::None);
  uint8_t position = static_cast<uint8_t>(Position::Unknown);
  uint8_t fault = static_cast<uint8_t>(Fault::None);
  uint8_t faultActuator = 0;
  uint8_t slaveMask = 0;
  uint8_t reedMask = 0;
  uint8_t capMask = 0;
  uint8_t sensorFlags = 0;
  uint8_t bootId = 0;
  uint8_t lastFault = 0;
  uint8_t commandSequence = 0;
  Command heartbeatCommand = Command::None;
  Command pendingCalibration = Command::None;
  bool calibrationSawMotion = false;
  uint32_t lastSeen = 0;
  uint32_t nextHeartbeat = 0;
  uint32_t commandStarted = 0;
  ActuatorRuntime actuators[MAX_ACTUATORS_PER_CABINET];
};

struct EventRecord {
  uint32_t timestamp;
  uint8_t objectId;
  uint8_t code;
  uint8_t actuator;
  char text[48];
};

struct DiscoveryRecord {
  uint32_t uidHash = 0;
  uint8_t configured = 0;
  uint8_t cabinetId = 0xFF;
  uint8_t role = 0;
  uint8_t firmware = 0;
  uint32_t lastSeen = 0;
};

Preferences prefs;
WebServer server(80);
ObjectConfig objects[MAX_CABINETS] = {};
ObjectRuntime runtime[MAX_CABINETS] = {};
RemoteRecord remotes[REMOTE_COUNT] = {};
EventRecord events[EVENT_COUNT] = {};
DiscoveryRecord discovered[DISCOVERY_COUNT] = {};
uint8_t objectCount = 0;
uint8_t remoteCount = 0;
uint8_t eventHead = 0;
uint8_t eventSize = 0;
uint8_t discoveredCount = 0;
char wifiSsid[33] = {};
char wifiPassword[65] = {};
char systemName[NAME_LENGTH] = "Окна и двери";
bool setupApMode = false;
bool canReady = false;
bool radioReady = false;
bool learnMode = false;
uint32_t learnStarted = 0;
uint32_t lastRfCode = 0;
uint32_t lastRfCodeAt = 0;
uint32_t learnButtonPressedAt = 0;
bool learnButtonWasDown = false;

volatile uint16_t rfPulseCount = 0;
volatile uint32_t rfPulses[RF_MAX_PULSES] = {};
volatile uint32_t rfLastEdgeUs = 0;
volatile uint32_t rfLastActivityUs = 0;
volatile bool rfHadActivity = false;
portMUX_TYPE rfMux = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR onRfEdge() {
  const uint32_t now = micros();
  portENTER_CRITICAL_ISR(&rfMux);
  if (rfHadActivity && rfPulseCount < RF_MAX_PULSES) {
    const uint16_t index = rfPulseCount;
    rfPulses[index] = now - rfLastEdgeUs;
    rfPulseCount = index + 1;
  }
  rfHadActivity = true;
  rfLastEdgeUs = now;
  rfLastActivityUs = now;
  portEXIT_CRITICAL_ISR(&rfMux);
}

String jsonEscape(const char *text) {
  String result;
  if (text == nullptr) return result;
  result.reserve(strlen(text) + 8);
  while (*text) {
    const char c = *text++;
    if (c == '\\' || c == '"') { result += '\\'; result += c; }
    else if (c == '\n') result += F("\\n");
    else if (static_cast<uint8_t>(c) >= 0x20) result += c;
  }
  return result;
}

const char *commandName(Command command) {
  switch (command) {
    case Command::Open: return "open";
    case Command::Close: return "close";
    case Command::Vent: return "vent";
    case Command::Stop: return "stop";
    case Command::CalibrateOpen: return "calibrate_open";
    case Command::CalibrateClose: return "calibrate_close";
    case Command::CalibrateFull: return "calibrate_full";
    case Command::ResetCalibration: return "reset_calibration";
    default: return "none";
  }
}

Command parseCommand(const String &value) {
  if (value == "open") return Command::Open;
  if (value == "close") return Command::Close;
  if (value == "vent") return Command::Vent;
  if (value == "stop") return Command::Stop;
  if (value == "calibrate_open") return Command::CalibrateOpen;
  if (value == "calibrate_close") return Command::CalibrateClose;
  if (value == "calibrate_full") return Command::CalibrateFull;
  if (value == "clear") return Command::ClearFault;
  if (value == "reset_calibration") return Command::ResetCalibration;
  return Command::None;
}

const char *faultText(uint8_t code) {
  switch (static_cast<Fault>(code)) {
    case Fault::NotConfigured: return "нет конфигурации";
    case Fault::CommunicationTimeout: return "таймаут связи";
    case Fault::OverCurrent: return "перегрузка";
    case Fault::NoCurrent: return "нет тока";
    case Fault::MovementTimeout: return "таймаут движения";
    case Fault::DriverDiagnostic: return "ошибка VNH";
    case Fault::SafetyEdge: return "защитная кромка";
    case Fault::SensorConflict: return "конфликт датчиков";
    case Fault::LowSupply: return "низкое питание";
    case Fault::SlaveOffline: return "нет ведомой STM";
    case Fault::CalibrationFailed: return "ошибка калибровки";
    case Fault::PowerRecovered: return "восстановление питания";
    case Fault::Cap1188Offline: return "нет CAP1188";
    default: return "нет";
  }
}

int objectIndexByCabinet(uint8_t cabinetId) {
  for (uint8_t i = 0; i < objectCount; ++i) {
    if (objects[i].enabled && objects[i].cabinetId == cabinetId) return i;
  }
  return -1;
}

int objectIndexById(uint8_t id) {
  for (uint8_t i = 0; i < objectCount; ++i) if (objects[i].id == id) return i;
  return -1;
}

void setDefaultObjects() {
  memset(objects, 0, sizeof(objects));
  objectCount = 5;
  const ObjectConfig defaults[5] = {
    {1, 0, 1, static_cast<uint8_t>(ObjectType::DoubleDoor), 8, 3, "Двойная дверь", 0x3F},
    {1, 1, 2, static_cast<uint8_t>(ObjectType::SingleDoor), 4, 1, "Одинарная дверь 1", 0x07},
    {1, 2, 3, static_cast<uint8_t>(ObjectType::SingleDoor), 4, 1, "Одинарная дверь 2", 0x07},
    {1, 3, 4, static_cast<uint8_t>(ObjectType::SingleDoor), 4, 1, "Одинарная дверь 3", 0x07},
    {1, 4, 5, static_cast<uint8_t>(ObjectType::Window), 2, 0, "Окно", 0x07},
  };
  memcpy(objects, defaults, sizeof(defaults));
}

void saveObjects() {
  prefs.begin("windowcan", false);
  prefs.putUChar("objcount", objectCount);
  prefs.putBytes("objects", objects, sizeof(objects));
  prefs.end();
}

void loadObjects() {
  prefs.begin("windowcan", true);
  const size_t stored = prefs.getBytesLength("objects");
  objectCount = prefs.getUChar("objcount", 0);
  if (stored == sizeof(objects) && objectCount <= MAX_CABINETS) prefs.getBytes("objects", objects, sizeof(objects));
  else objectCount = 0;
  prefs.end();
  if (objectCount == 0) { setDefaultObjects(); saveObjects(); }
}

void loadSystemSettings() {
  prefs.begin("windowcan", true);
  prefs.getString("ssid", wifiSsid, sizeof(wifiSsid));
  prefs.getString("pass", wifiPassword, sizeof(wifiPassword));
  prefs.getString("sysname", systemName, sizeof(systemName));
  prefs.end();
}

void saveSystemSettings() {
  prefs.begin("windowcan", false);
  prefs.putString("ssid", wifiSsid);
  prefs.putString("pass", wifiPassword);
  prefs.putString("sysname", systemName);
  prefs.end();
}

void saveRemotes() {
  prefs.begin("windowcan", false);
  prefs.putUChar("rfcount", remoteCount);
  prefs.putBytes("remotes", remotes, sizeof(remotes));
  prefs.end();
}

void loadRemotes() {
  prefs.begin("windowcan", true);
  remoteCount = prefs.getUChar("rfcount", 0);
  if (remoteCount > REMOTE_COUNT || prefs.getBytesLength("remotes") != sizeof(remotes)) remoteCount = 0;
  else prefs.getBytes("remotes", remotes, sizeof(remotes));
  prefs.end();
}

void appendEvent(uint8_t objectId, uint8_t code, uint8_t actuator, const char *text) {
  EventRecord &event = events[eventHead];
  event.timestamp = millis() / 1000u;
  event.objectId = objectId;
  event.code = code;
  event.actuator = actuator;
  strlcpy(event.text, text, sizeof(event.text));
  eventHead = (eventHead + 1u) % EVENT_COUNT;
  if (eventSize < EVENT_COUNT) ++eventSize;
}

bool beginCan() {
  twai_general_config_t general = TWAI_GENERAL_CONFIG_DEFAULT(
    static_cast<gpio_num_t>(PIN_CAN_TX), static_cast<gpio_num_t>(PIN_CAN_RX), TWAI_MODE_NORMAL);
  general.tx_queue_len = 16;
  general.rx_queue_len = 32;
  general.alerts_enabled = TWAI_ALERT_BUS_OFF | TWAI_ALERT_BUS_RECOVERED | TWAI_ALERT_RX_QUEUE_FULL;
  twai_timing_config_t timing = TWAI_TIMING_CONFIG_500KBITS();
  twai_filter_config_t filter = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  if (twai_driver_install(&general, &timing, &filter) != ESP_OK) return false;
  return twai_start() == ESP_OK;
}

bool sendCan(uint16_t id, const void *payload, uint8_t length) {
  if (!canReady || id > 0x7FF || length > 8) return false;
  twai_message_t message = {};
  message.identifier = id;
  message.data_length_code = length;
  if (payload != nullptr && length != 0) memcpy(message.data, payload, length);
  return twai_transmit(&message, pdMS_TO_TICKS(10)) == ESP_OK;
}

void sendObjectCommand(uint8_t index, Command command) {
  if (index >= objectCount || !objects[index].enabled) return;
  ObjectRuntime &state = runtime[index];
  if (command == Command::Stop) {
    CanCommandFrame frame = {PROTOCOL_VERSION, ++state.commandSequence,
      static_cast<uint8_t>(Command::Stop), 0, 0, 0};
    sendCan(CAN_COMMAND_BASE + objects[index].cabinetId, &frame, sizeof(frame));
    state.heartbeatCommand = Command::None;
    return;
  }

  CanCommandFrame arm = {PROTOCOL_VERSION, ++state.commandSequence,
    static_cast<uint8_t>(Command::Arm), 0, 0, 0};
  sendCan(CAN_COMMAND_BASE + objects[index].cabinetId, &arm, sizeof(arm));
  delay(3);
  CanCommandFrame frame = {PROTOCOL_VERSION, ++state.commandSequence,
    static_cast<uint8_t>(command), COMMAND_FLAG_ARMED, 0, 0};
  sendCan(CAN_COMMAND_BASE + objects[index].cabinetId, &frame, sizeof(frame));
  state.heartbeatCommand = command;
  state.commandStarted = millis();
  state.nextHeartbeat = millis() + CAN_HEARTBEAT_MS;
}

void sendCapConfiguration(uint8_t index) {
  if (index >= objectCount || !objects[index].enabled) return;
  ObjectRuntime &state = runtime[index];
  CanCommandFrame frame = {
    PROTOCOL_VERSION, ++state.commandSequence,
    static_cast<uint8_t>(Command::ConfigureCap1188), 0,
    objects[index].capEnabledMask, 0
  };
  sendCan(CAN_COMMAND_BASE + objects[index].cabinetId, &frame, sizeof(frame));
}

void updateHeartbeats() {
  const uint32_t now = millis();
  for (uint8_t i = 0; i < objectCount; ++i) {
    ObjectRuntime &state = runtime[i];
    if (state.heartbeatCommand == Command::None || static_cast<int32_t>(now - state.nextHeartbeat) < 0) continue;
    if (now - state.commandStarted > COMMAND_MAX_MS || state.fault != 0 ||
        (state.online && state.state == static_cast<uint8_t>(RunState::Idle) && now - state.commandStarted > 500)) {
      state.heartbeatCommand = Command::None;
      continue;
    }
    CanCommandFrame frame = {PROTOCOL_VERSION, state.commandSequence,
      static_cast<uint8_t>(state.heartbeatCommand), COMMAND_FLAG_ARMED, 0, 0};
    sendCan(CAN_COMMAND_BASE + objects[i].cabinetId, &frame, sizeof(frame));
    state.nextHeartbeat = now + CAN_HEARTBEAT_MS;
  }
}

void rememberDiscovery(const CanDiscoveryFrame &frame) {
  uint8_t index = DISCOVERY_COUNT;
  for (uint8_t i = 0; i < discoveredCount; ++i) if (discovered[i].uidHash == frame.uidHash) index = i;
  if (index == DISCOVERY_COUNT) {
    if (discoveredCount < DISCOVERY_COUNT) index = discoveredCount++;
    else index = frame.uidHash % DISCOVERY_COUNT;
  }
  discovered[index].uidHash = frame.uidHash;
  discovered[index].configured = frame.configured;
  discovered[index].cabinetId = frame.cabinetId;
  discovered[index].role = frame.role;
  discovered[index].firmware = frame.firmwareBuild;
  discovered[index].lastSeen = millis();
}

void processStatus(uint8_t cabinetId, const CanStatusFrame &frame) {
  const int index = objectIndexByCabinet(cabinetId);
  if (index < 0 || frame.version != PROTOCOL_VERSION) return;
  ObjectRuntime &state = runtime[index];
  const bool needsConfiguration = !state.online || state.bootId != frame.bootId;
  const uint8_t oldFault = state.fault;
  state.online = true;
  state.lastSeen = millis();
  state.state = frame.state;
  state.target = frame.target;
  state.position = frame.position;
  state.fault = frame.fault;
  state.faultActuator = frame.faultActuator;
  state.slaveMask = frame.slaveMask;
  state.bootId = frame.bootId;
  if (needsConfiguration) sendCapConfiguration(index);
  if (state.pendingCalibration != Command::None) {
    if (state.state == static_cast<uint8_t>(RunState::Calibrating)) state.calibrationSawMotion = true;
    if (state.fault != 0) {
      state.pendingCalibration = Command::None;
      state.calibrationSawMotion = false;
    }
  }
  if (oldFault != state.fault) {
    appendEvent(objects[index].id, state.fault, state.faultActuator,
                state.fault == 0 ? "авария сброшена" : faultText(state.fault));
  }
}

void updateCalibrationSequences() {
  for (uint8_t i = 0; i < objectCount; ++i) {
    ObjectRuntime &state = runtime[i];
    if (state.pendingCalibration == Command::None || !state.calibrationSawMotion || !state.online) continue;
    if (state.state != static_cast<uint8_t>(RunState::Idle) || state.fault != 0) continue;
    const Command next = state.pendingCalibration;
    state.pendingCalibration = Command::None;
    state.calibrationSawMotion = false;
    sendObjectCommand(i, next);
    appendEvent(objects[i].id, 0, 0, commandName(next));
  }
}

void processCanMessage(const twai_message_t &message) {
  if (message.extd || message.rtr) return;
  const uint16_t id = static_cast<uint16_t>(message.identifier);
  if (id >= CAN_STATUS_BASE && id < CAN_STATUS_BASE + MAX_CABINETS && message.data_length_code == sizeof(CanStatusFrame)) {
    CanStatusFrame frame = {}; memcpy(&frame, message.data, sizeof(frame));
    processStatus(id - CAN_STATUS_BASE, frame); return;
  }
  if (id >= CAN_SENSORS_BASE && id < CAN_SENSORS_BASE + MAX_CABINETS && message.data_length_code == sizeof(CanSensorFrame)) {
    const int index = objectIndexByCabinet(id - CAN_SENSORS_BASE); if (index < 0) return;
    CanSensorFrame frame = {}; memcpy(&frame, message.data, sizeof(frame));
    runtime[index].reedMask = frame.reedMask; runtime[index].capMask = frame.capMask;
    runtime[index].sensorFlags = frame.flags; runtime[index].lastSeen = millis(); runtime[index].online = true; return;
  }
  if (id >= CAN_ACTUATORS_BASE && id < CAN_EVENT_BASE && message.data_length_code == sizeof(CanActuatorFrame)) {
    const uint16_t offset = id - CAN_ACTUATORS_BASE;
    const uint8_t cabinetId = offset / 4u, slot = offset % 4u;
    const int index = objectIndexByCabinet(cabinetId); if (index < 0) return;
    CanActuatorFrame frame = {}; memcpy(&frame, message.data, sizeof(frame));
    for (uint8_t i = 0; i < 2; ++i) {
      const uint8_t actuator = slot * 2u + i; if (actuator >= MAX_ACTUATORS_PER_CABINET) continue;
      runtime[index].actuators[actuator].currentMa = frame.currentMa[i];
      runtime[index].actuators[actuator].pwmRaw = frame.pwm[i];
      runtime[index].actuators[actuator].flags = frame.flags[i];
      runtime[index].actuators[actuator].online = true;
    }
    runtime[index].lastSeen = millis(); runtime[index].online = true; return;
  }
  if (id >= CAN_DISCOVERY_RESPONSE_BASE && id < CAN_DISCOVERY_RESPONSE_BASE + MAX_CABINETS &&
      message.data_length_code == sizeof(CanDiscoveryFrame)) {
    CanDiscoveryFrame frame = {}; memcpy(&frame, message.data, sizeof(frame)); rememberDiscovery(frame); return;
  }
}

void pollCan() {
  if (!canReady) return;
  twai_message_t message;
  while (twai_receive(&message, 0) == ESP_OK) processCanMessage(message);
  uint32_t alerts = 0;
  if (twai_read_alerts(&alerts, 0) == ESP_OK && (alerts & TWAI_ALERT_BUS_OFF)) twai_initiate_recovery();
  const uint32_t now = millis();
  for (uint8_t i = 0; i < objectCount; ++i) {
    if (runtime[i].online && now - runtime[i].lastSeen > OBJECT_OFFLINE_MS) {
      runtime[i].online = false;
      appendEvent(objects[i].id, static_cast<uint8_t>(Fault::CommunicationTimeout), 0, "нет связи с CAN-шкафом");
    }
  }
}

bool webAuth() {
  if (server.authenticate(WEB_USER, WEB_PASSWORD)) return true;
  server.requestAuthentication();
  return false;
}

void sendJson(const String &json) {
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json; charset=utf-8", json);
}

String objectSummaryJson(uint8_t index) {
  const ObjectConfig &object = objects[index];
  const ObjectRuntime &state = runtime[index];
  String json; json.reserve(230);
  json += F("{\"id\":"); json += object.id;
  json += F(",\"cabinetId\":"); json += object.cabinetId;
  json += F(",\"name\":\""); json += jsonEscape(object.name); json += '"';
  json += F(",\"type\":"); json += object.type;
  json += F(",\"actuatorCount\":"); json += object.actuatorCount;
  json += F(",\"capEnabledMask\":"); json += object.capEnabledMask;
  json += F(",\"online\":"); json += state.online ? F("true") : F("false");
  json += F(",\"state\":"); json += state.state;
  json += F(",\"position\":"); json += state.position;
  json += F(",\"fault\":"); json += state.fault;
  json += '}';
  return json;
}

void handleObjectsApi() {
  if (!webAuth()) return;
  String json = F("{\"objects\":["); json.reserve(160 + objectCount * 220);
  bool first = true;
  for (uint8_t i = 0; i < objectCount; ++i) {
    if (!objects[i].enabled) continue;
    if (!first) json += ','; first = false; json += objectSummaryJson(i);
  }
  json += F("]}"); sendJson(json);
}

void handleObjectApi() {
  if (!webAuth()) return;
  const int index = objectIndexById(server.arg("id").toInt());
  if (index < 0) { server.send(404, "application/json", "{\"error\":\"not_found\"}"); return; }
  const ObjectConfig &object = objects[index]; const ObjectRuntime &state = runtime[index];
  uint16_t maxCurrent = 0;
  String json = objectSummaryJson(index); json.remove(json.length() - 1);
  json += F(",\"reeds\":"); json += state.reedMask;
  json += F(",\"cap\":"); json += state.capMask;
  json += F(",\"capNoise\":"); json += (state.sensorFlags & 4u) ? F("true") : F("false");
  json += F(",\"powerGood\":"); json += (state.sensorFlags & 2u) ? F("true") : F("false");
  json += F(",\"faultActuator\":"); json += state.faultActuator;
  json += F(",\"actuators\":[");
  for (uint8_t i = 0; i < object.actuatorCount; ++i) {
    if (i) json += ','; const ActuatorRuntime &a = state.actuators[i]; maxCurrent = max(maxCurrent, a.currentMa);
    json += F("{\"online\":"); json += a.online ? F("true") : F("false");
    json += F(",\"current\":"); json += a.currentMa;
    json += F(",\"pwm\":"); json += static_cast<uint16_t>(a.pwmRaw) * 100u / 250u;
    json += F(",\"direction\":\"");
    if (!(a.flags & ACTUATOR_MOVING)) json += F("стоп"); else json += (a.flags & ACTUATOR_EXTEND) ? F("открытие") : F("закрытие");
    json += F("\",\"calibrated\":"); json += (a.flags & ACTUATOR_CALIBRATED) ? F("true") : F("false"); json += '}';
  }
  json += F("],\"maxCurrent\":"); json += maxCurrent; json += '}'; sendJson(json);
}

void handleCapConfiguration() {
  if (!webAuth()) return;
  const int index = objectIndexById(server.arg("id").toInt());
  if (index < 0) {
    server.send(404, "application/json", "{\"error\":\"not_found\"}");
    return;
  }
  objects[index].capEnabledMask = static_cast<uint8_t>(
    constrain(server.arg("mask").toInt(), 0, 255));
  saveObjects();
  sendCapConfiguration(index);
  sendJson("{\"ok\":true}");
}

void handleObjectCommand() {
  if (!webAuth()) return;
  const int index = objectIndexById(server.arg("id").toInt());
  const Command command = parseCommand(server.arg("command"));
  if (index < 0 || command == Command::None) { server.send(400, "application/json", "{\"ok\":false}"); return; }
  sendObjectCommand(index, command); appendEvent(objects[index].id, 0, 0, commandName(command));
  sendJson("{\"ok\":true}");
}

void handleCalibration() {
  if (!webAuth()) return;
  const int index = objectIndexById(server.arg("id").toInt());
  if (index < 0) { server.send(404, "application/json", "{\"ok\":false}"); return; }
  const String mode = server.arg("mode");
  if (mode != "open" && mode != "close" && mode != "full" && mode != "reset") {
    server.send(400, "application/json", "{\"ok\":false}"); return;
  }
  if (mode == "reset") {
    sendObjectCommand(index, Command::ResetCalibration);
    appendEvent(objects[index].id, 0, 0, "калибровка сброшена");
    sendJson("{\"ok\":true}");
    return;
  }
  Command command = mode == "open" ? Command::CalibrateOpen : Command::CalibrateClose;
  if (mode == "full") {
    ObjectRuntime &state = runtime[index];
    if (state.position == static_cast<uint8_t>(Position::Closed)) {
      command = Command::CalibrateOpen;
      state.pendingCalibration = Command::CalibrateClose;
    } else if (state.position == static_cast<uint8_t>(Position::Open)) {
      command = Command::CalibrateClose;
      state.pendingCalibration = Command::CalibrateOpen;
    } else {
      server.send(409, "application/json", "{\"ok\":false,\"error\":\"position_unknown\"}");
      return;
    }
    state.calibrationSawMotion = false;
  }
  sendObjectCommand(index, command); appendEvent(objects[index].id, 0, 0, commandName(command)); sendJson("{\"ok\":true}");
}

void handleStopAll() {
  if (!webAuth()) return;
  for (uint8_t i = 0; i < objectCount; ++i) if (objects[i].enabled) sendObjectCommand(i, Command::Stop);
  appendEvent(0xFF, 0, 0, "остановлены все объекты"); sendJson("{\"ok\":true}");
}

void handleEvents() {
  if (!webAuth()) return;
  String json = F("{\"events\":["); json.reserve(4000);
  for (uint8_t n = 0; n < eventSize; ++n) {
    if (n) json += ',';
    const uint8_t index = (eventHead + EVENT_COUNT - 1u - n) % EVENT_COUNT;
    const EventRecord &event = events[index];
    const int objectIndex = objectIndexById(event.objectId);
    json += F("{\"time\":\""); json += event.timestamp; json += F(" с\",\"object\":\"");
    json += objectIndex >= 0 ? jsonEscape(objects[objectIndex].name) : String("Система");
    json += F("\",\"text\":\""); json += jsonEscape(event.text); json += F("\"}");
  }
  json += F("]}"); sendJson(json);
}

void handleClearEvents() {
  if (!webAuth()) return; eventHead = eventSize = 0; sendJson("{\"ok\":true}");
}

void handleDiscoveryStart() {
  if (!webAuth()) return;
  discoveredCount = 0; sendCan(CAN_DISCOVERY_REQUEST, nullptr, 0); sendJson("{\"ok\":true}");
}

void handleDiscoveryList() {
  if (!webAuth()) return;
  String json = F("{\"nodes\":["); json.reserve(2000);
  for (uint8_t i = 0; i < discoveredCount; ++i) {
    if (i) json += ','; char uid[9]; snprintf(uid, sizeof(uid), "%08lX", static_cast<unsigned long>(discovered[i].uidHash));
    json += F("{\"uid\":\""); json += uid; json += F("\",\"configured\":"); json += discovered[i].configured ? F("true") : F("false");
    json += F(",\"cabinetId\":"); json += discovered[i].cabinetId; json += F(",\"firmware\":"); json += discovered[i].firmware; json += '}';
  }
  json += F("]}"); sendJson(json);
}

void handleProvision() {
  if (!webAuth()) return;
  CanProvisionFrame frame = {};
  frame.uidHash = strtoul(server.arg("uid").c_str(), nullptr, 16);
  frame.cabinetId = constrain(server.arg("cabinetId").toInt(), 0, 63);
  frame.objectType = constrain(server.arg("type").toInt(), 0, 2);
  frame.slaveCount = constrain(server.arg("slaveCount").toInt(), 0, 3);
  frame.flags = constrain(server.arg("reedPolarityMask").toInt(), 0, 63);
  sendCan(CAN_PROVISION_REQUEST, &frame, sizeof(frame)); sendJson("{\"ok\":true}");
}

bool isShortPulse(uint32_t value) { return value >= RF_SHORT_MIN_US && value <= RF_SHORT_MAX_US; }
bool isLongPulse(uint32_t value) { return value >= RF_LONG_MIN_US && value <= RF_LONG_MAX_US; }
bool isSyncPulse(uint32_t value) { return value >= RF_SYNC_MIN_US && value <= RF_SYNC_MAX_US; }

bool decodeRf(const uint32_t *pulses, uint16_t count, uint32_t &code) {
  bool found = false; uint32_t candidate = 0;
  for (uint16_t sync = 0; sync < count; ++sync) {
    if (!isSyncPulse(pulses[sync])) continue;
    uint32_t value = 0; uint8_t bits = 0;
    for (uint16_t i = sync + 1; i + 1 < count && bits < RF_EXPECTED_BITS; i += 2) {
      if (isShortPulse(pulses[i]) && isLongPulse(pulses[i + 1])) value <<= 1;
      else if (isLongPulse(pulses[i]) && isShortPulse(pulses[i + 1])) value = (value << 1) | 1u;
      else break;
      ++bits;
    }
    if (bits != RF_EXPECTED_BITS) continue;
    if (!found) { candidate = value; found = true; }
    else if (candidate != value) return false;
  }
  code = candidate; return found;
}

void configureRadio() {
  ELECHOUSE_cc1101.setCCMode(1); ELECHOUSE_cc1101.setModulation(2);
  ELECHOUSE_cc1101.setMHZ(RF_FREQUENCY_MHZ); ELECHOUSE_cc1101.setDeviation(0);
  ELECHOUSE_cc1101.setChannel(0); ELECHOUSE_cc1101.setChsp(199.95);
  ELECHOUSE_cc1101.setRxBW(812.50); ELECHOUSE_cc1101.setDRate(RF_DATA_RATE_KBPS);
  ELECHOUSE_cc1101.setPA(10); ELECHOUSE_cc1101.setSyncMode(0); ELECHOUSE_cc1101.setAdrChk(0);
  ELECHOUSE_cc1101.setWhiteData(0); ELECHOUSE_cc1101.setPktFormat(3); ELECHOUSE_cc1101.setLengthConfig(0);
  ELECHOUSE_cc1101.setCrc(0); ELECHOUSE_cc1101.setCRC_AF(0); ELECHOUSE_cc1101.setDcFilterOff(0);
  ELECHOUSE_cc1101.setManchester(0); ELECHOUSE_cc1101.setFEC(0);
  ELECHOUSE_cc1101.SpiWriteReg(CC1101_IOCFG0, 0x0D); ELECHOUSE_cc1101.SpiWriteReg(CC1101_IOCFG2, 0x0E);
  ELECHOUSE_cc1101.SetRx();
}

bool beginRadio() {
  ELECHOUSE_cc1101.setSpiPin(PIN_RF_SCK, PIN_RF_MISO, PIN_RF_MOSI, PIN_RF_CS);
  ELECHOUSE_cc1101.setGDO(PIN_RF_GDO0, PIN_RF_GDO2); ELECHOUSE_cc1101.Init();
  if (!ELECHOUSE_cc1101.getCC1101()) return false;
  configureRadio(); pinMode(PIN_RF_GDO0, INPUT); attachInterrupt(PIN_RF_GDO0, onRfEdge, CHANGE); return true;
}

int findRemote(uint32_t code) {
  for (uint8_t i = 0; i < remoteCount; ++i) if (remotes[i].code == code) return i;
  return -1;
}

void executeRemote(const RemoteRecord &record) {
  if (!record.enabled) return;
  for (uint8_t i = 0; i < objectCount && i < 64; ++i) {
    if (record.targetMask & (uint64_t(1) << i)) sendObjectCommand(i, static_cast<Command>(record.command));
  }
}

void handleRfCode(uint32_t code) {
  const uint32_t now = millis(); if (code == lastRfCode && now - lastRfCodeAt < RF_DEBOUNCE_MS) return;
  lastRfCode = code; lastRfCodeAt = now;
  const int existing = findRemote(code);
  if (learnMode && existing < 0 && remoteCount < REMOTE_COUNT) {
    RemoteRecord &record = remotes[remoteCount]; memset(&record, 0, sizeof(record));
    record.code = code; record.targetMask = objectCount ? 1u : 0u; record.command = static_cast<uint8_t>(Command::Stop); record.enabled = 1;
    snprintf(record.name, sizeof(record.name), "Кнопка %u", remoteCount + 1); ++remoteCount; saveRemotes(); learnMode = false;
    appendEvent(0xFF, 0, 0, "добавлена кнопка пульта");
  } else if (existing >= 0) executeRemote(remotes[existing]);
}

void pollRadio() {
  if (!radioReady) return;
  uint16_t count = 0; uint32_t local[RF_MAX_PULSES] = {};
  portENTER_CRITICAL(&rfMux);
  const bool ready = rfHadActivity && micros() - rfLastActivityUs > RF_IDLE_FRAME_US;
  if (ready) { count = rfPulseCount; if (count > RF_MAX_PULSES) count = RF_MAX_PULSES; for (uint16_t i = 0; i < count; ++i) local[i] = rfPulses[i]; rfPulseCount = 0; rfHadActivity = false; }
  portEXIT_CRITICAL(&rfMux);
  if (ready) { uint32_t code = 0; if (decodeRf(local, count, code)) handleRfCode(code); }
  if (learnMode && millis() - learnStarted > LEARN_TIMEOUT_MS) learnMode = false;
}

void handleRemotesApi() {
  if (!webAuth()) return;
  String json = F("{\"learning\":"); json += learnMode ? F("true") : F("false"); json += F(",\"remotes\":[");
  for (uint8_t i = 0; i < remoteCount; ++i) {
    if (i) json += ','; char code[9]; snprintf(code, sizeof(code), "%06lX", static_cast<unsigned long>(remotes[i].code));
    json += F("{\"index\":"); json += i; json += F(",\"code\":\""); json += code; json += F("\",\"name\":\"");
    json += jsonEscape(remotes[i].name); json += F("\",\"action\":\""); json += commandName(static_cast<Command>(remotes[i].command));
    char mask[17]; snprintf(mask, sizeof(mask), "%016llX", static_cast<unsigned long long>(remotes[i].targetMask));
    json += F("\",\"targetMask\":\""); json += mask; json += F("\"}");
  }
  json += F("]}"); sendJson(json);
}

void handleRemoteLearn() { if (!webAuth()) return; learnMode = true; learnStarted = millis(); sendJson("{\"ok\":true}"); }
void handleRemoteDelete() {
  if (!webAuth()) return; const int index = server.arg("index").toInt();
  if (index < 0 || index >= remoteCount) { server.send(400, "application/json", "{\"ok\":false}"); return; }
  for (uint8_t i = index; i + 1 < remoteCount; ++i) remotes[i] = remotes[i + 1]; --remoteCount; saveRemotes(); sendJson("{\"ok\":true}");
}

void handleRemoteSave() {
  if (!webAuth()) return;
  const int index = server.arg("index").toInt();
  const Command command = parseCommand(server.arg("command"));
  if (index < 0 || index >= remoteCount ||
      (command != Command::Open && command != Command::Close && command != Command::Stop)) {
    server.send(400, "application/json", "{\"ok\":false}"); return;
  }
  strlcpy(remotes[index].name, server.arg("name").c_str(), sizeof(remotes[index].name));
  remotes[index].targetMask = strtoull(server.arg("targetMask").c_str(), nullptr, 16);
  remotes[index].command = static_cast<uint8_t>(command);
  remotes[index].enabled = remotes[index].targetMask != 0;
  saveRemotes(); sendJson("{\"ok\":true}");
}

void handleSettingsGet() {
  if (!webAuth()) return;
  String json = F("{\"systemName\":\""); json += jsonEscape(systemName);
  json += F("\",\"canRate\":500000,\"firmware\":\""); json += FW_VERSION; json += F("\"}");
  sendJson(json);
}

void handleSettingsSave() {
  if (!webAuth()) return;
  strlcpy(systemName, server.arg("systemName").c_str(), sizeof(systemName));
  saveSystemSettings(); sendJson("{\"ok\":true}");
}

void handleSetupPage() {
  String html = F("<!doctype html><html lang='ru'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Wi-Fi</title><style>body{background:#111317;color:#eee;font:16px Arial;max-width:480px;margin:30px auto;padding:16px}label{display:block;margin-top:14px}input,button{width:100%;box-sizing:border-box;padding:12px;margin-top:6px;background:#20242a;color:#fff;border:1px solid #454b54;border-radius:6px}button{margin-top:18px}</style><h1>Настройка Wi-Fi</h1><form method='post' action='/setup/save'><label>Сеть<input name='ssid' maxlength='32'></label><label>Пароль<input name='pass' type='password' maxlength='64'></label><button>Сохранить</button></form></html>");
  server.send(200, "text/html; charset=utf-8", html);
}

void handleSetupSave() {
  strlcpy(wifiSsid, server.arg("ssid").c_str(), sizeof(wifiSsid)); strlcpy(wifiPassword, server.arg("pass").c_str(), sizeof(wifiPassword));
  saveSystemSettings(); server.send(200, "text/plain; charset=utf-8", "Сохранено. ESP32 перезагружается."); delay(300); ESP.restart();
}

void beginWeb() {
  server.on("/", HTTP_GET, [] { if (!webAuth()) return; server.send_P(200, "text/html; charset=utf-8", WEB_UI_HTML); });
  server.on("/setup", HTTP_GET, handleSetupPage); server.on("/setup/save", HTTP_POST, handleSetupSave);
  server.on("/api/objects", HTTP_GET, handleObjectsApi); server.on("/api/object", HTTP_GET, handleObjectApi);
  server.on("/api/object/command", HTTP_POST, handleObjectCommand); server.on("/api/object/calibrate", HTTP_POST, handleCalibration);
  server.on("/api/object/cap", HTTP_POST, handleCapConfiguration);
  server.on("/api/stop-all", HTTP_POST, handleStopAll); server.on("/api/events", HTTP_GET, handleEvents);
  server.on("/api/events/clear", HTTP_POST, handleClearEvents); server.on("/api/discover", HTTP_POST, handleDiscoveryStart);
  server.on("/api/discovery", HTTP_GET, handleDiscoveryList); server.on("/api/provision", HTTP_POST, handleProvision);
  server.on("/api/remotes", HTTP_GET, handleRemotesApi); server.on("/api/remotes/learn", HTTP_POST, handleRemoteLearn);
  server.on("/api/remotes/delete", HTTP_POST, handleRemoteDelete);
  server.on("/api/remotes/save", HTTP_POST, handleRemoteSave);
  server.on("/api/settings", HTTP_GET, handleSettingsGet); server.on("/api/settings", HTTP_POST, handleSettingsSave);
  server.onNotFound([] { server.send(404, "application/json", "{\"error\":\"not_found\"}"); }); server.begin();
}

void beginNetwork() {
  WiFi.mode(WIFI_STA);
  if (wifiSsid[0]) {
    WiFi.begin(wifiSsid, wifiPassword); const uint32_t started = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - started < WIFI_CONNECT_TIMEOUT_MS) delay(100);
  }
  if (WiFi.status() != WL_CONNECTED) {
    setupApMode = true; WiFi.mode(WIFI_AP); WiFi.softAP("WindowControl-Setup", SETUP_AP_PASSWORD);
  }
  MDNS.begin("window-control"); MDNS.addService("http", "tcp", 80);
}

void pollLearnButton() {
  const bool down = digitalRead(PIN_LEARN_BUTTON) == LOW; const uint32_t now = millis();
  if (down && !learnButtonWasDown) learnButtonPressedAt = now;
  if (!down && learnButtonWasDown && now - learnButtonPressedAt >= LEARN_BUTTON_LONG_MS) { learnMode = true; learnStarted = now; }
  learnButtonWasDown = down;
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.printf("\nWindow CAN ESP32 %s\n", FW_VERSION);
  pinMode(PIN_LEARN_BUTTON, INPUT_PULLUP);
  loadSystemSettings(); loadObjects(); loadRemotes();
  beginNetwork();
  beginWeb();
  canReady = beginCan();
  radioReady = beginRadio();
  appendEvent(0xFF, 0, 0, "ESP32 запущена");
  Serial.printf("CAN: %s, CC1101: %s\n", canReady ? "ready" : "offline", radioReady ? "ready" : "offline");
  Serial.printf("Network: %s, IP: %s\n", setupApMode ? "WindowControl-Setup" : wifiSsid,
                setupApMode ? WiFi.softAPIP().toString().c_str() : WiFi.localIP().toString().c_str());
  Serial.println("Web: http://192.168.4.1 (AP mode) or http://window-control.local");
}

void loop() {
  server.handleClient(); pollCan(); updateCalibrationSequences(); updateHeartbeats(); pollRadio(); pollLearnButton(); delay(1);
}
