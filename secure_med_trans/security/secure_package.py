import json
import struct
from pathlib import Path
from typing import Dict, Any, Union

from secure_med_trans.utils.logger import get_logger
from secure_med_trans.utils.exceptions import InvalidPackageException

logger = get_logger(__name__)


class SecurePackage:

    MAGIC = b"SMT1"
    VERSION = 2

    HEADER_STRUCT = ">4sBIIIIIII"

    # -----------------------------
    # 🔒 JSON SAFE CONVERSION
    # -----------------------------
    @staticmethod
    def _make_json_safe(obj):
        if isinstance(obj, dict):
            return {k: SecurePackage._make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [SecurePackage._make_json_safe(v) for v in obj]
        elif isinstance(obj, bytes):
            return obj.hex()
        elif isinstance(obj, (int, float, bool)) or obj is None:
            return obj
        else:
            return str(obj)

    # -----------------------------
    # 🔐 CREATE PACKAGE
    # -----------------------------
    @classmethod
    def create(cls, data: Dict[str, Any]) -> bytes:

        safe_header = cls._make_json_safe(data["header"])
        header_json = json.dumps(
            safe_header,
            separators=(",", ":"),
            sort_keys=True
        ).encode("utf-8")

        encrypted_key = data["encrypted_key"]
        nonce = data["nonce"]
        tag = data["tag"]
        ciphertext = data["ciphertext"]

        signature = data.get("signature", b"")
        certificate = data.get("certificate", "").encode("utf-8")

        if not all([encrypted_key, nonce, tag, ciphertext]):
            raise InvalidPackageException("Missing required encryption fields")

        header = struct.pack(
            cls.HEADER_STRUCT,
            cls.MAGIC,
            cls.VERSION,
            len(header_json),
            len(encrypted_key),
            len(nonce),
            len(tag),
            len(ciphertext),
            len(signature),
            len(certificate),
        )

        package = (
            header +
            header_json +
            encrypted_key +
            nonce +
            tag +
            ciphertext +
            signature +
            certificate
        )

        logger.info(f"Package created: {len(package)} bytes")
        return package

    # -----------------------------
    # 🔓 EXTRACT PACKAGE (FIXED)
    # -----------------------------
    @classmethod
    def extract(cls, package: Union[bytes, str, Path]) -> Dict[str, Any]:

        if isinstance(package, (str, Path)):
            with open(package, "rb") as f:
                package = f.read()

        header_size = struct.calcsize(cls.HEADER_STRUCT)

        if len(package) < header_size:
            raise InvalidPackageException("Invalid package size")

        (
            magic,
            version,
            header_len,
            key_len,
            nonce_len,
            tag_len,
            data_len,
            sig_len,
            cert_len,
        ) = struct.unpack(cls.HEADER_STRUCT, package[:header_size])

        if magic != cls.MAGIC:
            raise InvalidPackageException("Invalid package magic")

        if version != cls.VERSION:
            raise InvalidPackageException("Unsupported version")

        offset = header_size

        total_expected = (
            offset +
            header_len +
            key_len +
            nonce_len +
            tag_len +
            data_len +
            sig_len +
            cert_len
        )

        if total_expected > len(package):
            raise InvalidPackageException("Corrupted package")

        # =========================
        # 🔥 CRITICAL FIX HERE
        # =========================
        header_json = package[offset: offset + header_len]
        header_bytes = header_json  # 🔥 preserve original bytes
        header = json.loads(header_json.decode("utf-8"))
        offset += header_len

        encrypted_key = package[offset: offset + key_len]
        offset += key_len

        nonce = package[offset: offset + nonce_len]
        offset += nonce_len

        tag = package[offset: offset + tag_len]
        offset += tag_len

        ciphertext = package[offset: offset + data_len]
        offset += data_len

        signature = package[offset: offset + sig_len]
        offset += sig_len

        certificate_bytes = package[offset: offset + cert_len]
        certificate = certificate_bytes.decode("utf-8")

        logger.info("Package extracted successfully")

        return {
            "header": header,
            "header_bytes": header_bytes,  # 🔥 ADDED (CRITICAL)
            "encrypted_key": encrypted_key,
            "nonce": nonce,
            "tag": tag,
            "ciphertext": ciphertext,
            "signature": signature,
            "certificate": certificate,
        }

    # -----------------------------
    # 💾 FILE OPERATIONS
    # -----------------------------
    @staticmethod
    def save(package: bytes, path: Union[str, Path]):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            f.write(package)

        logger.info(f"Package saved: {path}")

    @staticmethod
    def load(path: Union[str, Path]) -> bytes:
        with open(path, "rb") as f:
            return f.read()