"""
Encryption utilities for secure session storage
"""

import os
import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""
    
    def __init__(self, encryption_key: str):
        """Initialize encryption with a key"""
        self.encryption_key = encryption_key
        self.fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet encryption instance from key"""
        try:
            # Create a consistent salt from the key
            salt = hashlib.sha256(self.encryption_key.encode()).digest()[:16]
            
            # Derive a proper encryption key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Error creating encryption instance: {e}")
            # Fallback to a simpler method
            key = base64.urlsafe_b64encode(
                hashlib.sha256(self.encryption_key.encode()).digest()
            )
            return Fernet(key)
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string data and return bytes"""
        try:
            return self.fernet.encrypt(data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt bytes data and return string"""
        try:
            return self.fernet.decrypt(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def encrypt_file(self, file_path: str, data: str) -> bool:
        """Encrypt data and save to file"""
        try:
            encrypted_data = self.encrypt(data)
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Error encrypting file {file_path}: {e}")
            return False
    
    def decrypt_file(self, file_path: str) -> str:
        """Read and decrypt data from file"""
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            return self.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Error decrypting file {file_path}: {e}")
            raise
    
    @staticmethod
    def generate_key() -> str:
        """Generate a random encryption key"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
    
    def verify_key(self) -> bool:
        """Verify that the encryption key works correctly"""
        try:
            test_data = "test_encryption_data"
            encrypted = self.encrypt(test_data)
            decrypted = self.decrypt(encrypted)
            return decrypted == test_data
        except Exception:
            return False
"""
Professional encryption utilities for secure session and data storage
Uses industry-standard encryption with key derivation
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from config import Config

logger = logging.getLogger(__name__)

class FileEncryption:
    """
    Professional file encryption using Fernet (AES 128 in CBC mode)
    Provides secure encryption and decryption for sensitive data
    """
    
    def __init__(self):
        """Initialize encryption with configuration"""
        self.config = Config()
        self._fernet = None
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption key from configuration"""
        try:
            # Use encryption key from config
            encryption_key = self.config.ENCRYPTION_KEY.encode()
            
            # Derive key using PBKDF2
            salt = b'telegram_bot_salt_2024'  # Static salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key))
            self._fernet = Fernet(key)
            
            logger.info("Encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def save_encrypted_file(self, file_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save data to encrypted file"""
        try:
            # Convert data to JSON
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Encrypt data
            encrypted_data = self._fernet.encrypt(json_data.encode('utf-8'))
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write encrypted data to file
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            logger.debug(f"Encrypted file saved: {file_path}")
            return {'success': True, 'message': 'File saved successfully'}
            
        except Exception as e:
            logger.error(f"Error saving encrypted file {file_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    def load_encrypted_file(self, file_path: str) -> Dict[str, Any]:
        """Load data from encrypted file"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            # Read encrypted data
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            decrypted_data = self._fernet.decrypt(encrypted_data)
            
            # Parse JSON
            data = json.loads(decrypted_data.decode('utf-8'))
            
            logger.debug(f"Encrypted file loaded: {file_path}")
            return {'success': True, 'data': data}
            
        except Exception as e:
            logger.error(f"Error loading encrypted file {file_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    def encrypt_string(self, text: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        try:
            encrypted_data = self._fernet.encrypt(text.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encrypting string: {e}")
            raise
    
    def decrypt_string(self, encrypted_text: str) -> str:
        """Decrypt a base64 encoded encrypted string"""
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
            decrypted_data = self._fernet.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting string: {e}")
            raise
    
    def secure_delete_file(self, file_path: str) -> bool:
        """Securely delete a file by overwriting it first"""
        try:
            if not os.path.exists(file_path):
                return True
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Overwrite with random data multiple times
            with open(file_path, 'r+b') as f:
                for _ in range(3):  # Overwrite 3 times
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally delete the file
            os.remove(file_path)
            
            logger.debug(f"File securely deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error securely deleting file {file_path}: {e}")
            return False
    
    def verify_encryption(self) -> bool:
        """Test encryption/decryption to verify it's working"""
        try:
            test_data = {"test": "encryption_verification", "timestamp": "2024"}
            
            # Test save and load
            temp_file = os.path.join(self.config.SESSIONS_DIR, "test_encryption.tmp")
            
            save_result = self.save_encrypted_file(temp_file, test_data)
            if not save_result['success']:
                return False
            
            load_result = self.load_encrypted_file(temp_file)
            if not load_result['success']:
                return False
            
            # Verify data integrity
            loaded_data = load_result['data']
            if loaded_data != test_data:
                return False
            
            # Clean up test file
            self.secure_delete_file(temp_file)
            
            logger.info("Encryption verification successful")
            return True
            
        except Exception as e:
            logger.error(f"Encryption verification failed: {e}")
            return False

class SessionEncryption(FileEncryption):
    """
    Specialized encryption for Telegram sessions
    Provides additional session-specific security features
    """
    
    def __init__(self):
        super().__init__()
        self.sessions_dir = self.config.SESSIONS_DIR
    
    def save_session_data(self, phone_number: str, session_string: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save session with metadata"""
        try:
            clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            session_file = os.path.join(self.sessions_dir, f"session_{clean_phone}.enc")
            
            session_data = {
                'phone_number': phone_number,
                'session_string': session_string,
                'created_at': metadata.get('created_at') if metadata else None,
                'last_used': metadata.get('last_used') if metadata else None,
                'metadata': metadata or {}
            }
            
            return self.save_encrypted_file(session_file, session_data)
            
        except Exception as e:
            logger.error(f"Error saving session data for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    def load_session_data(self, phone_number: str) -> Dict[str, Any]:
        """Load session with metadata"""
        try:
            clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            session_file = os.path.join(self.sessions_dir, f"session_{clean_phone}.enc")
            
            return self.load_encrypted_file(session_file)
            
        except Exception as e:
            logger.error(f"Error loading session data for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
