"""
RSA Encryptor for Secure Medical Image Transmission System.

This module provides RSA encryption and decryption
for key exchange in hybrid encryption systems.
"""

import secrets
from typing import Tuple, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

from secure_med_trans.utils.logger import get_logger
from secure_med_trans.utils.exceptions import (
    EncryptionException,
    DecryptionException,
    InvalidKeyException,
    KeyGenerationException,
)


logger = get_logger(__name__)


class RSAEncryptor:
    """
    RSA encryption/decryption handler.
    
    Supports RSA-OAEP for encryption and RSA-PSS for signatures.
    """
    
    # Key sizes in bits
    KEY_SIZE_2048 = 2048
    KEY_SIZE_3072 = 3072
    KEY_SIZE_4096 = 4096
    
    # Supported hash algorithms
    HASH_SHA256 = "sha256"
    HASH_SHA512 = "sha512"
    
    def __init__(self, key_size: int = 2048):
        """
        Initialize RSA Encryptor.
        
        Args:
            key_size: Key size in bits (2048, 3072, or 4096).
        """
        if key_size not in [2048, 3072, 4096]:
            raise ValueError("Invalid key size. Must be 2048, 3072, or 4096 bits.")
        
        self._key_size = key_size
        self._initialized = False
        
        logger.debug(f"Initialized RSA-{key_size} encryptor")
    
    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate an RSA key pair.
        
        Returns:
            Tuple of (private_key_pem, public_key_pem).
        
        Raises:
            KeyGenerationException: If key generation fails.
        """
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self._key_size,
                backend=default_backend()
            )
            
            # Serialize private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Serialize public key
            public_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            logger.info(f"Generated RSA-{self._key_size} key pair")
            
            return private_pem, public_pem
            
        except Exception as e:
            logger.error(f"RSA key generation failed: {str(e)}")
            raise KeyGenerationException(f"Key generation failed: {str(e)}")
    
    def encrypt(
        self,
        plaintext: bytes,
        public_key: bytes,
        hash_algorithm: str = "sha256",
    ) -> bytes:
        """
        Encrypt data using RSA-OAEP.
        
        Args:
            plaintext: Data to encrypt (limited by key size).
            public_key: RSA public key in PEM format.
            hash_algorithm: Hash algorithm for OAEP padding.
        
        Returns:
            Encrypted data.
        
        Raises:
            EncryptionException: If encryption fails.
        """
        try:
            # Load public key
            if isinstance(public_key, bytes):
                pub_key = serialization.load_pem_public_key(
                    public_key,
                    backend=default_backend()
                )
            else:
                pub_key = public_key
            
            # Select hash algorithm
            hash_algo = self._get_hash_algorithm(hash_algorithm)
            
            # Encrypt with OAEP padding
            ciphertext = pub_key.encrypt(
                plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hash_algo),
                    algorithm=hash_algo,
                    label=None
                )
            )
            
            logger.debug(f"RSA-OAEP encrypted {len(plaintext)} bytes")
            
            return ciphertext
            
        except Exception as e:
            logger.error(f"RSA encryption failed: {str(e)}")
            raise EncryptionException(f"Encryption failed: {str(e)}")
    
    def decrypt(
        self,
        ciphertext: bytes,
        private_key: bytes,
        hash_algorithm: str = "sha256",
    ) -> bytes:
        """
        Decrypt data using RSA-OAEP.
        
        Args:
            ciphertext: Encrypted data.
            private_key: RSA private key in PEM format.
            hash_algorithm: Hash algorithm for OAEP padding.
        
        Returns:
            Decrypted data.
        
        Raises:
            DecryptionException: If decryption fails.
        """
        try:
            # Load private key
            if isinstance(private_key, bytes):
                priv_key = serialization.load_pem_private_key(
                    private_key,
                    password=None,
                    backend=default_backend()
                )
            else:
                priv_key = private_key
            
            # Select hash algorithm
            hash_algo = self._get_hash_algorithm(hash_algorithm)
            
            # Decrypt with OAEP padding
            plaintext = priv_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hash_algo),
                    algorithm=hash_algo,
                    label=None
                )
            )
            
            logger.debug(f"RSA-OAEP decrypted {len(ciphertext)} bytes")
            
            return plaintext
            
        except Exception as e:
            logger.error(f"RSA decryption failed: {str(e)}")
            raise DecryptionException(f"Decryption failed: {str(e)}")
    
    def get_max_encrypt_size(self) -> int:
        """
        Get maximum data size that can be encrypted with OAEP.
        
        Returns:
            Maximum plaintext size in bytes.
        """
        # For RSA-2048 with SHA-256:
        # key_size - 2 * hash_size - 2 = 2048 - 2*32 - 2 = 1982 bytes
        # Using a more conservative estimate
        hash_size = 32  # SHA-256
        return (self._key_size // 8) - 2 * hash_size - 2
    
    def _get_hash_algorithm(self, name: str):
        """Get hash algorithm object from name."""
        if name == "sha256":
            return hashes.SHA256()
        elif name == "sha512":
            return hashes.SHA512()
        else:
            raise ValueError(f"Unsupported hash algorithm: {name}")
    
    @property
    def key_size(self) -> int:
        """Get the configured key size in bits."""
        return self._key_size

