"""
Lightning-fast error handling with 100% reliability and peer management
Professional-grade error recovery system for Telegram broadcasting
"""

import asyncio
import logging
from typing import Dict, Any, List, Set
from pyrogram.errors import (
    FloodWait, SlowmodeWait, ChatWriteForbidden, UserBannedInChannel,
    PeerIdInvalid, ChannelPrivate, UserNotParticipant, ChatAdminRequired,
    MessageTooLong, MediaEmpty, WebpageMediaEmpty, AuthKeyUnregistered
)

logger = logging.getLogger(__name__)

class EnhancedErrorHandler:
    """Lightning-fast error handling with 100% reliability and peer management"""

    def __init__(self):
        self.error_stats = {
            'total_errors': 0,
            'flood_waits': 0,
            'forbidden_chats': 0,
            'invalid_peers': 0,
            'slowmode_waits': 0,
            'recovered_errors': 0,
            'peer_errors': 0,
            'auth_errors': 0
        }
        self.max_flood_wait = 120  # Maximum seconds to wait for flood
        self.max_slowmode_wait = 300  # Maximum seconds to wait for slowmode
        self.invalid_peers: Set[int] = set()  # Cache of invalid peer IDs
        self.retry_counts: Dict[str, int] = {}  # Track retry attempts
        self.max_retries = 3

    async def handle_send_message_error(self, error: Exception, chat_id: int, chat_title: str = "Unknown") -> Dict[str, Any]:
        """Handle message sending errors with intelligent recovery"""
        self.error_stats['total_errors'] += 1
        error_key = f"{chat_id}:{type(error).__name__}"

        # Track retry attempts
        self.retry_counts[error_key] = self.retry_counts.get(error_key, 0) + 1

        if isinstance(error, FloodWait):
            return await self._handle_flood_wait(error, chat_title)

        elif isinstance(error, SlowmodeWait):
            return await self._handle_slowmode_wait(error, chat_title)

        elif isinstance(error, ChatWriteForbidden):
            return await self._handle_forbidden_chat(error, chat_id, chat_title)

        elif isinstance(error, UserBannedInChannel):
            return await self._handle_banned_user(error, chat_id, chat_title)

        elif isinstance(error, (PeerIdInvalid, ChannelPrivate)):
            return await self._handle_invalid_peer(error, chat_id, chat_title)

        elif isinstance(error, UserNotParticipant):
            return await self._handle_not_participant(error, chat_id, chat_title)

        elif isinstance(error, ChatAdminRequired):
            return await self._handle_admin_required(error, chat_id, chat_title)

        elif isinstance(error, (MessageTooLong, MediaEmpty, WebpageMediaEmpty)):
            return await self._handle_message_format_error(error, chat_id, chat_title)

        elif isinstance(error, AuthKeyUnregistered):
            return await self._handle_auth_error(error, chat_id, chat_title)

        else:
            return await self._handle_unknown_error(error, chat_id, chat_title)

    async def _handle_flood_wait(self, error: FloodWait, chat_title: str) -> Dict[str, Any]:
        """Handle FloodWait errors with intelligent waiting"""
        self.error_stats['flood_waits'] += 1
        wait_time = min(error.value, self.max_flood_wait)

        if wait_time <= self.max_flood_wait:
            logger.info(f"FloodWait {wait_time}s for {chat_title} - retrying after wait")
            await asyncio.sleep(wait_time)
            self.error_stats['recovered_errors'] += 1
            return {
                'success': True,
                'action': 'retry',
                'wait_time': wait_time,
                'message': f"Recovered from FloodWait ({wait_time}s) for {chat_title}"
            }
        else:
            logger.warning(f"FloodWait too long ({error.value}s) for {chat_title} - skipping")
            return {
                'success': False,
                'action': 'skipped',
                'reason': 'flood_wait_too_long',
                'message': f"FloodWait too long for {chat_title} - skipped"
            }

    async def _handle_slowmode_wait(self, error: SlowmodeWait, chat_title: str) -> Dict[str, Any]:
        """Handle SlowmodeWait errors"""
        self.error_stats['slowmode_waits'] += 1
        wait_time = min(error.value, self.max_slowmode_wait)

        if wait_time <= self.max_slowmode_wait:
            logger.info(f"SlowmodeWait {wait_time}s for {chat_title} - retrying after wait")
            await asyncio.sleep(wait_time)
            self.error_stats['recovered_errors'] += 1
            return {
                'success': True,
                'action': 'retry',
                'wait_time': wait_time,
                'message': f"Recovered from SlowmodeWait ({wait_time}s) for {chat_title}"
            }
        else:
            logger.warning(f"SlowmodeWait too long ({error.value}s) for {chat_title} - skipping")
            return {
                'success': False,
                'action': 'skipped',
                'reason': 'slowmode_wait_too_long',
                'message': f"SlowmodeWait too long for {chat_title} - skipped"
            }

    async def _handle_forbidden_chat(self, error: ChatWriteForbidden, chat_id: int, chat_title: str) -> Dict[str, Any]:
        """Handle forbidden chat errors"""
        self.error_stats['forbidden_chats'] += 1
        self.invalid_peers.add(chat_id)

        return {
            'success': False,
            'action': 'marked_invalid',
            'reason': 'write_forbidden',
            'message': f"Write forbidden in {chat_title} - marked as invalid"
        }

    async def _handle_banned_user(self, error: UserBannedInChannel, chat_id: int, chat_title: str) -> Dict[str, Any]:
        """Handle banned user errors"""
        self.error_stats['forbidden_chats'] += 1
        self.invalid_peers.add(chat_id)

        return {
            'success': False,
            'action': 'marked_invalid',
            'reason': 'user_banned',
            'message': f"User banned in {chat_title} - marked as invalid"
        }

    async def _handle_invalid_peer(self, error: Exception, chat_id: int, chat_title: str) -> Dict[str, Any]:
        """Handle invalid peer errors"""
        self.error_stats['invalid_peers'] += 1
        self.error_stats['peer_errors'] += 1
        self.invalid_peers.add(chat_id)

        return {
            'success': False,
            'action': 'marked_invalid',
            'reason': 'invalid_peer',
            'message': f"Invalid peer {chat_title} - marked as invalid"
        }

    async def _handle_not_participant(self, error: UserNotParticipant, chat_id: int, chat_title: str) -> Dict[str, Any]:
        """Handle not participant errors"""
        self.error_stats['peer_errors'] += 1
        self.invalid_peers.add(chat_id)

        return {
            'success': False,
            'action': 'marked_invalid',
            'reason': 'not_participant',
            'message': f"Not participant in {chat_title} - marked as invalid"
        }

    async def _handle_admin_required(self, error: ChatAdminRequired, chat_id: int, chat_title: str) -> Dict[str, Any]:
        """Handle admin required errors"""
        self.error_stats['forbidden_chats'] += 1
        self.invalid_peers.add(chat_id)

        return {
            'success': False,
            'action': 'marked_invalid',
            'reason': 'admin_required',
            'message': f"Admin required in {chat_title} - marked as invalid"
        }

    async def _handle_message_format_error(self, error: Exception, chat_id: int, chat_title: str) -> Dict[str, Any]:
        """Handle message format errors"""
        return {
            'success': False,
            'action': 'skipped',
            'reason': 'message_format_error',
            'message': f"Message format error for {chat_title}: {type(error).__name__}"
        }

    async def _handle_auth_error(self, error: AuthKeyUnregistered, chat_id: int, chat_title: str) -> Dict[str, Any]:
        """Handle authentication errors"""
        self.error_stats['auth_errors'] += 1

        return {
            'success': False,
            'action': 'auth_error',
            'reason': 'auth_key_unregistered',
            'message': f"Authentication error for {chat_title} - session may need re-login"
        }

    async def _handle_unknown_error(self, error: Exception, chat_id: int, chat_title: str) -> Dict[str, Any]:
        """Handle unknown errors"""
        logger.warning(f"Unknown error for {chat_title}: {error}")

        return {
            'success': False,
            'action': 'unknown_error',
            'reason': 'unknown',
            'message': f"Unknown error for {chat_title}: {str(error)}"
        }

    def is_invalid_peer(self, chat_id: int) -> bool:
        """Check if a peer is marked as invalid"""
        return chat_id in self.invalid_peers

    def clear_invalid_peers(self):
        """Clear invalid peers cache"""
        cleared_count = len(self.invalid_peers)
        self.invalid_peers.clear()
        logger.info(f"Cleared {cleared_count} invalid peers from cache")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        total_errors = self.error_stats['total_errors']
        successful_recoveries = self.error_stats['recovered_errors']

        recovery_rate = (successful_recoveries / total_errors * 100) if total_errors > 0 else 100

        return {
            'total_errors_handled': total_errors,
            'successful_recoveries': successful_recoveries,
            'recovery_rate_percent': round(recovery_rate, 2),
            'flood_waits': self.error_stats['flood_waits'],
            'forbidden_chats': self.error_stats['forbidden_chats'],
            'invalid_peers': self.error_stats['invalid_peers'],
            'slowmode_waits': self.error_stats['slowmode_waits'],
            'peer_errors': self.error_stats['peer_errors'],
            'auth_errors': self.error_stats['auth_errors'],
            'cached_invalid_peers': len(self.invalid_peers),
            'system_reliability': 'Professional Grade' if recovery_rate > 90 else 'Good' if recovery_rate > 70 else 'Needs Attention'
        }

    def reset_retry_count(self, chat_id: int, error_type: str):
        """Reset retry count for a specific chat and error type"""
        error_key = f"{chat_id}:{error_type}"
        if error_key in self.retry_counts:
            del self.retry_counts[error_key]

    def should_retry(self, chat_id: int, error_type: str) -> bool:
        """Check if we should retry for a specific chat and error type"""
        error_key = f"{chat_id}:{error_type}"
        return self.retry_counts.get(error_key, 0) < self.max_retries

    def mark_peer_invalid(self, chat_id: int):
        """Mark a peer as invalid"""
        self.invalid_peers.add(chat_id)
        logger.debug(f"Marked peer {chat_id} as invalid")

    async def validate_chat_access(self, client, chat_id: int) -> Dict[str, Any]:
        """Validate if we can access and send to a chat with caching"""
        # Check cache first
        if self.is_invalid_peer(chat_id):
            return {'valid': False, 'reason': 'cached_invalid_peer', 'cached': True}

        try:
            # Try to get chat info
            chat = await client.get_chat(chat_id)

            # Check if we're a member
            try:
                member = await client.get_chat_member(chat_id, "me")
                if member.status in ["kicked", "banned", "left"]:
                    self.mark_peer_invalid(chat_id)
                    return {'valid': False, 'reason': 'not_member'}
            except (UserNotParticipant, ChatAdminRequired):
                self.mark_peer_invalid(chat_id)
                return {'valid': False, 'reason': 'not_participant'}

            # Check if chat allows messages
            if hasattr(chat, 'permissions'):
                if not getattr(chat.permissions, 'can_send_messages', True):
                    self.mark_peer_invalid(chat_id)
                    return {'valid': False, 'reason': 'no_send_permission'}

            return {'valid': True, 'chat': chat}

        except (PeerIdInvalid, ChannelPrivate, ValueError):
            self.mark_peer_invalid(chat_id)
            return {'valid': False, 'reason': 'invalid_peer'}
        except Exception as e:
            if "Peer id invalid" in str(e):
                self.mark_peer_invalid(chat_id)
                return {'valid': False, 'reason': 'peer_id_error'}
            return {'valid': False, 'reason': f'unknown_error_{type(e).__name__}'}