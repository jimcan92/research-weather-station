import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db.js';
import { sensorNodes, sensorReadings } from '$lib/server/schema.js';
import { sql, desc, count, eq } from 'drizzle-orm';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ url }) => {
  const page = Math.max(1, Number(url.searchParams.get('page')) || 1);
  const limit = Math.min(50, Math.max(1, Number(url.searchParams.get('limit')) || 10));
  const offset = (page - 1) * limit;

  try {
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

    // Attach latest reading for each node
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
    console.error('API /nodes error:', err);
    return json({ error: err.message }, { status: 500 });
  }
};
