"""
MongoDB Database Manager for storing user status, groups, and session data
Professional-grade MongoDB integration with error handling and data validation
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId

from config import Config

logger = logging.getLogger(__name__)

class MongoDBManager:
    """
    Professional MongoDB manager for user data, groups, and session management
    Handles user status, group memberships, broadcast history, and analytics
    """

    def __init__(self):
        """Initialize MongoDB connection"""
        self.config = Config()
        self.mongo_url = os.getenv('MONGO_DB_URL', '')

        if not self.mongo_url:
            logger.error("MONGO_DB_URL not found in environment variables")
            raise ValueError("MongoDB URL is required")

        try:
            # Initialize MongoDB client with timeout
            self.client = MongoClient(
                self.mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )

            # Test connection
            self.client.admin.command('ping')
            logger.info("MongoDB connection established successfully")

            # Database and collections
            self.db = self.client.telegram_bot
            self.users_collection = self.db.users
            self.groups_collection = self.db.groups
            self.sessions_collection = self.db.sessions
            self.broadcasts_collection = self.db.broadcasts
            self.analytics_collection = self.db.analytics

            # Create indexes for better performance
            self._create_indexes()

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"MongoDB initialization error: {e}")
            raise

    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # User indexes
            self.users_collection.create_index("phone_number", unique=True)
            self.users_collection.create_index("user_id")
            self.users_collection.create_index("status")

            # Group indexes
            self.groups_collection.create_index([("group_id", 1), ("session_phone", 1)], unique=True)
            self.groups_collection.create_index("session_phone")
            self.groups_collection.create_index("group_type")

            # Session indexes
            self.sessions_collection.create_index("phone_number", unique=True)
            self.sessions_collection.create_index("status")

            # Broadcast indexes
            self.broadcasts_collection.create_index("timestamp")
            self.broadcasts_collection.create_index("owner_id")

            logger.info("MongoDB indexes created successfully")

        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def store_user_data(self, phone_number: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store user data in MongoDB"""
        try:
            # Check if user already exists
            existing_user = self.users_collection.find_one({'phone_number': phone_number})

            if existing_user:
                # Update existing user (preserve created_at)
                update_doc = {
                    'user_id': user_data.get('user_id'),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'username': user_data.get('username', ''),
                    'is_premium': user_data.get('is_premium', False),
                    'language_code': user_data.get('language_code', 'en'),
                    'two_factor_enabled': user_data.get('two_factor_enabled', False),
                    'status': 'active',
                    'updated_at': datetime.utcnow(),
                    'last_login': datetime.utcnow()
                }

                result = self.users_collection.update_one(
                    {'phone_number': phone_number},
                    {'$set': update_doc}
                )
            else:
                # Create new user document
                user_doc = {
                    'phone_number': phone_number,
                    'user_id': user_data.get('user_id'),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'username': user_data.get('username', ''),
                    'is_premium': user_data.get('is_premium', False),
                    'language_code': user_data.get('language_code', 'en'),
                    'two_factor_enabled': user_data.get('two_factor_enabled', False),
                    'status': 'active',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'last_login': datetime.utcnow()
                }

                result = self.users_collection.insert_one(user_doc)

            logger.info(f"User data stored for {phone_number}")
            return {'success': True, 'message': 'User data stored successfully'}

        except Exception as e:
            logger.error(f"Error storing user data for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}

    def store_session_groups(self, phone_number: str, groups_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store groups data for a session with MongoDB"""
        try:
            # Remove existing groups for this session
            self.groups_collection.delete_many({"session_phone": phone_number})

            # Prepare groups documents
            groups_docs = []
            for group in groups_data:
                group_doc = {
                    "group_id": str(group.get('id', '')),
                    "session_phone": phone_number,
                    "title": group.get('title', 'Unknown'),
                    "type": group.get('type', 'unknown'),
                    "member_count": group.get('members_count', 0),
                    "is_admin": group.get('is_admin', False),
                    "is_creator": group.get('is_creator', False),
                    "can_send_messages": group.get('can_send_messages', True),
                    "is_muted": group.get('is_muted', False),
                    "restrictions": group.get('restrictions', {}),
                    "last_message_date": group.get('last_message_date'),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "status": "active"
                }
                groups_docs.append(group_doc)

            # Insert groups in batch
            if groups_docs:
                self.groups_collection.insert_many(groups_docs)

            # Update user's total groups count
            self.users_collection.update_one(
                {"phone_number": phone_number},
                {
                    "$set": {
                        "total_groups": len(groups_data),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.info(f"Stored {len(groups_data)} groups for {phone_number}")
            return {
                'success': True,
                'message': f'Stored {len(groups_data)} groups successfully',
                'groups_count': len(groups_data)
            }

        except Exception as e:
            logger.error(f"Error storing groups for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_groups(self, phone_number: str) -> Optional[List[Dict[str, Any]]]:
        """Get all groups for a specific user"""
        try:
            groups = list(self.groups_collection.find(
                {"session_phone": phone_number, "status": "active"},
                {"_id": 0}
            ))

            if groups:
                # Update last accessed
                self.users_collection.update_one(
                    {"phone_number": phone_number},
                    {"$set": {"last_seen": datetime.utcnow()}}
                )

                return groups

            return []

        except Exception as e:
            logger.error(f"Error retrieving groups for {phone_number}: {e}")
            return None

    def update_user_status(self, phone_number: str, status: str, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update user status and additional data"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }

            if additional_data:
                update_data.update(additional_data)

            result = self.users_collection.update_one(
                {"phone_number": phone_number},
                {"$set": update_data}
            )

            return {
                'success': result.modified_count > 0,
                'message': f'User status updated to {status}'
            }

        except Exception as e:
            logger.error(f"Error updating user status for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}

    def remove_user_data(self, phone_number: str) -> Dict[str, Any]:
        """Remove all user data and associated groups"""
        try:
            # Remove user groups
            groups_result = self.groups_collection.delete_many({"session_phone": phone_number})

            # Remove user data
            user_result = self.users_collection.delete_one({"phone_number": phone_number})

            # Remove session data
            session_result = self.sessions_collection.delete_one({"phone_number": phone_number})

            logger.info(f"Removed user data for {phone_number}: {groups_result.deleted_count} groups, {user_result.deleted_count} user records")

            return {
                'success': True,
                'message': f'All data for {phone_number} removed successfully',
                'details': {
                    'groups_removed': groups_result.deleted_count,
                    'user_records_removed': user_result.deleted_count,
                    'session_records_removed': session_result.deleted_count
                }
            }

        except Exception as e:
            logger.error(f"Error removing user data for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}

    def store_broadcast_record(self, owner_id: int, message: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Store broadcast history for analytics"""
        try:
            total_sent = sum(account.get('success_count', 0) for account in results.values())
            total_groups = sum(account.get('total_groups', 0) for account in results.values())

            broadcast_doc = {
                "owner_id": owner_id,
                "message": message,
                "message_length": len(message),
                "timestamp": datetime.utcnow(),
                "accounts_used": len(results),
                "total_groups": total_groups,
                "messages_sent": total_sent,
                "success_rate": (total_sent / total_groups * 100) if total_groups > 0 else 0,
                "results": results,
                "status": "completed"
            }

            result = self.broadcasts_collection.insert_one(broadcast_doc)

            # Update user broadcast stats
            for phone_number in results.keys():
                self.users_collection.update_one(
                    {"phone_number": phone_number},
                    {
                        "$inc": {"total_broadcasts": 1},
                        "$set": {"last_broadcast": datetime.utcnow()}
                    }
                )

            return {
                'success': True,
                'broadcast_id': str(result.inserted_id),
                'message': 'Broadcast record stored successfully'
            }

        except Exception as e:
            logger.error(f"Error storing broadcast record: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_analytics(self, phone_number: str = None) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        try:
            if phone_number:
                # Single user analytics
                user = self.users_collection.find_one({"phone_number": phone_number})
                if not user:
                    return {'success': False, 'error': 'User not found'}

                groups_count = self.groups_collection.count_documents({"session_phone": phone_number})

                return {
                    'success': True,
                    'user_data': {
                        'phone_number': user['phone_number'],
                        'status': user['status'],
                        'total_groups': groups_count,
                        'total_broadcasts': user.get('total_broadcasts', 0),
                        'last_seen': user.get('last_seen'),
                        'created_at': user.get('created_at')
                    }
                }
            else:
                # Overall analytics
                total_users = self.users_collection.count_documents({})
                active_users = self.users_collection.count_documents({"status": "active"})
                total_groups = self.groups_collection.count_documents({})
                total_broadcasts = self.broadcasts_collection.count_documents({})

                return {
                    'success': True,
                    'analytics': {
                        'total_users': total_users,
                        'active_users': active_users,
                        'total_groups': total_groups,
                        'total_broadcasts': total_broadcasts,
                        'last_updated': datetime.utcnow()
                    }
                }

        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {'success': False, 'error': str(e)}

    def get_all_users_data(self) -> Dict[str, Any]:
        """Get all users data with statistics"""
        try:
            users = list(self.users_collection.find({}, {"_id": 0}))

            return {
                'success': True,
                'users': users,
                'total_users': len(users),
                'active_users': len([u for u in users if u.get('status') == 'active']),
                'last_updated': datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting all users data: {e}")
            return {'success': False, 'error': str(e)}

    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old inactive data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Remove old broadcast records
            broadcasts_removed = self.broadcasts_collection.delete_many(
                {"timestamp": {"$lt": cutoff_date}}
            ).deleted_count

            # Mark old inactive users
            inactive_users = self.users_collection.update_many(
                {
                    "last_seen": {"$lt": cutoff_date},
                    "status": "active"
                },
                {"$set": {"status": "inactive"}}
            ).modified_count

            return {
                'success': True,
                'cleanup_stats': {
                    'broadcasts_removed': broadcasts_removed,
                    'users_marked_inactive': inactive_users,
                    'cutoff_date': cutoff_date
                }
            }

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {'success': False, 'error': str(e)}

    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            stats = {
                'users': {
                    'total': self.users_collection.count_documents({}),
                    'active': self.users_collection.count_documents({"status": "active"}),
                    'inactive': self.users_collection.count_documents({"status": "inactive"})
                },
                'groups': {
                    'total': self.groups_collection.count_documents({}),
                    'active': self.groups_collection.count_documents({"status": "active"})
                },
                'broadcasts': {
                    'total': self.broadcasts_collection.count_documents({}),
                    'today': self.broadcasts_collection.count_documents({
                        "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
                    })
                },
                'database_health': 'healthy',
                'last_updated': datetime.utcnow()
            }

            return {'success': True, 'stats': stats}

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'success': False, 'error': str(e)}

    def close_connection(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")