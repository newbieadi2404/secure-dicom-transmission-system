from secure_med_trans.core.dicom_handler import DICOMHandler
from secure_med_trans.security.hybrid_encryptor import HybridEncryptor
from secure_med_trans.security.secure_package import SecurePackage
from secure_med_trans.security.cryptography.digital_signature import DigitalSignature
from secure_med_trans.security.cryptography.ca import CertificateAuthority

from secure_med_trans.utils.replay_protection import check_and_store_nonce
from config import OUTPUT_DIR, KEYS_DIR

import numpy as np
import json
import hashlib
import time
import base64
from pathlib import Path


# 🔥 MUST MATCH encrypt side EXACTLY
def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif isinstance(obj, bytes):
        return obj.hex()
    elif isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    else:
        return str(obj)


def decrypt_pipeline(package_path: str):
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_dicom = output_dir / "decrypted.dcm"

    package_path = Path(package_path)
    if not package_path.exists():
        raise FileNotFoundError(f"❌ Package not found: {package_path}")

    print("📦 Loading package...")
    package_bytes = SecurePackage.load(package_path)
    extracted = SecurePackage.extract(package_bytes)

    header = extracted["header"]

    # =========================
    # 🔥 CERTIFICATE VERIFICATION (REPLACES trusted_keys.json)
    # =========================
    print("🛡️ Verifying sender via certificate...")

    certificate = extracted.get("certificate")

    if not certificate:
        raise Exception("❌ Missing certificate in package")

    # Load CA public key
    with open(KEYS_DIR / "ca_public.pem", "rb") as f:
        ca_public = f.read()

    valid, cert_data = CertificateAuthority.verify_certificate(
        certificate,
        ca_public
    )

    if not valid:
        raise Exception("❌ INVALID CERTIFICATE")

    sender = cert_data["identity"]
    trusted_public_key = base64.b64decode(cert_data["public_key"])

    print(f"✅ Verified sender: {sender}")

    # =========================
    # 🔥 SIGNATURE VERIFICATION
    # =========================
    safe_header = make_json_safe(header)

    header_bytes = json.dumps(
        safe_header,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    verifier = DigitalSignature()

    signing_blob = (
        extracted["encrypted_key"] +
        extracted["nonce"] +
        extracted["tag"] +
        extracted["ciphertext"] +
        header_bytes
    )

    is_valid = verifier.verify(
        signing_blob,
        extracted["signature"],
        trusted_public_key
    )

    if not is_valid:
        raise Exception("❌ SIGNATURE VERIFICATION FAILED")

    print("✅ Signature valid")

    # =========================
    # 🔥 REPLAY PROTECTION
    # =========================
    print("🛡️ Checking replay protection...")

    security = header.get("security", {})
    nonce = security.get("nonce")
    timestamp = security.get("timestamp")

    if not nonce or not timestamp:
        raise Exception("❌ Missing security metadata")

    check_and_store_nonce(sender, nonce, timestamp)

    current_time = int(time.time())

    if abs(current_time - timestamp) > 1800:
        raise Exception("❌ EXPIRED PACKAGE")

    print("✅ Replay protection passed")

    # =========================
    # 🔑 LOAD PRIVATE KEY
    # =========================
    print("🔑 Loading private key...")

    with open("keys/private.pem", "rb") as f:
        private_key = f.read()

    hybrid = HybridEncryptor()

    # =========================
    # 🔓 DECRYPT IMAGE
    # =========================
    print("🔓 Decrypting image...")
    decrypted_bytes = hybrid.decrypt(extracted, private_key)

    # =========================
    # 🔍 HASH VALIDATION
    # =========================
    print("🔍 Verifying data integrity (hash)...")

    recomputed_hash = hashlib.sha256(decrypted_bytes).hexdigest()

    if recomputed_hash != header.get("hash"):
        raise Exception("❌ HASH MISMATCH — DATA CORRUPTED")

    print("✅ Hash verified")

    # =========================
    # 🧠 RECONSTRUCT IMAGE
    # =========================
    print("🧠 Reconstructing image array...")

    payload = json.loads(decrypted_bytes.decode())

    image_bytes = bytes.fromhex(payload["data"])
    shape = tuple(payload["shape"])
    dtype = np.dtype(payload["dtype"])

    image_array = np.frombuffer(image_bytes, dtype=dtype).reshape(shape)

    # =========================
    # 🔐 DECRYPT METADATA
    # =========================
    print("🔐 Decrypting protected metadata...")

    metadata = header.get("metadata", {})
    protected = metadata.get("protected")

    if protected:
        meta_package = {
            "encrypted_key": bytes.fromhex(protected["encrypted_key"]),
            "ciphertext": bytes.fromhex(protected["ciphertext"]),
            "nonce": bytes.fromhex(protected["nonce"]),
            "tag": bytes.fromhex(protected["tag"]),
        }

        decrypted_meta_bytes = hybrid.decrypt(meta_package, private_key)
        protected_metadata = json.loads(decrypted_meta_bytes.decode())

        header["metadata"]["protected"] = protected_metadata

        print("✅ Protected metadata decrypted")
    else:
        print("⚠️ No protected metadata found")

    # =========================
    # 🩻 REBUILD DICOM
    # =========================
    print("🩻 Rebuilding DICOM...")

    dicom = DICOMHandler()
    ds = dicom.reconstruct_dicom(header, image_array)

    dicom.save_dicom(output_dicom, ds)

    print(f"✅ DECRYPTION COMPLETE: {output_dicom}")


if __name__ == "__main__":
    decrypt_pipeline("output/package.smt")