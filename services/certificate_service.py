import os
from pathlib import Path
import json
import time
import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Use absolute path for keys directory
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEYS_DIR = BASE_DIR / "keys"
REVOKED_FILE = KEYS_DIR / "revoked_certs.json"


# =========================
# 🔐 LOAD REVOKED LIST
# =========================
def load_revoked():
    if not REVOKED_FILE.exists():
        return []

    try:
        with open(REVOKED_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def is_revoked(identity):
    revoked = load_revoked()
    return identity in revoked


# =========================
# 🔐 CERTIFICATE VALIDATION
# =========================
def validate_certificate(cert_str, sender_email):
    try:
        cert = json.loads(cert_str)

        # =========================
        # 🔐 STRUCTURE VALIDATION
        # =========================
        if "data" not in cert or "signature" not in cert:
            raise Exception("Invalid certificate format")

        cert_data = cert["data"]
        signature = base64.b64decode(cert["signature"])

        if "identity" not in cert_data:
            raise Exception("Certificate missing identity")

        identity = cert_data["identity"]

        # 🔥 DEBUG (keep for now)
        print("CERT IDENTITY:", identity)
        print("REVOKED LIST:", load_revoked())

        # =========================
        # 🔐 IDENTITY CHECK
        # =========================
        if identity != sender_email:
            raise Exception("Certificate email mismatch")

        # =========================
        # 🔐 EXPIRY CHECK
        # =========================
        if "expiry" in cert_data:
            if cert_data["expiry"] < int(time.time()):
                raise Exception("Certificate expired")

        # =========================
        # 🔐 LOAD CA PUBLIC KEY
        # =========================
        ca_public_path = KEYS_DIR / "ca_public.pem"

        if not ca_public_path.exists():
            raise Exception("CA public key missing")

        ca_public = ca_public_path.read_bytes()

        ca_key = serialization.load_pem_public_key(ca_public)

        # =========================
        # 🔐 VERIFY CERT SIGNATURE
        # =========================
        ca_key.verify(
            signature,
            json.dumps(cert_data, sort_keys=True).encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        # =========================
        # 🔥 REVOCATION CHECK
        # =========================
        if is_revoked(identity):
            raise Exception("Certificate revoked")

        return True

    except Exception as e:
        raise Exception(f"Certificate validation failed: {str(e)}")

# =========================
# 🔐 CERTIFICATE GENERATION
# =========================
def generate_user_certificate(email: str, public_key_pem: bytes):
    """Generates a signed certificate for a user using the CA private key."""
    ca_private_path = KEYS_DIR / "ca_private.pem"
    
    if not ca_private_path.exists():
        raise Exception(f"CA private key missing at {ca_private_path}. Cannot sign certificate.")
        
    ca_private = ca_private_path.read_bytes()
    ca_key = serialization.load_pem_private_key(ca_private, password=None)
    
    cert_data = {
        "identity": email,
        "public_key": base64.b64encode(public_key_pem).decode(),
        "timestamp": int(time.time()),
        "expiry": int(time.time()) + (365 * 24 * 60 * 60) # 1 year
    }
    
    signature = ca_key.sign(
        json.dumps(cert_data, sort_keys=True).encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    certificate = {
        "data": cert_data,
        "signature": base64.b64encode(signature).decode()
    }
    
    # Save as user_cert.json (current system expectation)
    # In a real system, this might be stored in DB or returned to user
    cert_path = KEYS_DIR / "user_cert.json"
    with open(cert_path, "w") as f:
        json.dump(certificate, f, indent=2)
        
    return certificate