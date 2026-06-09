/**
 * lora.cpp — LoRa radio implementation
 */

#include "lora.h"

static SX1276* radio = nullptr;

bool loraInit() {
  SPI.begin(PIN_LORA_SCK, PIN_LORA_MISO, PIN_LORA_MOSI, PIN_LORA_NSS);

  radio = new SX1276(
    new Module(PIN_LORA_NSS, PIN_LORA_DIO0, PIN_LORA_RST)
  );

  int state = radio->begin(
    LORA_FREQ,
    LORA_BW,
    LORA_SF,
    LORA_CR,
    LORA_SYNC_WORD,
    LORA_POWER,
    LORA_PREAMBLE
  );

  if (state != RADIOLIB_ERR_NONE) {
    Serial.print("LoRa init failed, code: ");
    Serial.println(state);
    return false;
  }

  Serial.println("LoRa ready");
  return true;
}

bool loraSend(uint8_t* data, size_t len) {
  if (!radio) return false;

  int state = radio->transmit(data, len);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.print("LoRa TX failed, code: ");
    Serial.println(state);
    return false;
  }

  Serial.print("TX ok, ");
  Serial.print(len);
  Serial.print(" bytes, RSSI: ");
  Serial.print(loraRSSI());
  Serial.print(" dBm, SNR: ");
  Serial.print(loraSNR());
  Serial.println(" dB");
  return true;
}

bool loraSend(const String& str) {
  return loraSend((uint8_t*)str.c_str(), str.length());
}

void loraSleep() {
  if (radio) {
    radio->sleep();
  }
}

float loraRSSI() {
  return radio ? radio->getRSSI() : 0.0;
}

float loraSNR() {
  return radio ? radio->getSNR() : 0.0;
}
