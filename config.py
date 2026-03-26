from pathlib import Path

# =========================
#  PATH CONFIGURATION
# =========================
BASE_DIR = Path(__file__).parent.resolve()
KEYS_DIR = BASE_DIR / "keys"
OUTPUT_DIR = BASE_DIR / "output"
UPLOADS_DIR = BASE_DIR / "uploads"

# Ensure directories exist
KEYS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
