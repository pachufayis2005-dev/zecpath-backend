from cryptography.fernet import Fernet


class EncryptionService:

    KEY = Fernet.generate_key()
    cipher = Fernet(KEY)

    @classmethod
    def encrypt(cls, text):
        return cls.cipher.encrypt(text.encode()).decode()

    @classmethod
    def decrypt(cls, text):
        return cls.cipher.decrypt(text.encode()).decode()
