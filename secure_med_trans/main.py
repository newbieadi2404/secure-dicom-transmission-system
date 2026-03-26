import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import json
import hashlib
import time
import uuid

from secure_med_trans.core.dicom_handler import DICOMHandler
from secure_med_trans.core.image_processor import ImageProcessor
from secure_med_trans.core.metadata_manager import MetadataManager

from secure_med_trans.security.hybrid_encryptor import HybridEncryptor
from secure_med_trans.security.secure_package import SecurePackage
from secure_med_trans.security.cryptography.rsa_encryptor import RSAEncryptor
from secure_med_trans.security.cryptography.digital_signature import DigitalSignature

from secure_med_trans.transmission.email_sender import EmailSender


# 🔥 JSON-safe serializer
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


def encrypt_pipeline():
    base_dir = Path(__file__).parent.parent.resolve()
    output_dir = base_dir / "output"
    keys_dir = base_dir / "keys"

    output_dir.mkdir(parents=True, exist_ok=True)
    keys_dir.mkdir(parents=True, exist_ok=True)

    dicom_path = base_dir / "sample_data" / "sample.dcm"
    output_path = output_dir / "package.smt"

    print("🩻 Loading DICOM...")
    dicom = DICOMHandler()
    ds = dicom.load_dicom(dicom_path)

    print("📊 Extracting pixel data...")
    pixel_data = dicom.extract_pixel_data(ds)

    print("📑 Extracting header...")
    header = dicom.extract_header(ds)

    print("🔄 Serializing image...")
    processor = ImageProcessor()
    payload = processor.to_bytes(pixel_data)

    image_payload = {
        "data": payload["data"].hex(),
        "shape": payload["shape"],
        "dtype": payload["dtype"]
    }

    image_bytes = json.dumps(image_payload).encode()

    # 🔥 HASH
    print("🧮 Computing hash...")
    header["hash"] = hashlib.sha256(image_bytes).hexdigest()

    print("🔐 Preparing metadata...")
    metadata_mgr = MetadataManager()
    metadata = {
        "protected": metadata_mgr.select_protected_attributes(ds),
        "public": metadata_mgr.select_public_attributes(ds)
    }

    # =========================
    # 🔥 SECURITY LAYER
    # =========================
    sender_email = input("Sender email: ")

    header["security"] = {
        "sender": sender_email,
        "timestamp": int(time.time()),
        "nonce": str(uuid.uuid4())
    }

    # =========================
    # 🔑 KEY HANDLING
    # =========================
    print("🔑 Preparing RSA keys...")

    rsa = RSAEncryptor()

    private_path = keys_dir / "private.pem"
    public_path = keys_dir / "public.pem"

    if private_path.exists() and public_path.exists():
        print("🔑 Loading existing keys...")
        private_key = private_path.read_bytes()
        public_key = public_path.read_bytes()
    else:
        print("🔑 Generating new keys...")
        private_key, public_key = rsa.generate_key_pair()
        private_path.write_bytes(private_key)
        public_path.write_bytes(public_key)

    print("🔑 Keys ready")

    # =========================
    # 🔥 LOAD CERTIFICATE (CRITICAL)
    # =========================
    cert_path = keys_dir / "user_cert.json"

    if not cert_path.exists():
        raise Exception("❌ Certificate not found. Run generate_certificate.py first.")

    certificate = cert_path.read_text()

    hybrid = HybridEncryptor()

    print("🔒 Encrypting image...")
    encrypted_image = hybrid.encrypt(image_bytes, public_key)

    print("🔐 Encrypting metadata...")
    protected_bytes = json.dumps(metadata["protected"]).encode()
    encrypted_meta = hybrid.encrypt(protected_bytes, public_key)

    header["metadata"] = {
        "public": metadata["public"],
        "protected": {
            "encrypted_key": encrypted_meta["encrypted_key"].hex(),
            "ciphertext": encrypted_meta["ciphertext"].hex(),
            "nonce": encrypted_meta["nonce"].hex(),
            "tag": encrypted_meta["tag"].hex()
        }
    }

    # 🔥 deterministic header
    safe_header = make_json_safe(header)

    header_bytes = json.dumps(
        safe_header,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    print("✍️ Signing full package...")

    signing_blob = (
        encrypted_image["encrypted_key"] +
        encrypted_image["nonce"] +
        encrypted_image["tag"] +
        encrypted_image["ciphertext"] +
        header_bytes
    )

    signer = DigitalSignature()
    signature = signer.sign(signing_blob, private_key)

    print("📦 Creating package...")

    package = SecurePackage.create({
        "header": header,
        "encrypted_key": encrypted_image["encrypted_key"],
        "nonce": encrypted_image["nonce"],
        "tag": encrypted_image["tag"],
        "ciphertext": encrypted_image["ciphertext"],
        "signature": signature,
        "certificate": certificate   # 🔥 THIS REPLACES public_key
    })

    SecurePackage.save(package, output_path)

    print("✅ ENCRYPTION COMPLETE:", output_path)

    # =========================
    # 📧 EMAIL
    # =========================
    send = input("Send via email? (y/n): ").lower()

    if send == "y":
        password = input("App password: ")
        receiver_email = input("Receiver email: ")

        print("📧 Sending email...")

        email_sender = EmailSender()
        email_sender.send_package(
            sender_email,
            password,
            receiver_email,
            output_path
        )

    print("🩻 Loading DICOM...")
    dicom = DICOMHandler()
    ds = dicom.load_dicom(dicom_path)

    print("📊 Extracting pixel data...")
    pixel_data = dicom.extract_pixel_data(ds)

    print("📑 Extracting header...")
    header = dicom.extract_header(ds)

    print("🔄 Serializing image...")
    processor = ImageProcessor()
    payload = processor.to_bytes(pixel_data)

    image_payload = {
        "data": payload["data"].hex(),
        "shape": payload["shape"],
        "dtype": payload["dtype"]
    }

    image_bytes = json.dumps(image_payload).encode()

    # 🔥 HASH
    print("🧮 Computing hash...")
    header["hash"] = hashlib.sha256(image_bytes).hexdigest()

    print("🔐 Preparing metadata...")
    metadata_mgr = MetadataManager()
    metadata = {
        "protected": metadata_mgr.select_protected_attributes(ds),
        "public": metadata_mgr.select_public_attributes(ds)
    }

    # =========================
    # 🔥 SECURITY LAYER
    # =========================
    sender_email = input("Sender email: ")

    header["security"] = {
        "sender": sender_email,
        "timestamp": int(time.time()),
        "nonce": str(uuid.uuid4())
    }

    # =========================
    # 🔑 KEY HANDLING
    # =========================
    print("🔑 Preparing RSA keys...")

    rsa = RSAEncryptor()

    private_path = keys_dir / "private.pem"
    public_path = keys_dir / "public.pem"

    if private_path.exists() and public_path.exists():
        print("🔑 Loading existing keys...")
        private_key = private_path.read_bytes()
        public_key = public_path.read_bytes()
    else:
        print("🔑 Generating new keys...")
        private_key, public_key = rsa.generate_key_pair()
        private_path.write_bytes(private_key)
        public_path.write_bytes(public_key)

    print("🔑 Keys ready")

    # =========================
    # 🔥 LOAD CERTIFICATE (CRITICAL)
    # =========================
    cert_path = keys_dir / "user_cert.json"

    if not cert_path.exists():
        raise Exception("❌ Certificate not found. Run generate_certificate.py first.")

    certificate = cert_path.read_text()

    hybrid = HybridEncryptor()

    print("🔒 Encrypting image...")
    encrypted_image = hybrid.encrypt(image_bytes, public_key)

    print("🔐 Encrypting metadata...")
    protected_bytes = json.dumps(metadata["protected"]).encode()
    encrypted_meta = hybrid.encrypt(protected_bytes, public_key)

    header["metadata"] = {
        "public": metadata["public"],
        "protected": {
            "encrypted_key": encrypted_meta["encrypted_key"].hex(),
            "ciphertext": encrypted_meta["ciphertext"].hex(),
            "nonce": encrypted_meta["nonce"].hex(),
            "tag": encrypted_meta["tag"].hex()
        }
    }

    # 🔥 deterministic header
    safe_header = make_json_safe(header)

    header_bytes = json.dumps(
        safe_header,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    print("✍️ Signing full package...")

    signing_blob = (
        encrypted_image["encrypted_key"] +
        encrypted_image["nonce"] +
        encrypted_image["tag"] +
        encrypted_image["ciphertext"] +
        header_bytes
    )

    signer = DigitalSignature()
    signature = signer.sign(signing_blob, private_key)

    print("📦 Creating package...")

    package = SecurePackage.create({
        "header": header,
        "encrypted_key": encrypted_image["encrypted_key"],
        "nonce": encrypted_image["nonce"],
        "tag": encrypted_image["tag"],
        "ciphertext": encrypted_image["ciphertext"],
        "signature": signature,
        "certificate": certificate   # 🔥 THIS REPLACES public_key
    })

    SecurePackage.save(package, output_path)

    print("✅ ENCRYPTION COMPLETE:", output_path)

    # =========================
    # 📧 EMAIL
    # =========================
    send = input("Send via email? (y/n): ").lower()

    if send == "y":
        password = input("App password: ")
        receiver_email = input("Receiver email: ")

        print("📧 Sending email...")

        email_sender = EmailSender()
        email_sender.send_package(
            sender_email,
            password,
            receiver_email,
            output_path
        )


if __name__ == "__main__":
    encrypt_pipeline()