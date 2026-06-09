#!/usr/bin/env python3
"""
lora_gateway.py — Single-channel LoRa-to-MQTT packet forwarder

Listens on an SX1276/SX1278 module for incoming LoRa packets and
forwards them to the MQTT broker on the central server.

Polling-based (no IRQ) for simplicity. Adequate for weather station
data rates (1 packet every 60-300s per node).

Usage:
    python3 lora_gateway.py [--config config.yaml]
"""

import argparse
import json
import logging
import signal
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import yaml
from SX127x.LoRa import LoRa, MODE, BW, SF, CR
from SX127x.board_config import BOARD

# ── Config ──────────────────────────────────────────────────────────
DEFAULT_CONFIG = Path(__file__).parent / "config.yaml"

def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def setup_logging(cfg: dict) -> logging.Logger:
    logger = logging.getLogger("gateway")
    level = getattr(logging, cfg.get("logging", {}).get("level", "INFO"))
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.handlers.clear()
    logger.addHandler(handler)

    log_file = cfg.get("logging", {}).get("file", "")
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(handler.formatter)
        logger.addHandler(fh)

    return logger


# ── LoRa Setup ──────────────────────────────────────────────────────
def setup_lora(cfg: dict, logger: logging.Logger) -> LoRa:
    BOARD.setup()
    lora = LoRa()

    lora.set_mode(MODE.SLEEP)
    lora.reset_ptr_rx()

    freq = cfg["lora"]["frequency"]
    bw = cfg["lora"]["bandwidth"]
    sf = cfg["lora"]["spreading_factor"]
    cr = cfg["lora"]["coding_rate"]

    lora.set_freq(freq)
    lora.set_bw(bw)
    lora.set_spreading_factor(sf)
    lora.set_coding_rate(cr)
    lora.set_sync_word(cfg["lora"]["sync_word"])
    lora.set_preamble(cfg["lora"]["preamble_length"])

    logger.info(
        f"LoRa configured: {freq} MHz, BW={bw} kHz, "
        f"SF={sf}, CR=4/{cr}"
    )

    lora.set_mode(MODE.RXCONT)
    logger.info("LoRa in continuous RX mode")

    return lora


# ── MQTT Setup ──────────────────────────────────────────────────────
def setup_mqtt(cfg: dict, logger: logging.Logger) -> mqtt.Client:
    client = mqtt.Client(client_id=cfg["mqtt"]["client_id"])

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"MQTT connected to {cfg['mqtt']['broker']}:{cfg['mqtt']['port']}")
        else:
            logger.error(f"MQTT connection failed, rc={rc}")

    def on_disconnect(client, userdata, rc):
        logger.warning(f"MQTT disconnected, rc={rc} — will reconnect")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    client.connect_async(cfg["mqtt"]["broker"], cfg["mqtt"]["port"], cfg["mqtt"]["keepalive"])
    client.loop_start()

    return client


# ── Main Loop ───────────────────────────────────────────────────────
def run_gateway(lora: LoRa, mqtt_client: mqtt.Client, cfg: dict, logger: logging.Logger):
    topic = cfg["mqtt"]["topic"]
    show_packets = cfg.get("logging", {}).get("show_packets", True)
    running = True

    def shutdown(sig, frame):
        nonlocal running
        logger.info("Shutting down...")
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    packet_count = 0
    logger.info(f"Gateway ready — publishing to '{topic}'")

    while running:
        if lora.get_rx_done():
            try:
                payload_bytes = lora.read_payload()
                payload_str = bytes(payload_bytes).decode("utf-8", errors="replace")
                rssi = lora.get_pkt_rssi_value()

                # Publish to MQTT
                result = mqtt_client.publish(topic, payload_str)
                packet_count += 1

                if show_packets:
                    logger.info(
                        f"RX #{packet_count} | RSSI={rssi} dBm | "
                        f"len={len(payload_bytes)} | {payload_str[:120]}"
                    )
                else:
                    logger.debug(f"RX #{packet_count} | RSSI={rssi} dBm")

            except Exception as e:
                logger.error(f"Packet processing error: {e}")

        time.sleep(0.05)  # 50ms poll — responsive enough for LoRa data rates

    # Clean shutdown
    logger.info(f"Stopped. Total packets: {packet_count}")
    lora.set_mode(MODE.SLEEP)
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    BOARD.teardown()


# ── Entry Point ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="LoRa-to-MQTT Gateway")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    logger = setup_logging(cfg)

    logger.info("=== Weather Station LoRa Gateway ===")

    try:
        lora = setup_lora(cfg, logger)
    except Exception as e:
        logger.error(f"LoRa init failed: {e}")
        logger.error("Is SPI enabled? Run: sudo raspi-config")
        sys.exit(1)

    try:
        mqtt_client = setup_mqtt(cfg, logger)
    except Exception as e:
        logger.error(f"MQTT init failed: {e}")
        sys.exit(1)

    run_gateway(lora, mqtt_client, cfg, logger)


if __name__ == "__main__":
    main()
