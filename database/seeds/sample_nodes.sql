-- Sample sensor nodes for testing
INSERT INTO sensor_nodes (name, location, latitude, longitude, node_type)
VALUES
  ('Node 1 — Rooftop',  'Main building rooftop',  14.5995, 120.9842, 'WROOM-32'),
  ('Node 2 — Garden',   'Back garden weather hut', 14.6001, 120.9835, 'C3')
ON CONFLICT DO NOTHING;
