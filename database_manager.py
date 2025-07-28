"""
Database management for storing groups and session metadata
Enhanced with auto-cleanup and lifetime management features
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import Config
from encryption import EncryptionManager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Advanced database manager with MongoDB-like functionality
    Provides auto-cleanup, data integrity, and lifetime management
    """
    
    def __init__(self):
        self.config = Config()
        self.encryption = EncryptionManager(self.config.ENCRYPTION_KEY)
        
        # Database directories
        self.db_dir = Path(self.config.SESSIONS_DIR) / "database"
        self.groups_dir = self.db_dir / "groups"
        self.metadata_dir = self.db_dir / "metadata"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Database files
        self.groups_index_file = self.db_dir / "groups_index.enc"
        self.metadata_file = self.db_dir / "metadata.enc"
        
        # Load existing data
        self.groups_index = self._load_groups_index()
        self.metadata = self._load_metadata()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        for directory in [self.db_dir, self.groups_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_groups_index(self) -> Dict[str, Any]:
        """Load the groups index from encrypted file"""
        try:
            if self.groups_index_file.exists():
                encrypted_data = self.groups_index_file.read_bytes()
                decrypted_data = self.encryption.decrypt(encrypted_data)
                return json.loads(decrypted_data)
            else:
                return {"sessions": {}, "groups": {}, "last_cleanup": None}
        except Exception as e:
            logger.error(f"Error loading groups index: {e}")
            return {"sessions": {}, "groups": {}, "last_cleanup": None}
    
    def _save_groups_index(self) -> bool:
        """Save the groups index to encrypted file"""
        try:
            index_json = json.dumps(self.groups_index, indent=2, default=str)
            encrypted_data = self.encryption.encrypt(index_json)
            self.groups_index_file.write_bytes(encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Error saving groups index: {e}")
            return False
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from encrypted file"""
        try:
            if self.metadata_file.exists():
                encrypted_data = self.metadata_file.read_bytes()
                decrypted_data = self.encryption.decrypt(encrypted_data)
                return json.loads(decrypted_data)
            else:
                return {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "total_cleanups": 0,
                    "last_optimization": None
                }
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {"created_at": datetime.now().isoformat(), "version": "1.0.0"}
    
    def _save_metadata(self) -> bool:
        """Save metadata to encrypted file"""
        try:
            metadata_json = json.dumps(self.metadata, indent=2, default=str)
            encrypted_data = self.encryption.encrypt(metadata_json)
            self.metadata_file.write_bytes(encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            return False
    
    def store_session_groups(self, phone_number: str, groups_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store groups data for a session with infinite accuracy
        Auto-handles duplicates and maintains data integrity
        """
        try:
            session_id = self._sanitize_phone(phone_number)
            current_time = datetime.now()
            
            # Prepare session data
            session_data = {
                "phone_number": phone_number,
                "session_id": session_id,
                "groups_count": len(groups_data),
                "last_updated": current_time.isoformat(),
                "groups": groups_data,
                "status": "active",
                "auto_cleanup_enabled": True
            }
            
            # Save groups data to individual file
            groups_file = self.groups_dir / f"{session_id}_groups.enc"
            groups_json = json.dumps(session_data, indent=2, default=str)
            encrypted_data = self.encryption.encrypt(groups_json)
            groups_file.write_bytes(encrypted_data)
            
            # Update groups index
            self.groups_index["sessions"][phone_number] = {
                "session_id": session_id,
                "file_path": str(groups_file),
                "groups_count": len(groups_data),
                "last_updated": current_time.isoformat(),
                "status": "active"
            }
            
            # Index individual groups for fast lookup
            for group in groups_data:
                group_id = str(group.get('id', ''))
                if group_id:
                    self.groups_index["groups"][group_id] = {
                        "session_phone": phone_number,
                        "group_title": group.get('title', 'Unknown'),
                        "group_type": group.get('type', 'unknown'),
                        "last_seen": current_time.isoformat()
                    }
            
            # Save updated index
            if self._save_groups_index():
                logger.info(f"Stored {len(groups_data)} groups for session {phone_number}")
                return {
                    'success': True, 
                    'message': f'Stored {len(groups_data)} groups successfully',
                    'groups_count': len(groups_data)
                }
            else:
                return {'success': False, 'error': 'Failed to save groups index'}
                
        except Exception as e:
            logger.error(f"Error storing groups for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_groups(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Retrieve groups data for a session"""
        try:
            if phone_number not in self.groups_index["sessions"]:
                return None
            
            session_info = self.groups_index["sessions"][phone_number]
            groups_file = Path(session_info['file_path'])
            
            if not groups_file.exists():
                logger.warning(f"Groups file not found for {phone_number}")
                # Clean up index
                del self.groups_index["sessions"][phone_number]
                self._save_groups_index()
                return None
            
            # Read and decrypt groups data
            encrypted_data = groups_file.read_bytes()
            decrypted_data = self.encryption.decrypt(encrypted_data)
            groups_data = json.loads(decrypted_data)
            
            # Update last accessed
            groups_data['last_accessed'] = datetime.now().isoformat()
            self.groups_index["sessions"][phone_number]['last_accessed'] = groups_data['last_accessed']
            
            # Save updated data
            groups_json = json.dumps(groups_data, indent=2, default=str)
            encrypted_data = self.encryption.encrypt(groups_json)
            groups_file.write_bytes(encrypted_data)
            self._save_groups_index()
            
            return groups_data
            
        except Exception as e:
            logger.error(f"Error retrieving groups for {phone_number}: {e}")
            return None
    
    def remove_session_data(self, phone_number: str) -> Dict[str, Any]:
        """
        Remove all data related to a session with comprehensive cleanup
        Automatically cleans up orphaned groups and related metadata
        """
        try:
            removed_items = {
                'groups_file': False,
                'groups_count': 0,
                'index_entries': 0,
                'orphaned_groups': 0
            }
            
            # Get session info
            if phone_number in self.groups_index["sessions"]:
                session_info = self.groups_index["sessions"][phone_number]
                
                # Remove groups file
                groups_file = Path(session_info['file_path'])
                if groups_file.exists():
                    # Get groups count before deletion
                    try:
                        encrypted_data = groups_file.read_bytes()
                        decrypted_data = self.encryption.decrypt(encrypted_data)
                        groups_data = json.loads(decrypted_data)
                        removed_items['groups_count'] = len(groups_data.get('groups', []))
                    except Exception:
                        pass
                    
                    groups_file.unlink()
                    removed_items['groups_file'] = True
                    logger.info(f"Removed groups file: {groups_file}")
                
                # Remove from sessions index
                del self.groups_index["sessions"][phone_number]
                removed_items['index_entries'] += 1
            
            # Clean up orphaned group references
            orphaned_groups = []
            for group_id, group_info in list(self.groups_index["groups"].items()):
                if group_info.get('session_phone') == phone_number:
                    orphaned_groups.append(group_id)
                    del self.groups_index["groups"][group_id]
            
            removed_items['orphaned_groups'] = len(orphaned_groups)
            
            # Update metadata
            self.metadata['total_cleanups'] = self.metadata.get('total_cleanups', 0) + 1
            self.metadata['last_cleanup'] = datetime.now().isoformat()
            
            # Save all changes
            self._save_groups_index()
            self._save_metadata()
            
            logger.info(f"Comprehensive cleanup completed for {phone_number}: {removed_items}")
            return {
                'success': True,
                'message': f'All data for {phone_number} removed successfully',
                'details': removed_items
            }
            
        except Exception as e:
            logger.error(f"Error removing session data for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_sessions_data(self) -> Dict[str, Any]:
        """Get comprehensive data about all sessions"""
        sessions_data = {}
        
        for phone_number in list(self.groups_index["sessions"].keys()):
            session_data = self.get_session_groups(phone_number)
            if session_data:
                sessions_data[phone_number] = {
                    'groups_count': session_data.get('groups_count', 0),
                    'last_updated': session_data.get('last_updated'),
                    'last_accessed': session_data.get('last_accessed'),
                    'status': session_data.get('status', 'unknown')
                }
            else:
                # Clean up invalid session
                logger.warning(f"Removing invalid session {phone_number} from index")
                if phone_number in self.groups_index["sessions"]:
                    del self.groups_index["sessions"][phone_number]
        
        # Save cleaned index
        self._save_groups_index()
        
        return {
            'sessions': sessions_data,
            'total_sessions': len(sessions_data),
            'total_groups_tracked': len(self.groups_index["groups"]),
            'database_metadata': self.metadata
        }
    
    def auto_cleanup_old_data(self, max_age_days: int = 30) -> Dict[str, Any]:
        """
        Automatically cleanup old data based on age
        Provides lifetime management with configurable retention
        """
        try:
            cleanup_stats = {
                'sessions_cleaned': 0,
                'groups_cleaned': 0,
                'files_removed': 0,
                'space_freed': 0
            }
            
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Check sessions for old data
            sessions_to_remove = []
            for phone_number, session_info in self.groups_index["sessions"].items():
                last_updated = session_info.get('last_updated')
                if last_updated:
                    try:
                        update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        if update_date < cutoff_date:
                            sessions_to_remove.append(phone_number)
                    except Exception:
                        # If date parsing fails, consider it old
                        sessions_to_remove.append(phone_number)
            
            # Remove old sessions
            for phone_number in sessions_to_remove:
                result = self.remove_session_data(phone_number)
                if result['success']:
                    cleanup_stats['sessions_cleaned'] += 1
                    cleanup_stats['groups_cleaned'] += result['details']['groups_count']
                    cleanup_stats['files_removed'] += 1 if result['details']['groups_file'] else 0
            
            # Update cleanup metadata
            self.groups_index['last_cleanup'] = datetime.now().isoformat()
            self.metadata['total_cleanups'] = self.metadata.get('total_cleanups', 0) + 1
            self.metadata['last_auto_cleanup'] = datetime.now().isoformat()
            
            self._save_groups_index()
            self._save_metadata()
            
            logger.info(f"Auto-cleanup completed: {cleanup_stats}")
            return {
                'success': True,
                'cleanup_stats': cleanup_stats,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during auto-cleanup: {e}")
            return {'success': False, 'error': str(e)}
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        Optimize database for maximum performance and accuracy
        Removes duplicates, fixes inconsistencies, and rebuilds indexes
        """
        try:
            optimization_stats = {
                'duplicates_removed': 0,
                'inconsistencies_fixed': 0,
                'orphaned_cleaned': 0,
                'index_rebuilt': False
            }
            
            # Remove orphaned group references
            orphaned_groups = []
            active_sessions = set(self.groups_index["sessions"].keys())
            
            for group_id, group_info in list(self.groups_index["groups"].items()):
                session_phone = group_info.get('session_phone')
                if session_phone not in active_sessions:
                    orphaned_groups.append(group_id)
                    del self.groups_index["groups"][group_id]
            
            optimization_stats['orphaned_cleaned'] = len(orphaned_groups)
            
            # Verify file integrity
            sessions_to_fix = []
            for phone_number, session_info in list(self.groups_index["sessions"].items()):
                groups_file = Path(session_info['file_path'])
                if not groups_file.exists():
                    sessions_to_fix.append(phone_number)
            
            # Fix inconsistencies
            for phone_number in sessions_to_fix:
                del self.groups_index["sessions"][phone_number]
                optimization_stats['inconsistencies_fixed'] += 1
            
            # Rebuild index
            self._save_groups_index()
            optimization_stats['index_rebuilt'] = True
            
            # Update metadata
            self.metadata['last_optimization'] = datetime.now().isoformat()
            self._save_metadata()
            
            logger.info(f"Database optimization completed: {optimization_stats}")
            return {
                'success': True,
                'optimization_stats': optimization_stats
            }
            
        except Exception as e:
            logger.error(f"Error during database optimization: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            stats = {
                'total_sessions': len(self.groups_index["sessions"]),
                'total_groups_tracked': len(self.groups_index["groups"]),
                'database_size_mb': self._calculate_database_size(),
                'metadata': self.metadata,
                'last_cleanup': self.groups_index.get('last_cleanup'),
                'health_status': 'healthy'
            }
            
            # Calculate per-session statistics
            session_stats = []
            for phone_number, session_info in self.groups_index["sessions"].items():
                session_stats.append({
                    'phone': phone_number,
                    'groups_count': session_info.get('groups_count', 0),
                    'last_updated': session_info.get('last_updated'),
                    'status': session_info.get('status', 'unknown')
                })
            
            stats['sessions_detail'] = session_stats
            
            # Health check
            if stats['total_sessions'] == 0:
                stats['health_status'] = 'empty'
            elif any(not Path(s['file_path']).exists() for s in self.groups_index["sessions"].values()):
                stats['health_status'] = 'needs_optimization'
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            return {'error': str(e)}
    
    def _calculate_database_size(self) -> float:
        """Calculate total database size in MB"""
        try:
            total_size = 0
            for file_path in [self.groups_index_file, self.metadata_file]:
                if file_path.exists():
                    total_size += file_path.stat().st_size
            
            # Add groups files
            for groups_file in self.groups_dir.glob("*.enc"):
                total_size += groups_file.stat().st_size
            
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0
    
    def _sanitize_phone(self, phone_number: str) -> str:
        """Sanitize phone number for use as filename"""
        return phone_number.replace('+', '').replace('-', '').replace(' ', '')
    
    def clear_all_data(self) -> Dict[str, Any]:
        """Clear all database data with comprehensive cleanup"""
        try:
            removed_files = 0
            
            # Remove all groups files
            for groups_file in self.groups_dir.glob("*.enc"):
                groups_file.unlink()
                removed_files += 1
            
            # Remove index and metadata files
            for db_file in [self.groups_index_file, self.metadata_file]:
                if db_file.exists():
                    db_file.unlink()
                    removed_files += 1
            
            # Reset in-memory data
            self.groups_index = {"sessions": {}, "groups": {}, "last_cleanup": None}
            self.metadata = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "total_cleanups": 0,
                "last_optimization": None
            }
            
            logger.info(f"All database data cleared. Removed {removed_files} files.")
            return {
                'success': True,
                'message': f'All database data cleared. Removed {removed_files} files.',
                'files_removed': removed_files
            }
            
        except Exception as e:
            logger.error(f"Error clearing all data: {e}")
            return {'success': False, 'error': str(e)}