# Weather Station Sensor Network

ESP32 field sensors → LoRa 915 MHz → Raspberry Pi gateway → Ryzen 5 server (PostgreSQL + Grafana)

## Architecture

```
ESP32 Nodes (solar + battery)
  │  Sensors: BME280, DS18B20, rain gauge, anemometer, wind vane, soil moisture
  │  Radio:   SX1276/SX1278 LoRa @ 915 MHz (PH ISM band)
  │  Firmware: PlatformIO / Arduino framework
  │
  ▼ LoRa packets (JSON)
Raspberry Pi Gateway (near server)
  │  HAT:      LoRa concentrator or single-channel SX1276
  │  Software: Python MQTT bridge (lora_gateway.py)
  │
  ▼ MQTT (mosquitto)
Ryzen 5 Server (Ubuntu)
  │  Ingestor: Node.js/TypeScript → PostgreSQL
  │  Dashboard: Grafana (future: SvelteKit)
  └── PostgreSQL: raw readings + daily aggregates
```

## Repository Structure

```
weather-station/
├── firmware/weather-node/   # ESP32 PlatformIO project
│   └── src/
│       ├── main.cpp         # Entry point, deep sleep loop
│       ├── config.h         # Per-node config (pins, ID, calibration)
│       ├── sensors.cpp      # Sensor reading (BME280, DS18B20, etc.)
│       ├── lora.cpp         # LoRa radio wrapper (RadioLib)
│       └── packet.cpp       # Packet serialization (JSON/binary)
├── gateway/                 # RPi LoRa → MQTT bridge
│   ├── lora_gateway.py      # Main gateway script
│   ├── config.yaml          # MQTT + LoRa config
│   └── requirements.txt
├── server/                  # MQTT → PostgreSQL ingestor
│   └── src/
│       ├── index.ts         # MQTT subscriber entry point
│       ├── db.ts            # PostgreSQL connection + auto-migrate
│       ├── ingest.ts        # Packet parsing + insert
│       └── config.ts        # Environment config
├── database/
│   ├── migrations/          # SQL migration files
│   └── seeds/               # Sample data
├── docker-compose.yml       # Local dev: Postgres + Mosquitto + Grafana
├── mosquitto.conf           # MQTT broker config
├── grafana/                 # Grafana provisioning
├── docs/                    # Architecture, wiring, deployment guides
└── weather-station.code-workspace  # VS Code multi-root workspace
```

## Quick Start (Development)

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts: PostgreSQL (5432), Mosquitto MQTT (1883), Grafana (3000).

### 2. Install server dependencies

```bash
cd server
cp .env.example .env
npm install
npm run dev
```

### 3. Test the MQTT pipeline

```bash
# Publish a test packet
mosquitto_pub -t "weather/raw" -m '{"n":1,"t":29.4,"h":78,"p":1013,"b":3.8,"r":2,"ws":1.5,"wd":180,"sm":42}'

# Check PostgreSQL
psql -h localhost -U weather_ingestor -d weather_station \
  -c "SELECT * FROM sensor_readings ORDER BY received_at DESC LIMIT 5;"
```

### 4. Gateway setup (on Raspberry Pi)

```bash
cd gateway
sudo apt install python3-pip
pip3 install -r requirements.txt
# Edit config.yaml: set mqtt.broker to your server IP
sudo python3 lora_gateway.py
```

### 5. ESP32 node setup

```bash
# Install PlatformIO: https://platformio.org/install
cd firmware/weather-node
# Edit src/config.h: set NODE_ID, verify pin assignments
pio run -t upload -t monitor
```

## VS Code Remote Development

Open `weather-station.code-workspace` via VS Code Remote SSH.
The workspace groups all sub-projects into separate root folders.

## Production Notes

- Change PostgreSQL + Mosquitto passwords (use `.env`, never commit `.env`)
- Enable Mosquitto authentication: `mosquitto_passwd` + set `allow_anonymous false`
- Set `SLEEP_INTERVAL_S` to 120-300 for production nodes (5s for testing only)
- Use a LoRa concentrator HAT (SX1302) on the RPi for >10 nodes
- Set up systemd services for the ingestor and gateway for auto-start

## License

MIT — Jimboy Cantila, 2025
