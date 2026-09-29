import { json } from '@sveltejs/kit';
import { getDB, markDBFailed } from '$lib/server/db.js';
import { sensorNodes, sensorReadings } from '$lib/server/schema.js';
import { desc, eq } from 'drizzle-orm';
import { getMockNodeDetail } from '$lib/server/mock-data.js';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
  const nodeId = Number(params.id);
  if (isNaN(nodeId)) {
    return json({ error: 'Invalid node ID' }, { status: 400 });
  }

  const db = getDB();
  if (!db) {
    console.log(`API /nodes/${nodeId}: using mock data`);
    const detail = getMockNodeDetail(nodeId);
    if (!detail) return json({ error: 'Node not found' }, { status: 404 });
    return json(detail);
  }

  try {
    const [node] = await db
      .select()
      .from(sensorNodes)
      .where(eq(sensorNodes.id, nodeId));

    if (!node) {
      return json({ error: 'Node not found' }, { status: 404 });
    }

    const recentReadings = await db
      .select({
        id: sensorReadings.id,
        temperature: sensorReadings.temperature,
        humidity: sensorReadings.humidity,
        pressure: sensorReadings.pressure,
        battery_v: sensorReadings.batteryV,
        wind_speed: sensorReadings.windSpeed,
        wind_dir: sensorReadings.windDir,
        rain_mm: sensorReadings.rainMm,
        soil_moisture: sensorReadings.soilMoisture,
        rssi: sensorReadings.rssi,
        snr: sensorReadings.snr,
        received_at: sensorReadings.receivedAt,
      })
      .from(sensorReadings)
      .where(eq(sensorReadings.nodeId, nodeId))
      .orderBy(desc(sensorReadings.receivedAt))
      .limit(50);

    return json({ node, recentReadings });
  } catch (err: any) {
    console.error(`API /nodes/${nodeId} DB error, falling back to mock:`, err.message);
    markDBFailed();
    const detail = getMockNodeDetail(nodeId);
    if (!detail) return json({ error: 'Node not found' }, { status: 404 });
    return json(detail);
  }
};
