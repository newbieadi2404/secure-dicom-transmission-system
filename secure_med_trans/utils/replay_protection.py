import json
import time
from pathlib import Path

# =========================
# 🔐 REPLAY PROTECTION PATHS
# =========================
from config import OUTPUT_DIR

STORE_PATH = OUTPUT_DIR / "processed_nonces.json"

EXPIRY_WINDOW = 1800  # 30 minutes


def _load_store():
    if not STORE_PATH.exists():
        return {}

    try:
        with open(STORE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_store(store):
    STORE_PATH.parent.mkdir(exist_ok=True)

    temp_path = STORE_PATH.with_suffix(".tmp")

    with open(temp_path, "w") as f:
        json.dump(store, f, indent=2)

    temp_path.replace(STORE_PATH)


def check_and_store_nonce(sender, nonce, timestamp):
    store = _load_store()

    if sender not in store:
        store[sender] = {"nonces": {}}

    sender_data = store[sender]["nonces"]

    current_time = int(time.time())

    # 🔥 CLEAN OLD NONCES
    expired = [
        n for n, ts in sender_data.items()
        if current_time - ts > EXPIRY_WINDOW
    ]

    for n in expired:
        del sender_data[n]

    # 🔥 REPLAY CHECK
    if nonce in sender_data:
        raise Exception("❌ REPLAY ATTACK DETECTED")

    # 🔥 STORE NEW NONCE
    sender_data[nonce] = timestamp

    _save_store(store)