import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ANOMALY_FILE = os.getenv("ANOMALY_FILE")
SUMMARY_FILE = os.getenv("SUMMARY_FILE")
SENSOR_FILE = os.getenv("SENSOR_FILE")

app = FastAPI()


@app.get("/anomalies")
def get_anomalies():
    if not Path(ANOMALY_FILE).exists():
        return JSONResponse(content=[], status_code=200)
    with open(ANOMALY_FILE, "r") as f:
        anomalies = [json.loads(line) for line in f.readlines()]
    return anomalies


@app.get("/summary")
def get_summary():
    if not Path(SUMMARY_FILE).exists():
        return PlainTextResponse("No summary generated yet.", status_code=200)
    with open(SUMMARY_FILE, "r") as f:
        return PlainTextResponse(f.read())


@app.get("/status")
def get_status():
    def get_modified_time(path):
        if Path(path).exists():
            return Path(path).stat().st_mtime
        return 0

    now = datetime.utcnow().timestamp()
    status = {
        "sensor_active": (now - get_modified_time(SENSOR_FILE)) < 10,
        "anomaly_active": (now - get_modified_time(ANOMALY_FILE)) < 20,
        "summary_exists": Path(SUMMARY_FILE).exists(),
    }
    return status
