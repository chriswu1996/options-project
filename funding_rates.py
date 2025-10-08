import time
import requests
import pandas as pd

HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"

def get_historical_funding_rates(coin: str, start_time_ms: int, end_time_ms: int = None):
    payload = {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": start_time_ms
    }
    if end_time_ms is not None:
        payload["endTime"] = end_time_ms

    resp = requests.post(HYPERLIQUID_API, json=payload)
    resp.raise_for_status()
    return resp.json()

# last 24h of funding history for BTC
now_ms = int(time.time() * 1000)
one_day_ms = 24 * 60 * 60 * 1000
start_ms = now_ms - one_day_ms

history = get_historical_funding_rates("BTC", start_ms, now_ms)
history = pd.DataFrame(history)
history['time'] = pd.to_datetime(history["time"], unit="ms", utc=True)
print(history)
