import { drizzle } from 'drizzle-orm/node-postgres';
import pg from 'pg';
import * as schema from './schema.js';
import { env } from '$env/dynamic/private';

const pool = new pg.Pool({
  connectionString: env.DATABASE_URL || 'postgresql://weather_ingestor:changeme@localhost:5432/weather_station',
  max: 4,
  idleTimeoutMillis: 30_000,
});

export const db = drizzle(pool, { schema });

export { schema };
