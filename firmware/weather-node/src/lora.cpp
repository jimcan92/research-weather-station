/**
 * lora.cpp — E22-900T22D transparent UART implementation
 */

#include "lora.h"
#include <math.h>

static HardwareSerial e22Serial(2);
static bool e22Ready = false;
static bool e22PinsInitialized = false;

static bool waitAuxHigh(uint32_t timeoutMs) {
  const uint32_t started = millis();
  while (digitalRead(PIN_E22_AUX) == LOW) {
    if (millis() - started >= timeoutMs) {
      Serial.println("[E22] AUX timeout");
      return false;
    }
    delay(1);
  }
  // Ebyte recommends a short guard time after AUX rises.
  delay(2);
  return true;
}

static void setE22Mode(bool m0, bool m1) {
  digitalWrite(PIN_E22_M0, m0 ? HIGH : LOW);
  digitalWrite(PIN_E22_M1, m1 ? HIGH : LOW);
  delay(E22_MODE_SETTLE_MS);
}

bool loraInit() {
  pinMode(PIN_E22_M0, OUTPUT);
  pinMode(PIN_E22_M1, OUTPUT);
  pinMode(PIN_E22_AUX, INPUT_PULLUP);
  e22PinsInitialized = true;

  // HardwareSerial::begin(baud, config, rxPin, txPin)
  // ESP RX is wired to E22 TXD (GPIO7); ESP TX is wired to E22 RXD (GPIO6).
  e22Serial.begin(E22_UART_BAUD, SERIAL_8N1, PIN_E22_TXD, PIN_E22_RXD);

  // Mode 0: transparent transmission.
  setE22Mode(false, false);
  e22Ready = waitAuxHigh(E22_AUX_TIMEOUT_MS);

  if (!e22Ready) {
    Serial.println("[E22] Init failed: AUX did not become ready");
    return false;
  }

  Serial.printf(
      "[E22] Ready: UART=%d, M0=%d, M1=%d, RX=%d, TX=%d, AUX=%d\n",
      E22_UART_BAUD, PIN_E22_M0, PIN_E22_M1,
      PIN_E22_TXD, PIN_E22_RXD, PIN_E22_AUX);
  return true;
}

bool loraSend(const uint8_t* data, size_t len) {
  if (!e22Ready || data == nullptr || len == 0) {
    return false;
  }
  if (!waitAuxHigh(E22_AUX_TIMEOUT_MS)) {
    return false;
  }

  const size_t written = e22Serial.write(data, len);
  e22Serial.flush();
  if (written != len) {
    Serial.printf("[E22] UART short write: %u/%u bytes\n",
                  static_cast<unsigned>(written),
                  static_cast<unsigned>(len));
    return false;
  }

  // AUX may briefly stay high until the module consumes the UART buffer.
  delay(3);
  if (!waitAuxHigh(E22_AUX_TIMEOUT_MS)) {
    return false;
  }

  Serial.printf("[E22] TX queued: %u bytes\n", static_cast<unsigned>(len));
  return true;
}

bool loraSend(const String& str) {
  return loraSend(reinterpret_cast<const uint8_t*>(str.c_str()), str.length());
}

void loraSleep() {
  if (!e22PinsInitialized) {
    return;
  }
  if (e22Ready) {
    waitAuxHigh(E22_AUX_TIMEOUT_MS);
  }
  setE22Mode(true, true);  // Mode 3: sleep/config
  e22Ready = false;
  Serial.println("[E22] Sleep mode");
}

float loraRSSI() {
  return NAN;
}

float loraSNR() {
  return NAN;
}
