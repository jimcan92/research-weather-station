import pool from "./db.js";

/**
 * Expected JSON payload from ESP32 nodes (matches firmware packet.h):
 *
 * {
 *   "n":  1,       // node_id
 *   "t":  29.4,    // temperature °C
 *   "h":  78.2,    // humidity %
 *   "p":  1013.2,  // pressure hPa
 *   "b":  3.72,    // battery volts
 *   "r":  5,       // rain tips since last TX
 *   "ws": 2.1,     // wind speed m/s
 *   "wd": 180,     // wind direction degrees
 *   "sm": 42,      // soil moisture %
 *   "uv": 6.5,     // UV index (future)
 *   "sr": 650      // solar radiation W/m² (future)
 * }
 */

interface SensorPayload {
  n: number;   // node_id
  t?: number;  // temperature
  h?: number;  // humidity
  p?: number;  // pressure
  b?: number;  // battery
  r?: number;  // rain tips
  ws?: number; // wind speed
  wd?: number; // wind direction
  sm?: number; // soil moisture
  uv?: number; // UV index
  sr?: number; // solar radiation
}

/** Convert rain tips to mm using calibrated tip volume. */
const TIP_MM = 0.2794; // mm per tip — adjust per rain gauge

/**
 * Parse and insert a sensor reading into PostgreSQL.
 * Returns the inserted row id, or null on failure.
 */
export async function ingestPacket(
  rawPayload: string,
  rssi?: number,
  snr?: number
): Promise<number | null> {
  let data: SensorPayload;

  // Parse JSON
  try {
    data = JSON.parse(rawPayload);
  } catch {
    console.warn("Invalid JSON payload:", rawPayload.slice(0, 120));
    return null;
  }

  // Validate required field
  if (!data.n || typeof data.n !== "number") {
    console.warn("Payload missing valid node_id (n):", rawPayload.slice(0, 120));
    return null;
  }

  try {
    const result = await pool.query(
      `INSERT INTO sensor_readings
       (node_id, temperature, humidity, pressure, battery_v,
        rain_mm, wind_speed, wind_dir, soil_moisture,
        uv_index, solar_radiation, rssi, snr)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
       RETURNING id`,
      [
        data.n,
        data.t ?? null,
        data.h ?? null,
        data.p ?? null,
        data.b ?? null,
        data.r != null ? data.r * TIP_MM : null,
        data.ws ?? null,
        data.wd ?? null,
        data.sm ?? null,
        data.uv ?? null,
        data.sr ?? null,
        rssi ?? null,
        snr ?? null,
      ]
    );

    console.log(
      `Inserted reading #${result.rows[0].id} | node=${data.n} | ` +
        `temp=${data.t}°C | hum=${data.h}% | bat=${data.b}V`
    );

    return result.rows[0].id;
  } catch (err: any) {
    console.error("Insert failed:", err.message);
    return null;
  }
}
