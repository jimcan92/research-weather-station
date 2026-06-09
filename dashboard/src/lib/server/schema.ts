import { pgTable, serial, varchar, doublePrecision, numeric, integer, boolean, timestamp, bigserial, date, uniqueIndex } from 'drizzle-orm/pg-core';

// ── Sensor Nodes ───────────────────────────────────────────────────
export const sensorNodes = pgTable('sensor_nodes', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  location: varchar('location', { length: 200 }),
  latitude: doublePrecision('latitude'),
  longitude: doublePrecision('longitude'),
  elevationM: numeric('elevation_m', { precision: 6, scale: 1 }),
  nodeType: varchar('node_type', { length: 20 }).default('WROOM-32'),
  loraSpreadingFactor: integer('lora_spreading_factor').default(9),
  sleepIntervalS: integer('sleep_interval_s').default(120),
  active: boolean('active').default(true),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow(),
});

// ── Sensor Readings ────────────────────────────────────────────────
export const sensorReadings = pgTable('sensor_readings', {
  id: bigserial('id', { mode: 'number' }).primaryKey(),
  nodeId: integer('node_id').notNull().references(() => sensorNodes.id),
  receivedAt: timestamp('received_at', { withTimezone: true }).defaultNow(),
  measuredAt: timestamp('measured_at', { withTimezone: true }),
  temperature: numeric('temperature', { precision: 4, scale: 1 }),
  humidity: numeric('humidity', { precision: 4, scale: 1 }),
  pressure: numeric('pressure', { precision: 6, scale: 1 }),
  batteryV: numeric('battery_v', { precision: 3, scale: 2 }),
  rainMm: numeric('rain_mm', { precision: 5, scale: 1 }),
  windSpeed: numeric('wind_speed', { precision: 4, scale: 1 }),
  windDir: integer('wind_dir'),
  uvIndex: numeric('uv_index', { precision: 3, scale: 1 }),
  solarRadiation: numeric('solar_radiation', { precision: 5, scale: 1 }),
  soilMoisture: numeric('soil_moisture', { precision: 4, scale: 1 }),
  rssi: integer('rssi'),
  snr: numeric('snr', { precision: 4, scale: 1 }),
});

// ── Daily Aggregates ───────────────────────────────────────────────
export const sensorDaily = pgTable('sensor_daily', {
  id: bigserial('id', { mode: 'number' }).primaryKey(),
  nodeId: integer('node_id').notNull().references(() => sensorNodes.id),
  date: date('date').notNull(),
  tempMin: numeric('temp_min', { precision: 4, scale: 1 }),
  tempMax: numeric('temp_max', { precision: 4, scale: 1 }),
  tempAvg: numeric('temp_avg', { precision: 4, scale: 1 }),
  humidityAvg: numeric('humidity_avg', { precision: 4, scale: 1 }),
  pressureAvg: numeric('pressure_avg', { precision: 6, scale: 1 }),
  rainTotal: numeric('rain_total', { precision: 5, scale: 1 }),
  windMax: numeric('wind_max', { precision: 4, scale: 1 }),
  windDirAvg: numeric('wind_dir_avg', { precision: 4, scale: 1 }),
  readingCount: integer('reading_count'),
}, (table) => ({
  nodeDateUnique: uniqueIndex('idx_daily_node_date').on(table.nodeId, table.date),
}));
