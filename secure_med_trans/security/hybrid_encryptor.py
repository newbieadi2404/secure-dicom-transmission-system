from typing import Dict, Any
from secure_med_trans.security.cryptography.aes_encryptor import AESEncryptor
from secure_med_trans.security.cryptography.rsa_encryptor import RSAEncryptor


class HybridEncryptor:

    def __init__(self):
        self.aes = AESEncryptor(256)
        self.rsa = RSAEncryptor(2048)

    # -----------------------------
    # 🔐 ENCRYPT
    # -----------------------------
    def encrypt(self, data: bytes, public_key: bytes) -> Dict[str, Any]:
        if not isinstance(data, bytes):
            raise ValueError("Data must be bytes")

        # Generate AES key
        aes_key = self.aes.generate_key()

        # Encrypt data
        ciphertext, nonce, tag = self.aes.encrypt(data, aes_key)

        # Encrypt AES key
        encrypted_key = self.rsa.encrypt(aes_key, public_key)

        return {
            "version": 1,
            "algorithm": "hybrid-aes256-rsa2048",
            "encrypted_key": encrypted_key,
            "nonce": nonce,
            "tag": tag,
            "ciphertext": ciphertext,
        }

    # -----------------------------
    # 🔐 DECRYPT
    # -----------------------------
    def decrypt(self, package: Dict[str, Any], private_key: bytes) -> bytes:
        required_fields = ["encrypted_key", "nonce", "tag", "ciphertext"]

        for field in required_fields:
            if field not in package:
                raise ValueError(f"Missing field: {field}")

        # Decrypt AES key
        aes_key = self.rsa.decrypt(package["encrypted_key"], private_key)

        # Decrypt data
        plaintext = self.aes.decrypt(
            package["ciphertext"],
            aes_key,
            package["nonce"],
            package["tag"]
        )

        return plaintext