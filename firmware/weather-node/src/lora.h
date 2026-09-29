/**
 * lora.h — E22-900T22D UART LoRa wrapper
 *
 * The E22 runs in transparent UART mode:
 *   M0=LOW, M1=LOW  -> normal transmit/receive
 *   M0=HIGH, M1=HIGH -> sleep/config mode
 */

#ifndef LORA_H
#define LORA_H

#include <Arduino.h>
#include "config.h"

/** Initialize UART, mode pins and AUX. Returns true when the module is ready. */
bool loraInit();

/** Transmit a raw buffer in transparent mode. Returns true on success. */
bool loraSend(const uint8_t* data, size_t len);

/** Transmit a String (JSON mode). Returns true on success. */
bool loraSend(const String& str);

/** Put E22 into mode 3 (sleep/config) before ESP32 deep sleep. */
void loraSleep();

/** E22 transparent mode does not expose per-packet RSSI/SNR in this driver. */
float loraRSSI();
float loraSNR();

#endif // LORA_H
