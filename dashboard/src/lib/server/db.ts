import { drizzle } from 'drizzle-orm/node-postgres';
import pg from 'pg';
import * as schema from './schema.js';
import { env } from '$env/dynamic/private';

let _pool: pg.Pool | null = null;
let _db: ReturnType<typeof drizzle> | null = null;
let _initFailed = false;

export function getDB() {
  if (_db) return _db;
  if (_initFailed) return null;

  try {
    _pool = new pg.Pool({
      connectionString: env.DATABASE_URL || 'postgresql://weather_ingestor:***@localhost:5432/weather_station',
      max: 4,
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 3000,
    });
    _db = drizzle(_pool, { schema });
    return _db;
  } catch (err: any) {
    _initFailed = true;
    return null;
  }
}

export function markDBFailed() {
  _initFailed = true;
  _db = null;
  if (_pool) {
    _pool.end().catch(() => {});
    _pool = null;
  }
}

// Legacy export — lazy proxy
export const db = new Proxy({} as ReturnType<typeof drizzle>, {
  get(_, prop) {
    const real = getDB();
    if (!real) throw new Error('Database not available');
    return (real as any)[prop];
  },
});

export { schema };
