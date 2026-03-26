import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


keys_dir = Path("keys")

# 🔥 Load USER public key (IMPORTANT)
public_key = (keys_dir / "user_public.pem").read_bytes()

# 🔥 Load CA private key
ca_private = (keys_dir / "ca_private.pem").read_bytes()

ca_key = serialization.load_pem_private_key(ca_private, password=None)

# =========================
# CERT DATA
# =========================
cert_data = {
    "identity": "doctor@test.com",
    "public_key": base64.b64encode(public_key).decode()
}

# =========================
# SIGN CERT (CA)
# =========================
signature = ca_key.sign(
    json.dumps(cert_data, sort_keys=True).encode(),
    padding.PKCS1v15(),
    hashes.SHA256()
)

certificate = {
    "data": cert_data,
    "signature": base64.b64encode(signature).decode()
}

# =========================
# SAVE
# =========================
with open(keys_dir / "user_cert.json", "w") as f:
    json.dump(certificate, f, indent=2)

print("✅ Certificate regenerated (CORRECT KEY)")