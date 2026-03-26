from pathlib import Path
import json
import uuid
import base64

from secure_med_trans.security.secure_package import SecurePackage
from secure_med_trans.security.hybrid_encryptor import HybridEncryptor
from secure_med_trans.security.cryptography.digital_signature import DigitalSignature
from secure_med_trans.core.image_processor import ImageProcessor

from services.certificate_service import validate_certificate
from services.key_service import resolve_private_key
from config import OUTPUT_DIR


# =========================
# 🔐 REPLAY PROTECTION
# =========================
BASE_DIR = Path(__file__).parent.parent.resolve()
NONCE_FILE = BASE_DIR / "output" / "processed_nonces.json"


def is_replay_attack(nonce):
    if not NONCE_FILE.exists():
        return False
    try:
        with open(NONCE_FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return False
            return nonce in data
    except Exception:
        return False


def store_nonce(nonce):
    try:
        # Ensure directory exists
        NONCE_FILE.parent.mkdir(parents=True, exist_ok=True)

        if NONCE_FILE.exists():
            with open(NONCE_FILE, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        else:
            data = []
        data.append(nonce)
        with open(NONCE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        # Final attempt - if this fails, we let it bubble up with the original exception
        # but we should at least try to make the parent dir again
        NONCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(NONCE_FILE, "w") as f:
            json.dump([nonce], f)


# =========================
# 🔓 DECRYPT SERVICE (HARDENED)
# =========================
def decrypt_file(package_path):
    try:
        package_path = Path(package_path)

        if not package_path.exists():
            raise FileNotFoundError(f"Package not found: {package_path}")

        # =========================
        # 📦 EXTRACT PACKAGE
        # =========================
        package = SecurePackage.extract(package_path)

        header = package["header"]
        header_bytes = package["header_bytes"]
        encrypted_key = package["encrypted_key"]
        nonce = package["nonce"]
        tag = package["tag"]
        ciphertext = package["ciphertext"]
        signature = package["signature"]
        certificate = package["certificate"]

        # =========================
        # 🔥 REPLAY ATTACK CHECK
        # =========================
        nonce_value = header["security"]["nonce"]

        if is_replay_attack(nonce_value):
            raise Exception("Replay attack detected")

        store_nonce(nonce_value)

        # =========================
        # 🔐 CERT VALIDATION
        # =========================
        sender_email = header["security"]["sender"]
        receiver_email = header["security"]["receiver"]

        validate_certificate(certificate, sender_email)

        # =========================
        # 🔐 EXTRACT PUBLIC KEY FROM CERT
        # =========================
        cert_data = json.loads(certificate)

        public_key_b64 = cert_data["data"]["public_key"]
        public_key = base64.b64decode(public_key_b64)

        # =========================
        # 🔐 LOAD RECEIVER PRIVATE KEY
        # =========================
        private_key = resolve_private_key(receiver_email)
        if not private_key:
            raise FileNotFoundError("Receiver private key not found")

        # =========================
        # 🔐 VERIFY SIGNATURE
        # =========================
        signing_blob = (
            encrypted_key +
            nonce +
            tag +
            ciphertext +
            header_bytes
        )

        verifier = DigitalSignature()

        if not verifier.verify(signing_blob, signature, public_key):
            raise Exception("Signature verification failed")

        # =========================
        # 🔓 DECRYPT
        # =========================
        hybrid = HybridEncryptor()

        decrypted_bytes = hybrid.decrypt(
            {
                "encrypted_key": encrypted_key,
                "nonce": nonce,
                "tag": tag,
                "ciphertext": ciphertext
            },
            private_key
        )

        # =========================
        # 🧠 RECONSTRUCT IMAGE
        # =========================
        image_data = json.loads(decrypted_bytes.decode())

        processor = ImageProcessor()

        shape = tuple(image_data["shape"])
        
        # Use the size from the payload if available, otherwise calculate byte size
        raw_bytes = bytes.fromhex(image_data["data"])
        size = image_data.get("size", len(raw_bytes))

        image = processor.from_bytes({
            "data": raw_bytes,
            "shape": shape,
            "size": size,
            "dtype": image_data["dtype"]
        })

        # =========================
        # 💾 SAVE OUTPUT
        # =========================
        output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"decrypted_{uuid.uuid4().hex}.npy"

        import numpy as np
        np.save(output_path, image)

        return {
            "status": "decrypted",
            "output": str(output_path)
        }

    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")
