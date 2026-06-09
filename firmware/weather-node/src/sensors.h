/**
 * sensors.h — Sensor interface abstraction
 *
 * Supports: BME280, DS18B20, rain gauge, anemometer,
 *           wind vane, soil moisture (capacitive).
 */

#ifndef SENSORS_H
#define SENSORS_H

#include "config.h"

#ifdef __cplusplus

#include <Arduino.h>
#include "packet.h"

/** One-time sensor initialization. Call once in setup(). */
void sensorsInit();

/** Power on all sensors (via MOSFET gate). */
void sensorsPowerOn();

/** Power off all sensors. */
void sensorsPowerOff();

/** Read all enabled sensors into a SensorData struct. */
SensorData sensorsRead(uint16_t nodeId);

/** Get rain tips accumulated since last read (resets counter). */
uint16_t getRainTips();

/** Get anemometer pulse count since last read (resets counter). */
uint16_t getWindPulses();

#endif // __cplusplus
#endif // SENSORS_H
