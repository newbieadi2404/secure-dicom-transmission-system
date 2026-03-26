class DICOMHandlerException(Exception):
    pass


class EncryptionException(Exception):
    pass


class DecryptionException(Exception):
    pass


class InvalidPackageException(Exception):
    pass


# 🔥 Missing ones (this caused your crash)

class InvalidKeyException(Exception):
    pass


class KeyGenerationException(Exception):
    pass


class SignatureException(Exception):
    pass


class SignatureCreationException(Exception):
    pass


class SignatureVerificationException(Exception):
    pass