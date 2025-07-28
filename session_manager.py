"""
Session management for storing and retrieving Telegram sessions
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from config import Config
from encryption import EncryptionManager

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages Telegram session storage and retrieval"""
    
    def __init__(self):
        self.config = Config()
        self.encryption = EncryptionManager(self.config.ENCRYPTION_KEY)
        
        # Ensure sessions directory exists
        os.makedirs(self.config.SESSIONS_DIR, exist_ok=True)
        
        # Load existing sessions index
        self.sessions_index_file = os.path.join(self.config.SESSIONS_DIR, "sessions_index.enc")
        self.sessions_index = self._load_sessions_index()
    
    def _load_sessions_index(self) -> Dict[str, Any]:
        """Load the sessions index from encrypted file"""
        try:
            if os.path.exists(self.sessions_index_file):
                encrypted_data = self._read_file(self.sessions_index_file)
                decrypted_data = self.encryption.decrypt(encrypted_data)
                return json.loads(decrypted_data)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading sessions index: {e}")
            return {}
    
    def _save_sessions_index(self) -> bool:
        """Save the sessions index to encrypted file"""
        try:
            index_json = json.dumps(self.sessions_index, indent=2)
            encrypted_data = self.encryption.encrypt(index_json)
            self._write_file(self.sessions_index_file, encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Error saving sessions index: {e}")
            return False
    
    def _read_file(self, file_path: str) -> bytes:
        """Read binary data from file"""
        with open(file_path, 'rb') as f:
            return f.read()
    
    def _write_file(self, file_path: str, data: bytes) -> None:
        """Write binary data to file"""
        with open(file_path, 'wb') as f:
            f.write(data)
    
    def save_session(self, phone_number: str, session_string: str) -> Dict[str, Any]:
        """Save a Telegram session securely"""
        try:
            # Prepare session data
            session_data = {
                'phone_number': phone_number,
                'session_string': session_string,
                'created_at': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat()
            }
            
            # Encrypt and save session file
            session_json = json.dumps(session_data, indent=2)
            encrypted_data = self.encryption.encrypt(session_json)
            
            session_file_path = self.config.get_session_file_path(phone_number)
            self._write_file(session_file_path, encrypted_data)
            
            # Update sessions index
            self.sessions_index[phone_number] = {
                'file_path': session_file_path,
                'created_at': session_data['created_at'],
                'last_used': session_data['last_used']
            }
            
            # Save index
            if self._save_sessions_index():
                logger.info(f"Session saved successfully for {phone_number}")
                return {'success': True, 'message': 'Session saved successfully'}
            else:
                return {'success': False, 'error': 'Failed to save sessions index'}
                
        except Exception as e:
            logger.error(f"Error saving session for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    def load_session(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Load a Telegram session"""
        try:
            if phone_number not in self.sessions_index:
                return None
            
            session_file_path = self.sessions_index[phone_number]['file_path']
            
            if not os.path.exists(session_file_path):
                logger.warning(f"Session file not found for {phone_number}")
                # Clean up index
                del self.sessions_index[phone_number]
                self._save_sessions_index()
                return None
            
            # Read and decrypt session data
            encrypted_data = self._read_file(session_file_path)
            decrypted_data = self.encryption.decrypt(encrypted_data)
            session_data = json.loads(decrypted_data)
            
            # Update last used timestamp
            session_data['last_used'] = datetime.now().isoformat()
            self.sessions_index[phone_number]['last_used'] = session_data['last_used']
            
            # Save updated session
            session_json = json.dumps(session_data, indent=2)
            encrypted_data = self.encryption.encrypt(session_json)
            self._write_file(session_file_path, encrypted_data)
            self._save_sessions_index()
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error loading session for {phone_number}: {e}")
            return None
    
    def session_exists(self, phone_number: str) -> bool:
        """Check if a session exists for the given phone number"""
        return phone_number in self.sessions_index
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored sessions"""
        sessions = {}
        
        for phone_number in list(self.sessions_index.keys()):
            session_data = self.load_session(phone_number)
            if session_data:
                sessions[phone_number] = session_data
            else:
                # Clean up invalid session from index
                logger.warning(f"Removing invalid session {phone_number} from index")
                del self.sessions_index[phone_number]
        
        # Save cleaned index
        self._save_sessions_index()
        
        return sessions
    
    def remove_session(self, phone_number: str) -> Dict[str, Any]:
        """Remove a session and clean up all related data"""
        try:
            if phone_number not in self.sessions_index:
                return {'success': False, 'error': f'No session found for {phone_number}'}
            
            # Get session file path
            session_file_path = self.sessions_index[phone_number]['file_path']
            
            # Remove session file
            if os.path.exists(session_file_path):
                os.remove(session_file_path)
                logger.info(f"Session file removed: {session_file_path}")
            
            # Remove from index
            del self.sessions_index[phone_number]
            
            # Save updated index
            if self._save_sessions_index():
                logger.info(f"Session removed successfully for {phone_number}")
                return {'success': True, 'message': f'Session for {phone_number} removed successfully'}
            else:
                return {'success': False, 'error': 'Failed to update sessions index'}
                
        except Exception as e:
            logger.error(f"Error removing session for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    def clear_all_sessions(self) -> Dict[str, Any]:
        """Remove all sessions and clean up all data"""
        try:
            removed_count = 0
            
            # Remove all session files
            for phone_number in list(self.sessions_index.keys()):
                session_file_path = self.sessions_index[phone_number]['file_path']
                
                if os.path.exists(session_file_path):
                    os.remove(session_file_path)
                    removed_count += 1
                    logger.info(f"Session file removed: {session_file_path}")
            
            # Clear index
            self.sessions_index.clear()
            
            # Remove index file
            if os.path.exists(self.sessions_index_file):
                os.remove(self.sessions_index_file)
            
            logger.info(f"All sessions cleared. Removed {removed_count} session files.")
            return {'success': True, 'message': f'All sessions cleared. Removed {removed_count} sessions.'}
            
        except Exception as e:
            logger.error(f"Error clearing all sessions: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_count(self) -> int:
        """Get the number of active sessions"""
        return len(self.sessions_index)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get summary information about all sessions"""
        sessions = self.get_all_sessions()
        
        info = {
            'total_sessions': len(sessions),
            'sessions': []
        }
        
        for phone_number, session_data in sessions.items():
            info['sessions'].append({
                'phone_number': phone_number,
                'created_at': session_data.get('created_at', 'Unknown'),
                'last_used': session_data.get('last_used', 'Unknown')
            })
        
        return info
"""
Professional session management with encryption and MongoDB integration
Handles secure storage and retrieval of Telegram sessions
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pyrogram import Client
from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded

from config import Config
from encryption import FileEncryption

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Professional session manager with encryption and database integration
    Handles secure storage, retrieval, and management of Telegram sessions
    """
    
    def __init__(self):
        """Initialize session manager"""
        self.config = Config()
        self.encryption = FileEncryption()
        self.sessions_dir = self.config.SESSIONS_DIR
        self.sessions_index_file = os.path.join(self.sessions_dir, "sessions_index.enc")
        
        # Ensure directories exist
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        logger.info("Session manager initialized successfully")
    
    async def save_session(self, phone_number: str, session_string: str) -> Dict[str, Any]:
        """Save encrypted session with metadata"""
        try:
            # Generate session filename
            clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            session_file = os.path.join(self.sessions_dir, f"session_{clean_phone}.enc")
            
            # Prepare session data
            session_data = {
                'phone_number': phone_number,
                'session_string': session_string,
                'created_at': datetime.utcnow().isoformat(),
                'last_used': datetime.utcnow().isoformat(),
                'status': 'active',
                'session_type': 'string_session'
            }
            
            # Encrypt and save session
            save_result = self.encryption.save_encrypted_file(session_file, session_data)
            
            if save_result['success']:
                # Update sessions index
                await self._update_sessions_index(phone_number, {
                    'file_path': session_file,
                    'phone_number': phone_number,
                    'created_at': session_data['created_at'],
                    'status': 'active'
                })
                
                logger.info(f"Session saved successfully for {phone_number}")
                return {
                    'success': True,
                    'message': f'Session saved for {phone_number}',
                    'file_path': session_file
                }
            else:
                return {'success': False, 'error': save_result.get('error', 'Failed to save session')}
            
        except Exception as e:
            logger.error(f"Error saving session for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_session(self, phone_number: str) -> Optional[str]:
        """Get session string for a phone number"""
        try:
            clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            session_file = os.path.join(self.sessions_dir, f"session_{clean_phone}.enc")
            
            if not os.path.exists(session_file):
                return None
            
            # Load and decrypt session
            load_result = self.encryption.load_encrypted_file(session_file)
            
            if load_result['success']:
                session_data = load_result['data']
                
                # Update last used timestamp
                session_data['last_used'] = datetime.utcnow().isoformat()
                self.encryption.save_encrypted_file(session_file, session_data)
                
                return session_data.get('session_string')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session for {phone_number}: {e}")
            return None
    
    async def get_full_session_data(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get full session data including metadata"""
        try:
            clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            session_file = os.path.join(self.sessions_dir, f"session_{clean_phone}.enc")
            
            if not os.path.exists(session_file):
                return None
            
            # Load and decrypt session
            load_result = self.encryption.load_encrypted_file(session_file)
            
            if load_result['success']:
                session_data = load_result['data']
                
                # Update last used timestamp
                session_data['last_used'] = datetime.utcnow().isoformat()
                self.encryption.save_encrypted_file(session_file, session_data)
                
                return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting full session data for {phone_number}: {e}")
            return None
    
    async def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions with full session data"""
        try:
            sessions = {}
            
            # Load sessions index
            index_data = await self._load_sessions_index()
            
            for phone_number, session_info in index_data.items():
                if session_info.get('status') == 'active':
                    session_data = await self.get_full_session_data(phone_number)
                    if session_data:
                        sessions[phone_number] = session_data
            
            logger.info(f"Retrieved {len(sessions)} active sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting all sessions: {e}")
            return {}
    
    async def remove_session(self, phone_number: str) -> Dict[str, Any]:
        """Remove a session securely"""
        try:
            clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            session_file = os.path.join(self.sessions_dir, f"session_{clean_phone}.enc")
            
            # Check if session exists
            if not os.path.exists(session_file):
                return {'success': False, 'error': 'Session not found'}
            
            # Remove session file
            os.remove(session_file)
            
            # Update sessions index
            await self._remove_from_sessions_index(phone_number)
            
            logger.info(f"Session removed successfully for {phone_number}")
            return {
                'success': True,
                'message': f'Session removed for {phone_number}'
            }
            
        except Exception as e:
            logger.error(f"Error removing session for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def clear_all_sessions(self) -> Dict[str, Any]:
        """Clear all sessions securely"""
        try:
            removed_count = 0
            
            # Get all sessions
            index_data = await self._load_sessions_index()
            
            # Remove all session files
            for phone_number, session_info in index_data.items():
                try:
                    session_file = session_info.get('file_path')
                    if session_file and os.path.exists(session_file):
                        os.remove(session_file)
                        removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove session file for {phone_number}: {e}")
            
            # Clear sessions index
            await self._clear_sessions_index()
            
            logger.info(f"All sessions cleared successfully: {removed_count} removed")
            return {
                'success': True,
                'message': f'All sessions cleared successfully',
                'removed_count': removed_count
            }
            
        except Exception as e:
            logger.error(f"Error clearing all sessions: {e}")
            return {'success': False, 'error': str(e)}
    
    async def validate_session(self, phone_number: str) -> Dict[str, Any]:
        """Validate if a session is still active"""
        try:
            session_string = await self.get_session(phone_number)
            
            if not session_string:
                return {'valid': False, 'error': 'Session not found'}
            
            # Test session by creating temporary client
            test_client = Client(
                f"test_{phone_number.replace('+', '')}",
                session_string=session_string,
                api_id=self.config.API_ID,
                api_hash=self.config.API_HASH
            )
            
            try:
                await test_client.start()
                me = await test_client.get_me()
                await test_client.stop()
                
                return {
                    'valid': True,
                    'user_info': {
                        'id': me.id,
                        'first_name': me.first_name,
                        'username': me.username
                    }
                }
                
            except AuthKeyUnregistered:
                # Session is invalid, remove it
                await self.remove_session(phone_number)
                return {'valid': False, 'error': 'Session expired and removed'}
            
            except Exception as e:
                return {'valid': False, 'error': f'Validation failed: {str(e)}'}
            
        except Exception as e:
            logger.error(f"Error validating session for {phone_number}: {e}")
            return {'valid': False, 'error': str(e)}
    
    async def get_sessions_info(self) -> Dict[str, Any]:
        """Get comprehensive information about all sessions"""
        try:
            sessions_info = {}
            index_data = await self._load_sessions_index()
            
            for phone_number, session_info in index_data.items():
                sessions_info[phone_number] = {
                    'phone_number': phone_number,
                    'status': session_info.get('status', 'unknown'),
                    'created_at': session_info.get('created_at'),
                    'file_exists': os.path.exists(session_info.get('file_path', ''))
                }
            
            return {
                'success': True,
                'sessions': sessions_info,
                'total_sessions': len(sessions_info),
                'active_sessions': len([s for s in sessions_info.values() if s['status'] == 'active'])
            }
            
        except Exception as e:
            logger.error(f"Error getting sessions info: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _load_sessions_index(self) -> Dict[str, Any]:
        """Load sessions index from encrypted file"""
        try:
            if not os.path.exists(self.sessions_index_file):
                return {}
            
            load_result = self.encryption.load_encrypted_file(self.sessions_index_file)
            
            if load_result['success']:
                return load_result['data']
            
            return {}
            
        except Exception as e:
            logger.warning(f"Error loading sessions index: {e}")
            return {}
    
    async def _update_sessions_index(self, phone_number: str, session_info: Dict[str, Any]):
        """Update sessions index with new session info"""
        try:
            index_data = await self._load_sessions_index()
            index_data[phone_number] = session_info
            
            save_result = self.encryption.save_encrypted_file(self.sessions_index_file, index_data)
            
            if not save_result['success']:
                logger.error(f"Failed to update sessions index: {save_result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error updating sessions index: {e}")
    
    async def _remove_from_sessions_index(self, phone_number: str):
        """Remove session from index"""
        try:
            index_data = await self._load_sessions_index()
            
            if phone_number in index_data:
                del index_data[phone_number]
                
                save_result = self.encryption.save_encrypted_file(self.sessions_index_file, index_data)
                
                if not save_result['success']:
                    logger.error(f"Failed to update sessions index after removal: {save_result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error removing from sessions index: {e}")
    
    async def _clear_sessions_index(self):
        """Clear all sessions from index"""
        try:
            if os.path.exists(self.sessions_index_file):
                os.remove(self.sessions_index_file)
            
        except Exception as e:
            logger.error(f"Error clearing sessions index: {e}")
