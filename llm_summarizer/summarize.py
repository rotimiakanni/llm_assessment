import json
import os
from pathlib import Path
from langchain_community.llms import LlamaCpp
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

load_dotenv()

ANOMALY_FILE = os.environ.get("ANOMALY_FILE")
SUMMARY_FILE = os.environ.get("SUMMARY_FILE")
MODEL_PATH = "/app/models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
# MODEL_PATH = "/app/models/mistral-7b-instruct-v0.1.Q2_K.gguf"


def load_last_anomaly():
    if not os.path.exists(ANOMALY_FILE):
        return None
    with open(ANOMALY_FILE, "r") as f:
        lines = f.readlines()
        if not lines:
            return None
        return json.loads(lines[-1])


def summarize_anomalies():
    last_anomaly = load_last_anomaly()
    if not last_anomaly:
        print("[LLM Worker] No anomalies to summarize.", flush=True)
        return "No anomalies to summarize."

    print(f"[LLM Worker] Loaded last anomaly: {last_anomaly}", flush=True)
    prompt_text = (
        f"Summarize the following anomaly event:\n"
        f"{last_anomaly['timestamp']}: {last_anomaly['message']}"
    )

    prompt = PromptTemplate(
        input_variables=["log"], template="Summarize the following anomaly:\n{log}"
    )

    llm = LlamaCpp(
        model_path=MODEL_PATH,
        n_ctx=512,
        temperature=0.5,
        verbose=False,
    )

    chain = LLMChain(prompt=prompt, llm=llm)
    summary = chain.run({"log": prompt_text})
    print(f"[LLM Worker] Summary generated. {summary}", flush=True)

    try:
        with open(SUMMARY_FILE, "w") as f:
            f.write(summary)
        print("[LLM Worker] Summary saved to summary.txt", flush=True)
    except Exception as e:
        print(f"[LLM Worker] Failed to write summary.txt: {e}", flush=True)

    return summary
