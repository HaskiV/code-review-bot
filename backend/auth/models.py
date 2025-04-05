"""Модели пользователей для аутентификации."""
import uuid
import hashlib
import os
from datetime import datetime

class User:
    """Модель пользователя для аутентификации."""
    
    def __init__(self, username, password_hash, email=None, api_key=None, role="user"):
        """Инициализация пользователя."""
        self.id = str(uuid.uuid4())
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.api_key = api_key or self._generate_api_key()
        self.role = role
        self.created_at = datetime.now()
        self.last_login = None
    
    @staticmethod
    def hash_password(password, salt=None):
        """Хеширование пароля с солью."""
        salt = salt or os.urandom(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return salt + password_hash
    
    @staticmethod
    def verify_password(password, password_hash):
        """Проверка пароля по хешу."""
        salt = password_hash[:32]
        stored_hash = password_hash[32:]
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return new_hash == stored_hash
    
    def _generate_api_key(self):
        """Генерация уникального API-ключа."""
        return str(uuid.uuid4())