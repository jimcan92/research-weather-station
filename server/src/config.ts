import dotenv from "dotenv";
dotenv.config();

export const config = {
  database: {
    url: process.env.DATABASE_URL || "postgresql://weather_ingestor@localhost:5432/weather_station",
  },
  mqtt: {
    broker: process.env.MQTT_BROKER || "mqtt://localhost:1883",
    topic: process.env.MQTT_TOPIC || "weather/raw",
  },
  logLevel: process.env.LOG_LEVEL || "info",
} as const;
