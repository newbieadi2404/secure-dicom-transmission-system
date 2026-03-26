import os
import json
from typing import Optional
from pathlib import Path

# Use absolute path for keys directory
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEYS_DIR = BASE_DIR / "keys"
REGISTRY_FILE = KEYS_DIR / "user_keys.json"


def _load_registry() -> dict:
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def resolve_private_key(email: str) -> Optional[bytes]:
    reg = _load_registry()
    if email in reg and "private" in reg[email]:
        path = Path(reg[email]["private"])
        if path.exists():
            return path.read_bytes()

    # Default convention: keys/{email}_private.pem
    # Also support legacy names for doctor and patient test accounts
    # Default convention: keys/{email}_private.pem
    # Also support legacy names for doctor and patient test accounts
    possible_paths = [
        KEYS_DIR / f"{email}_private.pem",
        KEYS_DIR / f"{email.split('@')[0]}_private.pem"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.read_bytes()
            
    return None


def resolve_public_key(email: str) -> Optional[bytes]:
    reg = _load_registry()
    if email in reg and "public" in reg[email]:
        path = Path(reg[email]["public"])
        if path.exists():
            return path.read_bytes()

    # Default convention: keys/{email}_public.pem
    # Also support legacy names for doctor and patient test accounts
    # Default convention: keys/{email}_public.pem
    # Also support legacy names for doctor and patient test accounts
    possible_paths = [
        KEYS_DIR / f"{email}_public.pem",
        KEYS_DIR / f"{email.split('@')[0]}_public.pem"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.read_bytes()
            
    return None
