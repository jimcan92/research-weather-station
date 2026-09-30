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

/** Scan I2C bus and print detected device addresses to Serial. */
void sensorsScanI2C();

/** Read all enabled sensors into a SensorData struct. */
SensorData sensorsRead(uint16_t nodeId);

/** Read battery voltage (calibrated via analogReadMilliVolts). */
float readBatteryVoltage();

/**
 * Averaged battery ADC pin millivolts, outlier-rejected and cached for
 * BAT_ADC_CACHE_MS so every caller in one read cycle sees the same sample.
 */
uint32_t readBatteryRawMilliVolts();

/** Read capacitive soil moisture percentage (0-100%). */
uint8_t readSoilMoisture();

/** Read RS485 wind speed in m/s (returns -1.0 on timeout/error). */
float readRS485WindSpeed();

/** Read RS485 wind direction in degrees (0-360, returns 0xFFFF on error). */
uint16_t readRS485WindDirection();

/** Get rain tips accumulated since last read (resets counter). */
uint16_t getRainTips();

/** Get current MOSFET power switch state. */
bool getMosfetState();

/** Set MOSFET power switch state. */
void setMosfetState(bool on);

/** Read BME280 temperature, humidity, pressure. */
float readBmeTemp();
float readBmeHum();
float readBmePress();

/** Read DS18B20 temperature. */
float readDS18B20Temp();

/** Check if BME280 or BMP280 is currently operational. */
bool isBmeWorking();

#endif // __cplusplus
#endif // SENSORS_H
