import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_med_trans.security.cryptography.aes_encryptor import AESEncryptor
from secure_med_trans.security.cryptography.rsa_encryptor import RSAEncryptor
from secure_med_trans.security.cryptography.digital_signature import DigitalSignature

class TestCryptography(unittest.TestCase):
    def test_aes_encryption_decryption(self):
        key = AESEncryptor.generate_key()
        encryptor = AESEncryptor(key)
        data = b"Sensitive medical data"
        
        encrypted_data, nonce, tag = encryptor.encrypt(data)
        decrypted_data = encryptor.decrypt(encrypted_data, nonce, tag)
        
        self.assertEqual(data, decrypted_data)

    def test_rsa_key_generation_and_encryption(self):
        priv_key, pub_key = RSAEncryptor.generate_key_pair()
        
        encryptor = RSAEncryptor(pub_key, priv_key)
        data = b"Secret AES Key"
        
        encrypted_data = encryptor.encrypt(data)
        decrypted_data = encryptor.decrypt(encrypted_data)
        
        self.assertEqual(data, decrypted_data)

    def test_digital_signature(self):
        priv_key, pub_key = RSAEncryptor.generate_key_pair()
        data = b"Important medical record"
        
        signature = DigitalSignature.sign(data, priv_key)
        is_valid = DigitalSignature.verify(data, signature, pub_key)
        
        self.assertTrue(is_valid)

if __name__ == '__main__':
    unittest.main()
