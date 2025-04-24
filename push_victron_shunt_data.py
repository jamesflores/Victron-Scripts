import subprocess
import json
import warnings
import logging
import requests
from datetime import datetime
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import os

# Suppress all FutureWarnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Config
load_dotenv()
DEVICE = os.getenv("DEVICE")
KEY = os.getenv("KEY")
WORKER_URL = os.getenv("WORKER_URL")
LOG_PATH = os.getenv("LOG_PATH")

# Setup log rotation (100MB max, keep 3 backups)
logger = logging.getLogger("VictronLogger")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_PATH, maxBytes=100 * 1024 * 1024, backupCount=3)
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

# Read command
cmd = ["/home/james/Scripts/Victron/venv/bin/victron-ble", "read", f"{DEVICE}@{KEY}"]

try:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    first_line = proc.stdout.readline()
    proc.terminate()

    data = json.loads(first_line.decode())
    data["timestamp"] = datetime.utcnow().isoformat()

    # Save to local log
    logger.info(json.dumps(data))

    # Push to Cloudflare Worker
    response = requests.put(
        WORKER_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )

    if response.ok:
        print("✅ Sent to Cloudflare Worker!")
    else:
        print(f"❌ Push failed: {response.status_code} - {response.text}")

    # Also print to console
    print("🔋 Victron Reading:")
    print(f"Voltage: {data['payload']['voltage']} V")
    print(f"Current: {data['payload']['current']} A")
    print(f"SOC: {data['payload']['soc']} %")
    print(f"Consumed Ah: {data['payload']['consumed_ah']} Ah")

    remaining_mins = data['payload'].get('remaining_mins')
    if remaining_mins is not None:
        hours = remaining_mins // 60
        minutes = remaining_mins % 60
        print(f"Time Remaining: {hours}h {minutes}m")

except Exception as e:
    print("❌ Error:", e)
