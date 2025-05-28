import os
from celery import Celery
from dotenv import load_dotenv
from summarize import summarize_anomalies

load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER")

app = Celery("tasks", broker=BROKER_URL)


@app.task
def generate_summary_task():
    summary = summarize_anomalies()
    print(f"[LLM Worker] Summary generated. {summary}", flush=True)
    return summary
