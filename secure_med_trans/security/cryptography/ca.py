import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


class CertificateAuthority:

    @staticmethod
    def generate_ca_keys():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        public_key = private_key.public_key()

        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return priv_bytes, pub_bytes

    @staticmethod
    def issue_certificate(identity, public_key_bytes, ca_private_bytes):
        """
        Creates a signed certificate
        """

        # Load CA private key
        private_key = serialization.load_pem_private_key(
            ca_private_bytes,
            password=None
        )

        cert_data = {
            "identity": identity,
            "public_key": base64.b64encode(public_key_bytes).decode()
        }

        cert_json = json.dumps(cert_data, sort_keys=True).encode()

        # Sign certificate
        signature = private_key.sign(
            cert_json,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        certificate = {
            "data": cert_data,
            "signature": base64.b64encode(signature).decode()
        }

        return json.dumps(certificate)

    @staticmethod
    def verify_certificate(cert_json, ca_public_bytes):
        """
        Verify certificate authenticity
        """

        cert = json.loads(cert_json)

        data = cert["data"]
        signature = base64.b64decode(cert["signature"])

        public_key = serialization.load_pem_public_key(ca_public_bytes)

        data_bytes = json.dumps(data, sort_keys=True).encode()

        try:
            public_key.verify(
                signature,
                data_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True, data
        except Exception:
            return False, None