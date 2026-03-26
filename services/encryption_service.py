from pathlib import Path
import json
import hashlib
import time
import uuid

from secure_med_trans.core.dicom_handler import DICOMHandler
from secure_med_trans.core.image_processor import ImageProcessor
from secure_med_trans.core.metadata_manager import MetadataManager

from secure_med_trans.security.hybrid_encryptor import HybridEncryptor
from secure_med_trans.security.secure_package import SecurePackage
from secure_med_trans.security.cryptography.digital_signature import DigitalSignature
from secure_med_trans.security.security_metrics import SecurityMetrics

from secure_med_trans.transmission.email_sender import EmailSender
from services.key_service import resolve_private_key, resolve_public_key


from config import UPLOADS_DIR

# =========================
# 🔧 Utility
# =========================
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


# =========================
# 🧩 Step 1: DICOM Processing
# =========================
def process_dicom(dicom_path):
    if not Path(dicom_path).exists():
        raise FileNotFoundError(f"DICOM file not found: {dicom_path}")

    dicom = DICOMHandler()
    ds = dicom.load_dicom(dicom_path)

    pixel_data = dicom.extract_pixel_data(ds)
    header = dicom.extract_header(ds)

    processor = ImageProcessor()
    payload = processor.to_bytes(pixel_data)

    image_payload = {
        "data": payload["data"].hex(),
        "shape": payload["shape"],
        "dtype": payload["dtype"],
        "size": payload["size"]
    }

    image_bytes = json.dumps(image_payload).encode()
    header["hash"] = hashlib.sha256(image_bytes).hexdigest()

    metadata_mgr = MetadataManager()
    metadata = {
        "protected": metadata_mgr.select_protected_attributes(ds),
        "public": metadata_mgr.select_public_attributes(ds)
    }

    return image_bytes, header, metadata, pixel_data


# =========================
# 🔐 Step 2: Encryption (FIXED)
# =========================
def encrypt_data(image_bytes, metadata, header, sender_email, receiver_email, certificate=None):
    if not sender_email:
        raise ValueError("Sender email is required")

    header["security"] = {
        "sender": sender_email,
        "receiver": receiver_email,
        "timestamp": int(time.time()),
        "nonce": str(uuid.uuid4())
    }

    private_key = resolve_private_key(sender_email)
    if not private_key:
        import logging
        logging.error(f"DEBUG: resolve_private_key failed for {sender_email}")
        raise Exception("Unknown sender")

    receiver_public = resolve_public_key(receiver_email)
    if not receiver_public:
        raise Exception("Unknown receiver")

    # If certificate not provided, try to find it in the keys directory
    if not certificate:
        keys_dir = Path("keys")
        cert_path = keys_dir / "user_cert.json"
        if cert_path.exists():
            certificate = cert_path.read_text()
        else:
            raise Exception("Certificate missing. Please ensure doctor is registered.")

    # Validate certificate identity
    try:
        cert_json = json.loads(certificate)
        identity = cert_json.get("data", {}).get("identity")
        if identity != sender_email:
            raise Exception("Certificate identity does not match sender")
    except Exception as e:
        raise Exception(f"Certificate error: {str(e)}")

    hybrid = HybridEncryptor()

    # 🔥 REAL ENCRYPTION (receiver key)
    encrypted_image = hybrid.encrypt(image_bytes, receiver_public)

    protected_bytes = json.dumps(metadata["protected"]).encode()
    encrypted_meta = hybrid.encrypt(protected_bytes, receiver_public)

    header["metadata"] = {
        "public": metadata["public"],
        "protected": {
            "encrypted_key": encrypted_meta["encrypted_key"].hex(),
            "ciphertext": encrypted_meta["ciphertext"].hex(),
            "nonce": encrypted_meta["nonce"].hex(),
            "tag": encrypted_meta["tag"].hex()
        }
    }

    return encrypted_image, header, private_key, certificate


# =========================
# 📦 Step 3: Package Creation
# =========================
def create_package(encrypted_image, header, private_key, certificate, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    safe_header = make_json_safe(header)

    header_bytes = json.dumps(
        safe_header,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    signing_blob = (
        encrypted_image["encrypted_key"] +
        encrypted_image["nonce"] +
        encrypted_image["tag"] +
        encrypted_image["ciphertext"] +
        header_bytes
    )

    signer = DigitalSignature()
    signature = signer.sign(signing_blob, private_key)

    package = SecurePackage.create({
        "header": header,
        "encrypted_key": encrypted_image["encrypted_key"],
        "nonce": encrypted_image["nonce"],
        "tag": encrypted_image["tag"],
        "ciphertext": encrypted_image["ciphertext"],
        "signature": signature,
        "certificate": certificate
    })

    SecurePackage.save(package, output_path)
    return str(output_path)


# =========================
# 📧 Step 4: Email
# =========================
def send_secure_email(sender, receiver, file_path):
    from flask import current_app
    system_email = current_app.config.get('SMTP_EMAIL')
    system_password = current_app.config.get('SMTP_PASSWORD')
    email_sender = EmailSender()
    email_sender.send_package(system_email, system_password, receiver, file_path)


# =========================
# 🚀 FINAL PIPELINE (FIXED)
# =========================
def process_and_send(dicom_path, sender_email, receiver_email, certificate=None):
    image_bytes, header, metadata, pixel_data = process_dicom(dicom_path)

    encrypted_image, header, private_key, certificate = encrypt_data(
        image_bytes, metadata, header, sender_email, receiver_email, certificate
    )

    # 🔥 SECURITY EVALUATION (for IEE Paper)
    try:
        SecurityMetrics.comprehensive_analysis(pixel_data, encrypted_image["ciphertext"])
    except Exception as e:
        import logging
        logging.warning(f"Security evaluation skipped: {e}")

    timestamp = int(time.time())
    output_path = UPLOADS_DIR / f"record_{timestamp}.smt"
    created_path = create_package(
        encrypted_image,
        header,
        private_key,
        certificate,
        output_path
    )

    send_secure_email(sender_email, receiver_email, created_path)

    return {
        "status": "success",
        "file": created_path,
        "receiver": receiver_email
    }
