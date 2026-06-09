import mqtt from "mqtt";
import { config } from "./config.js";
import { migrate } from "./db.js";
import { ingestPacket } from "./ingest.js";

async function main() {
  console.log("=== Weather Station Ingestor ===");
  console.log(`MQTT: ${config.mqtt.broker} → topic '${config.mqtt.topic}'`);
  console.log(`DB:   ${config.database.url.replace(/\/\/.*@/, "//***@")}`);

  // Auto-migrate on startup
  await migrate();

  // Connect to MQTT broker
  const client = mqtt.connect(config.mqtt.broker);

  client.on("connect", () => {
    console.log("MQTT connected");
    client.subscribe(config.mqtt.topic, (err) => {
      if (err) {
        console.error("MQTT subscribe error:", err);
      } else {
        console.log(`Subscribed to '${config.mqtt.topic}'`);
      }
    });
  });

  client.on("error", (err) => {
    console.error("MQTT error:", err.message);
  });

  client.on("message", async (topic, message) => {
    // MQTT v5 properties may include user properties
    const payload = message.toString();

    await ingestPacket(payload);
    // Note: RSSI/SNR can be added as MQTT user properties in future
  });

  client.on("close", () => {
    console.log("MQTT disconnected — will reconnect");
  });

  // Graceful shutdown
  const shutdown = () => {
    console.log("\nShutting down...");
    client.end();
    process.exit(0);
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
