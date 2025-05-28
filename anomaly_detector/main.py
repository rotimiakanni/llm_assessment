import os
import json
import time
from datetime import datetime
from pathlib import Path
import celery
from dotenv import load_dotenv

load_dotenv()


SENSOR_ID = os.getenv("SENSOR_ID")
INPUT_FILE = os.getenv("INPUT_FILE")
OUTPUT_FILE = os.getenv("OUTPUT_FILE")
BROKER_URL = os.getenv("CELERY_BROKER")


class AnomalyDetector:
    TEMP_SPIKE = 40.0
    PRESSURE_SPIKE = 4.0
    FLOW_SPIKE = 120.0
    TEMP_DRIFT = 38.0
    DRIFT_DURATION = 15  # seconds
    DROPOUT_THRESHOLD = 10  # seconds

    def __init__(self):
        self.last_timestamp = None
        self.drift_start = None

    def parse_timestamp(self, ts: str) -> datetime:
        try:
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

    def check_spike(self, reading, ts):
        anomalies = []
        if reading["temperature"] > self.TEMP_SPIKE:
            anomalies.append(
                {
                    "type": "spike",
                    "timestamp": reading["timestamp"],
                    "sensor_id": SENSOR_ID,
                    "parameter": "temperature",
                    "value": reading["temperature"],
                    "message": "Temperature spike detected.",
                }
            )
        if reading["pressure"] > self.PRESSURE_SPIKE:
            anomalies.append(
                {
                    "type": "spike",
                    "timestamp": reading["timestamp"],
                    "sensor_id": SENSOR_ID,
                    "parameter": "pressure",
                    "value": reading["pressure"],
                    "message": "Pressure spike detected.",
                }
            )
        if reading["flow"] > self.FLOW_SPIKE:
            anomalies.append(
                {
                    "type": "spike",
                    "timestamp": reading["timestamp"],
                    "sensor_id": SENSOR_ID,
                    "parameter": "flow",
                    "value": reading["flow"],
                    "message": "Flow spike detected.",
                }
            )
        return anomalies

    def check_drift(self, reading, ts):
        anomalies = []
        temp = reading["temperature"]
        if temp > self.TEMP_DRIFT:
            if not self.drift_start:
                self.drift_start = ts
            elif (ts - self.drift_start).total_seconds() >= self.DRIFT_DURATION:
                anomalies.append(
                    {
                        "type": "drift",
                        "timestamp": reading["timestamp"],
                        "sensor_id": SENSOR_ID,
                        "parameter": "temperature",
                        "value": temp,
                        "duration_seconds": int(
                            (ts - self.drift_start).total_seconds()
                        ),
                        "message": f"Temperature drift detected over {int((ts - self.drift_start).total_seconds())} seconds.",
                    }
                )
                self.drift_start = None
        else:
            self.drift_start = None
        return anomalies

    def check_dropout(self, ts):
        anomalies = []
        if self.last_timestamp:
            delta = (ts - self.last_timestamp).total_seconds()
            if delta > self.DROPOUT_THRESHOLD:
                anomalies.append(
                    {
                        "type": "dropout",
                        "timestamp": ts.isoformat() + "Z",
                        "sensor_id": SENSOR_ID,
                        "parameter": "data",
                        "value": None,
                        "duration_seconds": int(delta),
                        "message": f"No data received for {int(delta)} seconds.",
                    }
                )
        self.last_timestamp = ts
        return anomalies

    def detect(self, reading):
        ts = self.parse_timestamp(reading["timestamp"])
        anomalies = []
        anomalies += self.check_spike(reading, ts)
        anomalies += self.check_drift(reading, ts)
        anomalies += self.check_dropout(ts)
        return anomalies


def stream_and_detect():
    detector = AnomalyDetector()
    Path(OUTPUT_FILE).touch()
    with open(INPUT_FILE, "r") as f:
        f.seek(0, 2)  # move to end
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            try:
                reading = json.loads(line)
                anomalies = detector.detect(reading)
                for anomaly in anomalies:
                    print(f"[Anomaly Detected] {anomaly}", flush=True)
                    with open(OUTPUT_FILE, "a") as out:
                        out.write(json.dumps(anomaly) + "\n")

                    # Trigger LLM summary task
                    try:
                        app = celery.Celery("client", broker=BROKER_URL)
                        app.send_task("worker.generate_summary_task")
                        print("[Anomaly Detector] Summary regenerated.", flush=True)
                    except Exception as e:
                        print(f"[Anomaly Detector] Failed to trigger summary: {e}", flush=True)
            except json.JSONDecodeError:
                continue


if __name__ == "__main__":
    print("[Anomaly Detector] Monitoring...")
    stream_and_detect()
