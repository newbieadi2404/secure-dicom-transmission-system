"""
AES Encryptor for Secure Medical Image Transmission System.

This module provides AES-256-GCM encryption and decryption
for protecting medical image pixel data.
"""

import secrets
from typing import Tuple, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

from secure_med_trans.utils.logger import get_logger
from secure_med_trans.utils.exceptions import EncryptionException, DecryptionException


logger = get_logger(__name__)


class AESEncryptor:
    """
    AES-256-GCM encryption/decryption handler.
    
    Uses Galois/Counter Mode (GCM) which provides both
    confidentiality and integrity through authentication tags.
    """
    
    # Key sizes in bits
    KEY_SIZE_128 = 16
    KEY_SIZE_192 = 24
    KEY_SIZE_256 = 32
    
    # Nonce size in bytes (96 bits recommended for GCM)
    NONCE_SIZE = 12
    
    # Auth tag size in bytes (128 bits)
    TAG_SIZE = 16
    
    def __init__(self, key_size: int = 256):
        """
        Initialize AES Encryptor.
        
        Args:
            key_size: Key size in bits (128, 192, or 256).
        """
        if key_size not in [128, 192, 256]:
            raise ValueError("Invalid key size. Must be 128, 192, or 256 bits.")
        
        self._key_size = key_size
        self._key_bytes = key_size // 8
        self._initialized = False
        
        logger.debug(f"Initialized AES-{key_size}-GCM encryptor")
    
    def generate_key(self) -> bytes:
        """
        Generate a random AES key.
        
        Returns:
            Random key bytes.
        """
        return secrets.token_bytes(self._key_bytes)
    
    def encrypt(
        self,
        plaintext: bytes,
        key: bytes,
        nonce: Optional[bytes] = None,
        additional_data: Optional[bytes] = None,
    ) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt.
            key: AES key (must match configured key size).
            nonce: Nonce/IV (if None, generated randomly).
            additional_data: Additional authenticated data (optional).
        
        Returns:
            Tuple of (ciphertext, nonce, auth_tag).
        
        Raises:
            EncryptionException: If encryption fails.
        """
        try:
            # Validate key size
            if len(key) != self._key_bytes:
                raise EncryptionException(
                    f"Invalid key size: expected {self._key_bytes}, got {len(key)}"
                )
            
            # Generate nonce if not provided
            if nonce is None:
                nonce = secrets.token_bytes(self.NONCE_SIZE)
            elif len(nonce) != self.NONCE_SIZE:
                raise EncryptionException(
                    f"Invalid nonce size: expected {self.NONCE_SIZE}, got {len(nonce)}"
                )
            
            # Create AES-GCM cipher
            aesgcm = AESGCM(key)
            
            # Encrypt
            aad = additional_data if additional_data else b''
            ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, aad)
            
            # Split ciphertext and auth tag
            ciphertext = ciphertext_with_tag[:-self.TAG_SIZE]
            auth_tag = ciphertext_with_tag[-self.TAG_SIZE:]
            
            logger.debug(
                f"Encrypted {len(plaintext)} bytes to {len(ciphertext)} bytes "
                f"with AES-{self._key_size}-GCM"
            )
            
            return ciphertext, nonce, auth_tag
            
        except EncryptionException:
            raise
        except Exception as e:
            logger.error(f"AES encryption failed: {str(e)}")
            raise EncryptionException(f"Encryption failed: {str(e)}")
    
    def decrypt(
        self,
        ciphertext: bytes,
        key: bytes,
        nonce: bytes,
        auth_tag: bytes,
        additional_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            ciphertext: Encrypted data.
            key: AES key.
            nonce: Nonce used during encryption.
            auth_tag: Authentication tag.
            additional_data: Additional authenticated data (optional).
        
        Returns:
            Decrypted plaintext.
        
        Raises:
            DecryptionException: If decryption fails.
        """
        try:
            # Validate key size
            if len(key) != self._key_bytes:
                raise DecryptionException(
                    f"Invalid key size: expected {self._key_bytes}, got {len(key)}"
                )
            
            # Create AES-GCM cipher
            aesgcm = AESGCM(key)
            
            # Reconstruct ciphertext with tag
            ciphertext_with_tag = ciphertext + auth_tag
            
            # Decrypt
            aad = additional_data if additional_data else b''
            plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, aad)
            
            logger.debug(
                f"Decrypted {len(ciphertext)} bytes to {len(plaintext)} bytes"
            )
            
            return plaintext
            
        except Exception as e:
            logger.error(f"AES decryption failed: {str(e)}")
            raise DecryptionException(f"Decryption failed: {str(e)}")
    
    def encrypt_in_place(
        self,
        data: bytes,
        key: bytes,
        additional_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Encrypt data with auto-generated nonce.
        
        Args:
            data: Data to encrypt.
            key: AES key.
            additional_data: Additional authenticated data (optional).
        
        Returns:
            Complete encrypted package (nonce + ciphertext + tag).
        """
        ciphertext, nonce, auth_tag = self.encrypt(
            data, key, additional_data=additional_data
        )
        
        return nonce + ciphertext + auth_tag
    
    def decrypt_in_place(
        self,
        encrypted_package: bytes,
        key: bytes,
        additional_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt a complete encrypted package.
        
        Args:
            encrypted_package: Complete package (nonce + ciphertext + tag).
            key: AES key.
            additional_data: Additional authenticated data (optional).
        
        Returns:
            Decrypted data.
        """
        # Extract components
        nonce = encrypted_package[:self.NONCE_SIZE]
        ciphertext = encrypted_package[self.NONCE_SIZE:-self.TAG_SIZE]
        auth_tag = encrypted_package[-self.TAG_SIZE:]
        
        return self.decrypt(
            ciphertext, key, nonce, auth_tag, additional_data
        )
    
    @property
    def key_size(self) -> int:
        """Get the configured key size in bits."""
        return self._key_size
    
    @property
    def nonce_size(self) -> int:
        """Get the nonce size in bytes."""
        return self.NONCE_SIZE
    
    @property
    def tag_size(self) -> int:
        """Get the authentication tag size in bytes."""
        return self.TAG_SIZE

