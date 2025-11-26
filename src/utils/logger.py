import json
import datetime
import os

class StructuredLogger:
    def __init__(self, log_path="logs/run_log.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def info(self, event, data=None):
        entry = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "event": event,
            "data": data or {}
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
