
"""
Enhanced configuration management with multiple owner support
Professional-grade configuration with validation and security
"""

import os
import logging
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Professional configuration manager with validation"""
    
    def __init__(self):
        """Initialize configuration with validation"""
        load_dotenv()
        self._validate_and_load_config()
    
    def _validate_and_load_config(self):
        """Validate and load all configuration parameters"""
        try:
            # Telegram API Configuration
            self.API_ID = self._get_required_int('API_ID')
            self.API_HASH = self._get_required_str('API_HASH')
            self.BOT_TOKEN = self._get_required_str('BOT_TOKEN')
            
            # Owner Configuration with multiple owner support
            self.OWNER_IDS = self._parse_owner_ids()
            
            # Encryption Configuration
            self.ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default_encryption_key_change_in_production')
            
            # Directory Configuration
            self.SESSIONS_DIR = os.getenv('SESSIONS_DIR', 'sessions')
            
            # Logging Configuration
            self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
            self.LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
            
            # Broadcasting Configuration
            self.BROADCAST_DELAY = float(os.getenv('BROADCAST_DELAY', '1.0'))
            self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
            
            # Validation
            self._validate_config()
            
            # Create directories
            self._ensure_directories()
            
            logger.info("Configuration loaded and validated successfully")
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}")
    
    def _parse_owner_ids(self) -> List[int]:
        """Parse owner IDs from environment variables with multiple owner support"""
        owner_ids = []
        
        # Try new OWNER_IDS format (supports multiple owners)
        owner_ids_str = os.getenv('OWNER_IDS', '').strip()
        if owner_ids_str:
            try:
                # Parse comma-separated owner IDs
                ids = [id.strip() for id in owner_ids_str.split(',') if id.strip()]
                owner_ids = [int(id) for id in ids if id.isdigit()]
                
                if owner_ids:
                    logger.info(f"Loaded {len(owner_ids)} owner ID(s) from OWNER_IDS")
                    return owner_ids
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing OWNER_IDS: {e}")
        
        # Fallback to legacy OWNER_ID format (single owner)
        owner_id_str = os.getenv('OWNER_ID', '').strip()
        if owner_id_str:
            try:
                owner_id = int(owner_id_str)
                owner_ids = [owner_id]
                logger.info("Loaded single owner ID from OWNER_ID (legacy format)")
                return owner_ids
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing OWNER_ID: {e}")
        
        # No valid owner IDs found
        raise ValueError("No valid OWNER_IDS or OWNER_ID found in environment variables")
    
    def _get_required_str(self, key: str) -> str:
        """Get required string environment variable"""
        value = os.getenv(key, '').strip()
        if not value:
            raise ValueError(f"Required environment variable {key} is missing or empty")
        return value
    
    def _get_required_int(self, key: str) -> int:
        """Get required integer environment variable"""
        value = os.getenv(key, '').strip()
        if not value:
            raise ValueError(f"Required environment variable {key} is missing or empty")
        
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be a valid integer")
    
    def _validate_config(self):
        """Validate configuration parameters"""
        # Validate API_ID
        if not isinstance(self.API_ID, int) or self.API_ID <= 0:
            raise ValueError("API_ID must be a positive integer")
        
        # Validate API_HASH
        if not isinstance(self.API_HASH, str) or len(self.API_HASH) < 10:
            raise ValueError("API_HASH must be a valid string")
        
        # Validate BOT_TOKEN
        if not isinstance(self.BOT_TOKEN, str) or ':' not in self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN must be a valid Telegram bot token")
        
        # Validate OWNER_IDS
        if not self.OWNER_IDS or not all(isinstance(id, int) and id > 0 for id in self.OWNER_IDS):
            raise ValueError("OWNER_IDS must contain at least one valid positive integer")
        
        # Validate delays and retries
        if self.BROADCAST_DELAY < 0:
            raise ValueError("BROADCAST_DELAY must be non-negative")
        
        if self.MAX_RETRIES < 1:
            raise ValueError("MAX_RETRIES must be at least 1")
        
        logger.info("All configuration parameters validated successfully")
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        try:
            os.makedirs(self.SESSIONS_DIR, exist_ok=True)
            
            # Create subdirectories
            subdirs = ['database', 'database/groups', 'database/metadata']
            for subdir in subdirs:
                os.makedirs(os.path.join(self.SESSIONS_DIR, subdir), exist_ok=True)
            
            logger.info(f"Directory structure created: {self.SESSIONS_DIR}")
            
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging (without sensitive data)"""
        return {
            'api_id_set': bool(self.API_ID),
            'api_hash_set': bool(self.API_HASH),
            'bot_token_set': bool(self.BOT_TOKEN),
            'owner_count': len(self.OWNER_IDS),
            'sessions_dir': self.SESSIONS_DIR,
            'log_level': self.LOG_LEVEL,
            'broadcast_delay': self.BROADCAST_DELAY,
            'max_retries': self.MAX_RETRIES
        }
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user ID is in the list of authorized owners"""
        return user_id in self.OWNER_IDS
    
    def add_owner(self, user_id: int) -> bool:
        """Add a new owner ID (runtime only, not persistent)"""
        if user_id not in self.OWNER_IDS:
            self.OWNER_IDS.append(user_id)
            logger.info(f"Added new owner ID: {user_id}")
            return True
        return False
    
    def remove_owner(self, user_id: int) -> bool:
        """Remove an owner ID (runtime only, not persistent)"""
        if user_id in self.OWNER_IDS and len(self.OWNER_IDS) > 1:
            self.OWNER_IDS.remove(user_id)
            logger.info(f"Removed owner ID: {user_id}")
            return True
        return False
    
    @property
    def OWNER_ID(self) -> int:
        """Legacy compatibility - return first owner ID"""
        return self.OWNER_IDS[0] if self.OWNER_IDS else 0
