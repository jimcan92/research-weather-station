import { json } from '@sveltejs/kit';
import { getDB, markDBFailed } from '$lib/server/db.js';
import { sensorNodes, sensorReadings } from '$lib/server/schema.js';
import { desc, count, eq } from 'drizzle-orm';
import { getMockNodes } from '$lib/server/mock-data.js';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ url }) => {
  const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
  const limit = Math.min(50, Math.max(1, Number(url.searchParams.get('limit')) || 10));

  const db = getDB();
  if (!db) {
    console.log('API /nodes: using mock data');
    return json(getMockNodes(page, limit));
  }

  try {
    const offset = (page - 1) * limit;
    const [{ cnt }] = await db.select({ cnt: count() }).from(sensorNodes);
    const total = Number(cnt);

    const nodesList = await db
      .select({
        id: sensorNodes.id,
        name: sensorNodes.name,
        location: sensorNodes.location,
        node_type: sensorNodes.nodeType,
        active: sensorNodes.active,
        created_at: sensorNodes.createdAt,
      })
      .from(sensorNodes)
      .orderBy(sensorNodes.id)
      .limit(limit)
      .offset(offset);

    const nodes = await Promise.all(
      nodesList.map(async (n) => {
        const [latest] = await db
          .select({
            temperature: sensorReadings.temperature,
            humidity: sensorReadings.humidity,
            battery_v: sensorReadings.batteryV,
            rssi: sensorReadings.rssi,
            received_at: sensorReadings.receivedAt,
          })
          .from(sensorReadings)
          .where(eq(sensorReadings.nodeId, n.id))
          .orderBy(desc(sensorReadings.receivedAt))
          .limit(1);
        return { ...n, last_reading: latest || null };
      })
    );

    return json({ nodes, total, page, limit });
  } catch (err: any) {
    console.error('API /nodes DB error, falling back to mock:', err.message);
    markDBFailed();
    return json(getMockNodes(page, limit));
  }
};
