# Deployment Guide

## Hardware Checklist

### Per ESP32 Node
- [ ] ESP32-S3 N16R8 dev board
- [ ] E22-900T22D UART LoRa module + 900/915 MHz antenna (SMA)
- [ ] 470µF/10V + 100nF capacitors at E22 VCC/GND
- [ ] BME280 sensor module
- [ ] DS18B20 waterproof probe (optional, secondary temp)
- [ ] Rain gauge (tipping bucket)
- [ ] Anemometer (cup type)
- [ ] Wind vane (potentiometer type)
- [ ] Capacitive soil moisture sensor v1.2
- [ ] Solar panel (5-10W, 18V)
- [ ] 18650 Li-Ion battery (3.7V, 2500-3500mAh)
- [ ] CN3791 solar charge controller
- [ ] HT7333-A 3.3V LDO regulator
- [ ] P-channel MOSFET (for sensor power bus)
- [ ] Resistors: 100kΩ, 220kΩ, 4.7kΩ
- [ ] IP65 weatherproof enclosure
- [ ] Mounting hardware (pole, brackets, cable glands)

### Raspberry Pi Gateway
- [ ] Raspberry Pi (3B+, 4, or 5)
- [ ] MicroSD card (32GB+)
- [ ] LoRa HAT (single SX1276 or SX1302 concentrator)
- [ ] 915 MHz antenna (outdoor, high-gain)
- [ ] Power supply (5V 3A)
- [ ] Ethernet cable (connect to same network as server)

### Server
- [ ] Ryzen 5 + Ubuntu Server
- [ ] Static IP on local network
- [ ] Docker + Docker Compose installed

## Server Setup

### 1. Install Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Log out and back in
```

### 2. Clone and Start Services

```bash
cd /home/jimcan/dev/projects
git clone <repo-url> weather-station
cd weather-station

# Start PostgreSQL + Mosquitto + Grafana
docker compose up -d

# Verify
docker compose ps
```

### 3. Install Server Ingestor

```bash
cd server
cp .env.example .env
# Edit .env with real passwords
npm install
npm run build
npm start
```

### 4. Systemd Service (for auto-start)

Create `/etc/systemd/system/weather-ingestor.service`:

```ini
[Unit]
Description=Weather Station Ingestor
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=jimcan
WorkingDirectory=/home/jimcan/dev/projects/weather-station/server
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now weather-ingestor
```

## Raspberry Pi Gateway Setup

### 1. Flash OS

Use Raspberry Pi Imager: Raspberry Pi OS Lite (64-bit).

### 2. Enable SPI

```bash
sudo raspi-config
# Interface Options → SPI → Enable
# Reboot
```

### 3. Deploy Gateway Code

```bash
# From your workstation
rsync -avz gateway/ pi@<rpi-ip>:/home/pi/weather-gateway/

# On RPi
cd /home/pi/weather-gateway
sudo apt install -y python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Edit config.yaml: mqtt.broker to server IP
sudo venv/bin/python lora_gateway.py
```

### 4. Auto-start Gateway

Create `/etc/systemd/system/lora-gateway.service`:

```ini
[Unit]
Description=LoRa MQTT Gateway
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/weather-gateway
ExecStart=/home/pi/weather-gateway/venv/bin/python lora_gateway.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## ESP32 Node Deployment

### 1. Flash Firmware

```bash
cd firmware/weather-node

# Edit src/config.h:
#   - Set NODE_ID unique per node
#   - Configure sleep interval
#   - Adjust pin assignments if different

# Flash (USB connection)
pio run -t upload

# Monitor serial output
pio run -t monitor
```

### 2. Field Deployment

1. Mount enclosure on pole (2m+ height for wind sensors)
2. Connect antenna, ensure vertical orientation
3. Place solar panel facing south (northern hemisphere)
4. Connect battery last (prevents spark)
5. Verify: check serial monitor for sensor readings + TX confirmations
6. Verify: check PostgreSQL for incoming data

### 3. Add Node to Database

```sql
INSERT INTO sensor_nodes (name, location, latitude, longitude, node_type)
VALUES ('Node 2 — Garden', 'Back garden weather hut', 14.6001, 120.9835, 'C3');
```

## Testing the Pipeline End-to-End

### 1. MQTT Test

```bash
# On server, subscribe to topic
mosquitto_sub -t "weather/raw" -v

# Publish a test packet
mosquitto_pub -t "weather/raw" -m '{"n":1,"t":29.4,"h":78,"p":1013,"b":3.8,"r":2,"ws":1.5,"wd":180,"sm":42}'
```

### 2. Database Check

```bash
psql -h localhost -U weather_ingestor -d weather_station \
  -c "SELECT node_id, temperature, humidity, received_at FROM sensor_readings ORDER BY received_at DESC LIMIT 5;"
```

### 3. Grafana

- Open http://<server-ip>:3000
- Login: admin / admin
- Data source "WeatherStation" should already be configured
- Create a new dashboard → Add panel → Query sensor_readings

## Troubleshooting

See `docs/troubleshooting.md` for common issues.
