import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db.js';
import { sensorReadings, sensorNodes } from '$lib/server/schema.js';
import { sql, desc, count, avg, sum } from 'drizzle-orm';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ url }) => {
  const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
  const limit = Math.min(100, Math.max(1, Number(url.searchParams.get('limit')) || 20));
  const offset = (page - 1) * limit;

  try {
    // Total count
    const [{ cnt }] = await db.select({ cnt: count() }).from(sensorReadings);
    const total = Number(cnt);

    // Paginated readings
    const readings = await db
      .select({
        id: sensorReadings.id,
        node_id: sensorReadings.nodeId,
        node_name: sensorNodes.name,
        temperature: sensorReadings.temperature,
        humidity: sensorReadings.humidity,
        pressure: sensorReadings.pressure,
        battery_v: sensorReadings.batteryV,
        wind_speed: sensorReadings.windSpeed,
        wind_dir: sensorReadings.windDir,
        rain_mm: sensorReadings.rainMm,
        soil_moisture: sensorReadings.soilMoisture,
        rssi: sensorReadings.rssi,
        received_at: sensorReadings.receivedAt,
      })
      .from(sensorReadings)
      .leftJoin(sensorNodes, sql`${sensorReadings.nodeId} = ${sensorNodes.id}`)
      .orderBy(desc(sensorReadings.receivedAt))
      .limit(limit)
      .offset(offset);

    // Overview stats (only for first page)
    let totalNodes = 0;
    let activeNodes = 0;
    let latestReadings: any[] = [];
    let todayStats = { readings: 0, avgTemp: '—', totalRain: '—' };

    if (page === 1) {
      const [nodesCount] = await db.select({ cnt: count() }).from(sensorNodes);
      totalNodes = Number(nodesCount.cnt);

      const [activeCount] = await db
        .select({ cnt: count() })
        .from(sensorNodes)
        .where(sql`${sensorNodes.active} = true`);
      activeNodes = Number(activeCount.cnt);

      latestReadings = await db
        .select({
          node_id: sensorReadings.nodeId,
          node_name: sensorNodes.name,
          temperature: sensorReadings.temperature,
          humidity: sensorReadings.humidity,
          pressure: sensorReadings.pressure,
          battery_v: sensorReadings.batteryV,
          wind_speed: sensorReadings.windSpeed,
          rain_mm: sensorReadings.rainMm,
          received_at: sensorReadings.receivedAt,
        })
        .from(sensorReadings)
        .leftJoin(sensorNodes, sql`${sensorReadings.nodeId} = ${sensorNodes.id}`)
        .orderBy(desc(sensorReadings.receivedAt))
        .limit(5);

      // Today's stats
      const todayStart = new Date();
      todayStart.setHours(0, 0, 0, 0);

      const [today] = await db
        .select({
          readings: count(),
          avgTemp: avg(sensorReadings.temperature),
          totalRain: sum(sensorReadings.rainMm),
        })
        .from(sensorReadings)
        .where(sql`${sensorReadings.receivedAt} >= ${todayStart.toISOString()}`);

      todayStats = {
        readings: Number(today.readings),
        avgTemp: today.avgTemp ? Number(today.avgTemp).toFixed(1) : '—',
        totalRain: today.totalRain ? Number(today.totalRain).toFixed(1) : '0.0',
      };
    }

    return json({
      readings,
      total,
      page,
      limit,
      totalNodes,
      activeNodes,
      latestReadings,
      todayStats,
    });
  } catch (err: any) {
    console.error('API /readings error:', err);
    return json({ error: err.message }, { status: 500 });
  }
};
