import json
import random
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

SENSOR_ID = os.getenv("SENSOR_ID")
DATA_FILE = os.getenv("SENSOR_FILE")

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)


def generate_reading():
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sensor_id": SENSOR_ID,
        "temperature": round(random.uniform(10.0, 41.0), 2),
        "pressure": round(random.uniform(1.0, 5.0), 2),
        "flow": round(random.uniform(20.0, 121.0), 2),
    }


def write_reading_to_file(reading):
    with open(DATA_FILE, "a") as f:
        f.write(json.dumps(reading) + "\n")


if __name__ == "__main__":
    print("[Sensor Generator] Starting sensor stream...")
    while True:
        reading = generate_reading()
        print(f"[Sensor Generator] Emitting: {reading}")
        write_reading_to_file(reading)
        time.sleep(2)
