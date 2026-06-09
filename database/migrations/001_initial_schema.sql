-- 001_initial_schema.sql
-- Run: psql -d weather_station -f database/migrations/001_initial_schema.sql

BEGIN;

-- ── Sensor Nodes Registry ──────────────────────────────────────────
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

-- ── Sensor Readings ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sensor_readings (
  id            BIGSERIAL PRIMARY KEY,
  node_id       INT NOT NULL REFERENCES sensor_nodes(id),
  received_at   TIMESTAMPTZ DEFAULT NOW(),
  measured_at   TIMESTAMPTZ,
  temperature   NUMERIC(4,1),       -- °C
  humidity      NUMERIC(4,1),       -- %
  pressure      NUMERIC(6,1),       -- hPa
  battery_v     NUMERIC(3,2),       -- V
  rain_mm       NUMERIC(5,1),       -- mm
  wind_speed    NUMERIC(4,1),       -- m/s
  wind_dir      INT,                -- degrees (0-360)
  uv_index      NUMERIC(3,1),
  solar_radiation NUMERIC(5,1),     -- W/m²
  soil_moisture NUMERIC(4,1),       -- %
  rssi          INT,                -- dBm
  snr           NUMERIC(4,1)        -- dB
);

-- ── Indexes ───────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_readings_node_time
  ON sensor_readings(node_id, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_readings_time
  ON sensor_readings(received_at DESC);

-- ── Daily Aggregates (for fast Grafana dashboards) ────────────────
CREATE TABLE IF NOT EXISTS sensor_daily (
  id            BIGSERIAL PRIMARY KEY,
  node_id       INT NOT NULL REFERENCES sensor_nodes(id),
  date          DATE NOT NULL,
  temp_min      NUMERIC(4,1),
  temp_max      NUMERIC(4,1),
  temp_avg      NUMERIC(4,1),
  humidity_avg  NUMERIC(4,1),
  pressure_avg  NUMERIC(6,1),
  rain_total    NUMERIC(5,1),
  wind_max      NUMERIC(4,1),
  wind_dir_avg  NUMERIC(4,1),
  reading_count INT,
  UNIQUE(node_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_node_date
  ON sensor_daily(node_id, date DESC);

COMMIT;
