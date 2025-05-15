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
DEVICES = os.getenv("DEVICES", "").split(",")  # Format: DEVICE1@KEY1,DEVICE2@KEY2,...
WORKER_URL = os.getenv("WORKER_URL")
LOG_PATH = os.getenv("LOG_PATH")

# Setup log rotation (100MB max, keep 3 backups)
logger = logging.getLogger("VictronLogger")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_PATH, maxBytes=100 * 1024 * 1024, backupCount=3)
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

for device_key in DEVICES:
    device_key = device_key.strip()
    if not device_key:
        continue

    cmd = ["/home/james/Scripts/Victron/venv/bin/victron-ble", "read", device_key]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            first_line = proc.stdout.readline()
        except Exception:
            print(f"⏱️  Timeout reading from {device_key} — skipping")
            continue

        proc.terminate()
        proc.wait(timeout=10)

        if not first_line:
            print(f"⚠️  [{device_key}] Empty response — possibly out of range or not paired")
            continue

        try:
            data = json.loads(first_line.decode())
        except json.JSONDecodeError:
            print(f"⚠️  [{device_key}] Invalid JSON received")
            continue
        
        data = json.loads(first_line.decode())
        data["timestamp"] = datetime.utcnow().isoformat()
        data["device_id"] = device_key  # Optional: track which device

        # Save to local log
        logger.info(json.dumps(data))

        # Push to Cloudflare Worker
        response = requests.put(
            WORKER_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )

        if response.ok:
            print(f"✅ [{device_key}] Sent to Cloudflare Worker!")
        else:
            print(f"❌ [{device_key}] Push failed: {response.status_code} - {response.text}")

        # Also print to console
        print(f"🔋 [{device_key}] Victron Reading:")
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
        print(f"❌ [{device_key}] Error:", e)
