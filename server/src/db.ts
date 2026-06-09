import { Pool, PoolClient } from "pg";
import { config } from "./config.js";

const pool = new Pool({
  connectionString: config.database.url,
  max: 4,
  idleTimeoutMillis: 30_000,
});

pool.on("error", (err) => {
  console.error("PostgreSQL pool error:", err.message);
});

/**
 * Run database migrations (idempotent — uses IF NOT EXISTS).
 * Call once on startup.
 */
export async function migrate(): Promise<void> {
  const client: PoolClient = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS sensor_nodes (
        id            SERIAL PRIMARY KEY,
        name          VARCHAR(100) NOT NULL,
        location      VARCHAR(200),
        latitude      DOUBLE PRECISION,
        longitude     DOUBLE PRECISION,
        elevation_m   NUMERIC(6,1),
        node_type     VARCHAR(20) DEFAULT 'WROOM-32',
        lora_spreading_factor INT DEFAULT 9,
        sleep_interval_s      INT DEFAULT 120,
        active        BOOLEAN DEFAULT true,
        created_at    TIMESTAMPTZ DEFAULT NOW()
      );
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS sensor_readings (
        id            BIGSERIAL PRIMARY KEY,
        node_id       INT REFERENCES sensor_nodes(id),
        received_at   TIMESTAMPTZ DEFAULT NOW(),
        measured_at   TIMESTAMPTZ,
        temperature   NUMERIC(4,1),
        humidity      NUMERIC(4,1),
        pressure      NUMERIC(6,1),
        battery_v     NUMERIC(3,2),
        rain_mm       NUMERIC(5,1),
        wind_speed    NUMERIC(4,1),
        wind_dir      INT,
        uv_index      NUMERIC(3,1),
        solar_radiation NUMERIC(5,1),
        soil_moisture NUMERIC(4,1),
        rssi          INT,
        snr           NUMERIC(4,1)
      );
    `);

    // Indexes (IF NOT EXISTS is not in PG < 9.5 for indexes, catch duplicates)
    for (const idx of [
      "CREATE INDEX IF NOT EXISTS idx_readings_node_time ON sensor_readings(node_id, received_at DESC);",
      "CREATE INDEX IF NOT EXISTS idx_readings_time ON sensor_readings(received_at DESC);",
    ]) {
      try {
        await client.query(idx);
      } catch (e: any) {
        if (!e.message?.includes("already exists")) throw e;
      }
    }

    console.log("Database migrations complete");
  } finally {
    client.release();
  }
}

export default pool;
