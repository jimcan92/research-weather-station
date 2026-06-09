/**
 * lora.h — LoRa radio wrapper (SX1276/SX1278 via RadioLib)
 */

#ifndef LORA_H
#define LORA_H

#include <RadioLib.h>
#include "config.h"

#ifdef __cplusplus

/** Initialize the LoRa module. Returns true on success. */
bool loraInit();

/** Transmit a buffer. Returns true on success. */
bool loraSend(uint8_t* data, size_t len);

/** Transmit a String (JSON mode). Returns true on success. */
bool loraSend(const String& str);

/** Put radio to sleep to save power. */
void loraSleep();

/** Get last RSSI in dBm. */
float loraRSSI();

/** Get last SNR in dB. */
float loraSNR();

#endif // __cplusplus
#endif // LORA_H
