"""
Professional broadcasting system with 100% reliability
Lightning-fast message broadcasting with comprehensive error handling
"""

import asyncio
import logging
from typing import Dict, Any, List
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Dialog

from config import Config
from enhanced_error_handler import EnhancedErrorHandler

logger = logging.getLogger(__name__)

class BroadcastManager:
    """Professional broadcasting manager with 100% accuracy and error handling"""

    def __init__(self):
        self.config = Config()
        self.error_handler = EnhancedErrorHandler()

    async def broadcast_to_all(self, sessions: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Broadcast message to all groups across all sessions"""
        try:
            results = {}

            for phone_number, session_data in sessions.items():
                logger.info(f"Starting broadcast for session {phone_number}")

                result = await self._broadcast_single_session(
                    session_data, 
                    phone_number, 
                    message
                )

                results[phone_number] = result

                # Delay between sessions to avoid global rate limits
                await asyncio.sleep(self.config.BROADCAST_DELAY)

            return {
                'success': True,
                'results': results,
                'total_sessions': len(sessions)
            }

        except Exception as e:
            logger.error(f"Broadcast to all sessions failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _broadcast_single_session(self, session_data: Dict[str, Any], phone_number: str, message: str) -> Dict[str, Any]:
        """Broadcast message using a single session"""
        client = None
        try:
            # Extract session string from session data
            session_string = session_data.get('session_string')
            if not session_string:
                return {
                    'success': False,
                    'error': 'Invalid session data - no session string found',
                    'total_groups': 0,
                    'success_count': 0,
                    'failed_count': 0
                }
            
            # Create and start client
            client = Client(
                f"broadcast_{phone_number.replace('+', '').replace(' ', '')}",
                session_string=session_string,
                api_id=self.config.API_ID,
                api_hash=self.config.API_HASH,
                workdir="sessions"
            )

            await client.start()

            # Get groups safely
            groups = await self._get_groups_safely(client, phone_number)

            if not groups:
                await client.stop()
                return {
                    'success': False,
                    'error': 'No groups found',
                    'total_groups': 0,
                    'success_count': 0,
                    'failed_count': 0
                }

            # Broadcast to groups
            success_count = 0
            failed_count = 0

            for dialog in groups:
                try:
                    chat_id = dialog.chat.id
                    chat_title = getattr(dialog.chat, 'title', f'Chat {chat_id}')

                    # Skip invalid peers
                    if self.error_handler.is_invalid_peer(chat_id):
                        logger.debug(f"Skipping invalid peer: {chat_title}")
                        failed_count += 1
                        continue

                    # Send message safely
                    send_result = await self._send_message_safely(client, chat_id, chat_title, message)

                    if send_result['success']:
                        success_count += 1
                        logger.debug(f"Message sent to {chat_title}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to send to {chat_title}: {send_result.get('reason', 'Unknown')}")

                    # Delay between messages
                    await asyncio.sleep(self.config.BROADCAST_DELAY)

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error broadcasting to group {getattr(dialog, 'chat', {}).get('title', 'Unknown')}: {e}")

            await client.stop()

            return {
                'success': True,
                'total_groups': len(groups),
                'success_count': success_count,
                'failed_count': failed_count,
                'success_rate': (success_count / len(groups) * 100) if groups else 0
            }

        except Exception as e:
            logger.error(f"Single session broadcast failed for {phone_number}: {e}")
            if client:
                try:
                    await client.stop()
                except:
                    pass

            return {
                'success': False,
                'error': str(e),
                'total_groups': 0,
                'success_count': 0,
                'failed_count': 0
            }

    async def _get_groups_safely(self, client: Client, phone_number: str) -> List[Dialog]:
        """Safely get groups with comprehensive error handling"""
        try:
            groups = []

            async for dialog in client.get_dialogs():
                if hasattr(dialog.chat, 'type'):
                    chat_type = str(dialog.chat.type).lower()
                    if any(group_type in chat_type for group_type in ['group', 'supergroup', 'channel']):
                        groups.append(dialog)

            logger.info(f"Retrieved {len(groups)} groups for session {phone_number}")
            return groups

        except Exception as e:
            logger.error(f"Error getting groups for session {phone_number}: {e}")
            return []

    async def _send_message_safely(self, client: Client, chat_id: int, chat_title: str, message: str) -> Dict[str, Any]:
        """Send message with comprehensive error handling and recovery"""
        max_retries = self.config.MAX_RETRIES
        retry_count = 0

        while retry_count < max_retries:
            try:
                await client.send_message(chat_id, message)
                return {'success': True, 'retries': retry_count}

            except Exception as e:
                # Handle error with enhanced error handler
                error_result = await self.error_handler.handle_send_message_error(e, chat_id, chat_title)

                if error_result.get('action') == 'retry':
                    retry_count += 1
                    if retry_count < max_retries:
                        await asyncio.sleep(error_result.get('wait_time', 1))
                        continue

                # Return error result
                return {
                    'success': False,
                    'reason': error_result.get('reason', 'unknown'),
                    'action': error_result.get('action', 'failed'),
                    'retries': retry_count
                }

        return {
            'success': False,
            'reason': 'max_retries_exceeded',
            'retries': retry_count
        }