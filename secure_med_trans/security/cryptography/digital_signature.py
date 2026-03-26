from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


class DigitalSignature:
    """
    Simple RSA-PSS Digital Signature
    """

    def sign(self, data: bytes, private_key: bytes) -> bytes:
        # Load private key
        key = serialization.load_pem_private_key(
            private_key,
            password=None,
            backend=default_backend()
        )

        signature = key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )

        return signature

    def verify(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        try:
            key = serialization.load_pem_public_key(
                public_key,
                backend=default_backend()
            )

            key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=32
                ),
                hashes.SHA256()
            )

            return True

        except Exception:
            return False