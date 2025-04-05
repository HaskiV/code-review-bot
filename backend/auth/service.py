import hashlib
import secrets
from typing import Tuple, Dict, Optional, Any
import json
from pathlib import Path
from flask_jwt_extended import create_access_token

class AuthService:
    """Сервис для аутентификации и авторизации пользователей"""
    
    def __init__(self, users_file=None):
        """
        Инициализация сервиса аутентификации
        
        Args:
            users_file: Путь к файлу с пользователями
        """
        self.users_file = users_file or Path(__file__).parent.parent / "data" / "users.json"
        self.users = {}
        self.load_users()
    
    def load_users(self):
        """Загрузка пользователей из файла"""
        if self.users_file.exists():
            try:
                with open(self.users_file, "r") as f:
                    self.users = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки пользователей: {str(e)}")
                # Создаем администратора по умолчанию
                self._create_default_admin()
        else:
            # Создаем администратора по умолчанию
            self._create_default_admin()
    
    def _create_default_admin(self):
        """Создание администратора по умолчанию"""
        admin_id = "admin"
        password = "admin"  # В реальном проекте использовать сильный пароль
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        
        self.users[admin_id] = {
            "id": admin_id,
            "password_hash": password_hash,
            "salt": salt,
            "role": "admin",
            "api_keys": {
                "default": self._generate_api_key()
            }
        }
        
        self.save_users()
    
    def save_users(self):
        """Сохранение пользователей в файл"""
        try:
            # Создаем директорию, если она не существует
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.users_file, "w") as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения пользователей: {str(e)}")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """
        Хеширование пароля с использованием соли
        
        Args:
            password: Пароль
            salt: Соль
            
        Returns:
            Хеш пароля
        """
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_api_key(self) -> str:
        """
        Генерация API ключа
        
        Returns:
            API ключ
        """
        return secrets.token_hex(32)
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Аутентификация пользователя по имени и паролю
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            Кортеж (успех, пользователь)
        """
        if username not in self.users:
            return False, None
        
        user = self.users[username]
        salt = user["salt"]
        password_hash = self._hash_password(password, salt)
        
        if password_hash != user["password_hash"]:
            return False, None
        
        return True, user
    
    def authenticate_with_api_key(self, api_key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Аутентификация пользователя по API ключу
        
        Args:
            api_key: API ключ
            
        Returns:
            Кортеж (успех, пользователь)
        """
        for user_id, user_data in self.users.items():
            for key_name, key_value in user_data.get("api_keys", {}).items():
                if key_value == api_key:
                    return True, user_data
        
        return False, None
    
    def create_access_token(self, user_id: str) -> str:
        """
        Создание JWT токена для пользователя
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            JWT токен
        """
        return create_access_token(identity=user_id)