#!/usr/bin/env python3
import time
import json
import fourletterphat
from dotenv import load_dotenv
import os

load_dotenv()
LOG_PATH = os.getenv("LOG_PATH")

def display_value(value: float, symbol: str):
    fourletterphat.clear()

    if value >= 100:
        # Just show '100%' or '100V'
        display = f"100{symbol}"
        fourletterphat.print_str(display)
    else:
        # Format to one decimal, remove '.', pad to 3 digits
        formatted = f"{value:.1f}".replace('.', '')  # e.g. 1.1 → '11', 99.8 → '998'
        formatted = formatted.zfill(3)               # ensure 3 digits: '011', '998'
        display = formatted + symbol                 # '011%' or '998V'

        fourletterphat.print_str(display)
        fourletterphat.set_decimal(1, True)          # Decimal after char[1]

    fourletterphat.show()

while True:
    try:
        with open(LOG_PATH, 'rb') as f:
            f.seek(-2, 2)
            while f.read(1) != b'\n':
                f.seek(-2, 1)
            last_line = f.readline().decode()

        data = json.loads(last_line)
        soc = data['payload']['soc']
        voltage = data['payload']['voltage']

        display_value(soc, '%')
        time.sleep(5)

        display_value(voltage, 'V')
        time.sleep(5)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)
