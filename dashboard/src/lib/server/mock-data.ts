// Mock data for when PostgreSQL is not running
// Realistic weather data for a tropical location (Philippines)

const now = new Date();

export const MOCK_NODES = [
  { id: 1, name: 'Node 1 — Rooftop', location: 'Main building roof', node_type: 'WROOM-32', active: true, created_at: new Date('2025-12-01').toISOString() },
  { id: 2, name: 'Node 2 — Garden', location: 'Back garden weather hut', node_type: 'C3', active: true, created_at: new Date('2026-01-15').toISOString() },
  { id: 3, name: 'Node 3 — Field Station', location: 'East field, near irrigation', node_type: 'WROOM-32', active: false, created_at: new Date('2026-03-10').toISOString() },
];

function reading(minutesAgo: number, nodeId: number, tempOffset = 0) {
  return {
    id: nodeId * 1000 + minutesAgo,
    node_id: nodeId,
    node_name: MOCK_NODES[nodeId - 1]?.name || `Node ${nodeId}`,
    temperature: String((28.5 + tempOffset + Math.sin(minutesAgo / 60) * 3).toFixed(1)),
    humidity: String((75 + Math.cos(minutesAgo / 45) * 10).toFixed(0)),
    pressure: String((1012 + Math.sin(minutesAgo / 120) * 2).toFixed(1)),
    battery_v: String((3.8 - minutesAgo / 5000).toFixed(2)),
    wind_speed: String((2 + Math.abs(Math.sin(minutesAgo / 30)) * 5).toFixed(1)),
    wind_dir: Math.round(180 + Math.sin(minutesAgo / 20) * 90),
    rain_mm: minutesAgo < 120 ? String((Math.random() * 1.5).toFixed(1)) : '0.0',
    soil_moisture: String((42 + Math.sin(minutesAgo / 200) * 5).toFixed(1)),
    rssi: -50 - Math.round(Math.random() * 30),
    snr: String((7 + Math.random() * 5).toFixed(1)),
    received_at: new Date(now.getTime() - minutesAgo * 60000).toISOString(),
    measured_at: new Date(now.getTime() - (minutesAgo + 1) * 60000).toISOString(),
  };
}

export function getMockReadings(page = 1, limit = 20) {
  const total = 500;
  const offset = (page - 1) * limit;
  const all: ReturnType<typeof reading>[] = [];
  for (let i = 0; i < Math.min(limit, total - offset); i++) {
    const minutesAgo = offset + i * 2 + Math.floor(Math.random() * 3);
    const nodeId = (i % 3) + 1;
    all.push(reading(minutesAgo, nodeId, (nodeId - 1) * 0.5));
  }
  return { readings: all, total };
}

export function getMockOverview() {
  const latestReadings = [
    reading(1, 1, 0),
    reading(3, 2, 0.5),
    reading(2, 1, 0),
    reading(6, 3, 1),
    reading(5, 2, 0.5),
  ];

  const todayReadings = Array.from({ length: 48 }, (_, i) => reading(i * 5, (i % 2) + 1, (i % 2) * 0.5));
  const temps = todayReadings.map(r => Number(r.temperature));
  const rains = todayReadings.map(r => Number(r.rain_mm));

  return {
    totalNodes: 3,
    activeNodes: 2,
    latestReadings,
    todayStats: {
      readings: 48,
      avgTemp: (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1),
      totalRain: rains.reduce((a, b) => a + b, 0).toFixed(1),
    },
  };
}

export function getMockNodes(page = 1, limit = 10) {
  const nodes = MOCK_NODES.map((n, i) => ({
    ...n,
    last_reading: reading(i * 2 + 1, n.id, i * 0.5),
  }));
  return { nodes, total: nodes.length, page, limit };
}

export function getMockNodeDetail(nodeId: number) {
  const node = MOCK_NODES.find(n => n.id === nodeId);
  if (!node) return null;
  const recentReadings = Array.from({ length: 20 }, (_, i) => reading(i * 5 + 1, nodeId, (nodeId - 1) * 0.5));
  return { node, recentReadings };
}
