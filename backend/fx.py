# backend/fx.py
import requests
import json
import os
from datetime import datetime, timedelta

FX_CACHE_FILE = os.environ.get("FX_CACHE_FILE", "./fx_cache.json")
BOC_URL = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json"

def _read_cache():
    try:
        if not os.path.exists(FX_CACHE_FILE):
            return None
        with open(FX_CACHE_FILE, "r") as f:
            data = json.load(f)
        ts = datetime.fromisoformat(data.get("fetched_at"))
        if datetime.utcnow() - ts > timedelta(hours=24):
            return None
        return data.get("rate")
    except Exception:
        return None

def _write_cache(rate):
    try:
        with open(FX_CACHE_FILE, "w") as f:
            json.dump({"rate": rate, "fetched_at": datetime.utcnow().isoformat()}, f)
    except Exception:
        pass

def get_usd_to_cad_rate():
    r = _read_cache()
    if r:
        return r
    try:
        resp = requests.get(BOC_URL, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        obs = payload.get("observations", [])
        if obs and obs[0].get("FXUSDCAD") and obs[0]["FXUSDCAD"].get("v"):
            rate = float(obs[0]["FXUSDCAD"]["v"])
            _write_cache(rate)
            return rate
    except Exception:
        pass
    # fallback
    return 1.35
