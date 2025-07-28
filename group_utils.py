"""
Group management utilities for Telegram accounts
"""

import asyncio
import logging
from typing import Dict, Any, List
from pyrogram.client import Client
from pyrogram.types import Dialog
from pyrogram.errors import FloodWait, ChatAdminRequired, UserNotParticipant
from pyrogram.enums import ChatMemberStatus

from config import Config
from optimized_helpers import OptimizedHelpers

logger = logging.getLogger(__name__)

class GroupManager:
    """Manages group-related operations across accounts"""

    def __init__(self):
        self.config = Config()

    async def leave_muted_groups(self, sessions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Leave groups where the account is muted or restricted"""
        logger.info(f"Checking groups across {len(sessions)} accounts for muted/restricted status")

        total_checked = 0
        left_count = 0
        failed_accounts = {}

        for phone_number, session_data in sessions.items():
            try:
                logger.info(f"Checking groups for account: {phone_number}")

                # Create client for this session
                client = Client(
                    f"group_check_{phone_number.replace('+', '')}",
                    api_id=self.config.API_ID,
                    api_hash=self.config.API_HASH,
                    session_string=session_data['session_string']
                )

                await client.start()

                account_checked, account_left = await self._check_and_leave_groups(
                    client, phone_number
                )

                total_checked += account_checked
                left_count += account_left

                await client.stop()

                # Add delay between accounts
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error checking groups for {phone_number}: {e}")
                failed_accounts[phone_number] = str(e)

        logger.info(f"Group cleanup completed. Left {left_count} groups out of {total_checked} checked")

        return {
            'left_count': left_count,
            'total_checked': total_checked,
            'failed_accounts': failed_accounts
        }

    async def _check_and_leave_groups(self, client: Client, phone_number: str) -> tuple:
        """Check and leave muted groups for a single account"""
        checked_count = 0
        left_count = 0

        try:
            # Get user's own ID
            me = await client.get_me()
            user_id = me.id

            # Get all dialogs
            dialogs = await OptimizedHelpers.safe_get_dialogs(client)
            for dialog in dialogs:
                if OptimizedHelpers.is_group_or_supergroup(dialog):
                    checked_count += 1

                    try:
                        # Check if user can send messages in this group
                        should_leave = await self._should_leave_group(client, dialog, user_id)

                        if should_leave:
                            await client.leave_chat(dialog.chat.id)
                            left_count += 1
                            logger.info(f"Left group: {dialog.chat.title} ({phone_number})")

                            # Small delay after leaving
                            await asyncio.sleep(0.5)

                    except FloodWait as e:
                        logger.warning(f"FloodWait {e.value}s when checking {dialog.chat.title}")
                        await OptimizedHelpers.safe_sleep_flood_wait(e)

                    except Exception as e:
                        logger.error(f"Error checking group {dialog.chat.title}: {e}")

        except Exception as e:
            logger.error(f"Error getting dialogs for {phone_number}: {e}")

        return checked_count, left_count

    async def _should_leave_group(self, client: Client, dialog: Dialog, user_id: int) -> bool:
        """Determine if the account should leave a group"""
        try:
            chat = dialog.chat

            # Check if the group is muted (using notification settings)
            if OptimizedHelpers.safe_get_attribute(dialog, 'is_muted', False):
                logger.debug(f"Group {chat.title} is muted - marking for leave")
                return True

            # For supergroups, check if user has restricted permissions
            if chat.type == "supergroup":
                try:
                    # Get chat member info
                    member = await client.get_chat_member(chat.id, user_id)

                    # Check if user is restricted or cannot send messages
                    if member.status == "restricted":
                        if hasattr(member, 'permissions') and member.permissions:
                            if not member.permissions.can_send_messages:
                                logger.debug(f"Cannot send messages in {chat.title} - marking for leave")
                                return True
                        else:
                            # If no permissions info, assume restricted
                            logger.debug(f"Restricted in {chat.title} - marking for leave")
                            return True

                    # Check if user is banned
                    if member.status in ["kicked", "banned"]:
                        logger.debug(f"Banned/kicked from {chat.title} - marking for leave")
                        return True

                except UserNotParticipant:
                    # User is not a participant (already left or was removed)
                    logger.debug(f"Not a participant in {chat.title}")
                    return False

                except ChatAdminRequired:
                    # Cannot get member info, but if we're here we're probably a member
                    logger.debug(f"Cannot check permissions in {chat.title} (admin required)")
                    return False

                except Exception as e:
                    logger.debug(f"Error checking permissions in {chat.title}: {e}")
                    return False

            # Check if it's a read-only group (no recent messages or very old last message)
            try:
                # Get the latest message
                messages = await OptimizedHelpers.safe_get_chat_history(client, chat.id, limit=1)
                for message in messages:
                    # If we can get messages and there are recent ones, don't leave
                    from datetime import datetime, timedelta
                    if message.date and (datetime.now() - message.date).days < 30:
                        return False
                    else:
                        logger.debug(f"Group {chat.title} seems inactive - marking for leave")
                        return True

                # If no messages found, consider it inactive
                logger.debug(f"No messages found in {chat.title} - marking for leave")
                return True

            except Exception as e:
                logger.debug(f"Cannot check messages in {chat.title}: {e}")
                # If we can't check messages, probably restricted
                return True

        except Exception as e:
            logger.error(f"Error determining if should leave {dialog.chat.title}: {e}")
            return False

        return False

    async def get_group_count(self, session_string: str) -> int:
        """Get the number of groups for a session"""
        try:
            # Create temporary client
            client = Client(
                "temp_count_client",
                api_id=self.config.API_ID,
                api_hash=self.config.API_HASH,
                session_string=session_string
            )

            await client.start()

            group_count = 0
            dialogs = await OptimizedHelpers.safe_get_dialogs(client)
            for dialog in dialogs:
                if OptimizedHelpers.is_group_or_supergroup(dialog):
                    group_count += 1

            await client.stop()

            return group_count

        except Exception as e:
            logger.error(f"Error getting group count: {e}")
            return 0

    async def get_group_list(self, session_string: str) -> List[Dict[str, Any]]:
        """Get detailed information about all groups for a session"""
        groups = []

        try:
            client = Client(
                "temp_list_client",
                api_id=self.config.API_ID,
                api_hash=self.config.API_HASH,
                session_string=session_string
            )

            await client.start()

            dialogs = await OptimizedHelpers.safe_get_dialogs(client)
            for dialog in dialogs:
                if OptimizedHelpers.is_group_or_supergroup(dialog):
                    chat = dialog.chat

                    group_info = {
                        'id': chat.id,
                        'title': chat.title or 'Unknown',
                        'type': OptimizedHelpers.safe_get_chat_type(dialog),
                        'username': chat.username,
                        'member_count': OptimizedHelpers.safe_get_attribute(chat, 'members_count', 0),
                        'is_muted': OptimizedHelpers.safe_get_attribute(dialog, 'is_muted', False),
                        'unread_count': OptimizedHelpers.safe_get_attribute(dialog, 'unread_messages_count', 0)
                    }

                    groups.append(group_info)

            await client.stop()

        except Exception as e:
            logger.error(f"Error getting group list: {e}")

        return groups
"""
Professional group management utilities
Handles group operations, cleanup, and optimization
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.types import Dialog
from pyrogram.errors import FloodWait, PeerIdInvalid, ChannelPrivate

logger = logging.getLogger(__name__)

class GroupManager:
    """Professional group management with optimization and cleanup"""

    def __init__(self):
        """Initialize group manager"""
        logger.info("Group manager initialized")

    
    async def leave_muted_groups(self, sessions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Leave muted groups across all sessions"""
        try:
            results = {}

            for phone_number, session_data in sessions.items():
                logger.info(f"Processing groups for session {phone_number}")

                # Extract session string from session data
                session_string = session_data.get('session_string') if isinstance(session_data, dict) else session_data

                if not session_string:
                    results[phone_number] = {
                        'success': False,
                        'error': 'No session string found',
                        'groups_checked': 0,
                        'groups_left': 0
                    }
                    continue

                result = await self._leave_muted_groups_single_session(
                    session_string, 
                    phone_number
                )

                results[phone_number] = result

                # Delay between sessions
                await asyncio.sleep(1)

            return {
                'success': True,
                'results': results,
                'total_sessions': len(sessions)
            }

        except Exception as e:
            logger.error(f"Leave muted groups failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _process_account_groups(self, phone_number: str, session_string: str) -> Dict[str, Any]:
        """Process groups for a single account"""
        try:
            from config import Config
            config = Config()

            # Create client for this session
            client = Client(
                f"group_cleanup_{phone_number.replace('+', '')}",
                session_string=session_string,
                api_id=config.API_ID,
                api_hash=config.API_HASH
            )

            await client.start()

            groups_checked = 0
            groups_left = 0

            try:
                # Get all dialogs (chats)
                async for dialog in client.get_dialogs():
                    if dialog.chat.type in ["group", "supergroup", "channel"]:
                        groups_checked += 1

                        # Check if we should leave this group
                        should_leave = await self._should_leave_group(client, dialog)

                        if should_leave:
                            try:
                                await client.leave_chat(dialog.chat.id)
                                groups_left += 1
                                logger.info(f"Left group: {dialog.chat.title} ({phone_number})")

                                # Small delay to avoid rate limits
                                await asyncio.sleep(1)

                            except Exception as e:
                                logger.warning(f"Failed to leave group {dialog.chat.title}: {e}")

            finally:
                await client.stop()

            return {
                'success': True,
                'groups_checked': groups_checked,
                'groups_left': groups_left,
                'phone_number': phone_number
            }

        except Exception as e:
            logger.error(f"Error processing account groups for {phone_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'groups_checked': 0,
                'groups_left': 0
            }

    async def _should_leave_group(self, client: Client, dialog: Dialog) -> bool:
        """Determine if we should leave a group"""
        try:
            chat = dialog.chat

            # Check if chat is muted
            if hasattr(dialog, 'is_muted') and dialog.is_muted:
                return True

            # Check if we can send messages
            try:
                member = await client.get_chat_member(chat.id, "me")

                # If we're restricted or banned
                if hasattr(member, 'status') and member.status in ["restricted", "kicked"]:
                    return True

                # Check if we have send permissions
                if hasattr(member, 'permissions'):
                    if not getattr(member.permissions, 'can_send_messages', True):
                        return True

            except Exception:
                # If we can't get member info, we might not have access
                return True

            # Check if group is inactive (no recent messages)
            try:
                # Check last message date
                if hasattr(dialog, 'top_message') and dialog.top_message:
                    last_message_date = dialog.top_message.date
                    if last_message_date:
                        days_since_last_message = (datetime.now() - last_message_date).days
                        if days_since_last_message > 30:  # 30 days of inactivity
                            return True
            except Exception:
                pass

            return False

        except Exception as e:
            logger.warning(f"Error checking if should leave group {dialog.chat.title}: {e}")
            return False

    async def get_groups_info(self, sessions: Dict[str, str]) -> Dict[str, Any]:
        """Get information about groups across all sessions"""
        try:
            all_groups_info = {}

            for phone_number, session_string in sessions.items():
                try:
                    groups_info = await self._get_account_groups_info(phone_number, session_string)
                    all_groups_info[phone_number] = groups_info
                except Exception as e:
                    logger.error(f"Error getting groups info for {phone_number}: {e}")
                    all_groups_info[phone_number] = {
                        'success': False,
                        'error': str(e)
                    }

            return {
                'success': True,
                'accounts': all_groups_info,
                'total_accounts': len(all_groups_info)
            }

        except Exception as e:
            logger.error(f"Error getting groups info: {e}")
            return {'success': False, 'error': str(e)}

    async def _get_account_groups_info(self, phone_number: str, session_string: str) -> Dict[str, Any]:
        """Get groups information for a single account"""
        try:
            from config import Config
            config = Config()

            client = Client(
                f"groups_info_{phone_number.replace('+', '')}",
                session_string=session_string,
                api_id=config.API_ID,
                api_hash=config.API_HASH
            )

            await client.start()

            groups = []
            total_groups = 0
            active_groups = 0
            muted_groups = 0

            try:
                async for dialog in client.get_dialogs():
                    if dialog.chat.type in ["group", "supergroup", "channel"]:
                        total_groups += 1

                        group_info = {
                            'id': dialog.chat.id,
                            'title': dialog.chat.title,
                            'type': dialog.chat.type,
                            'members_count': getattr(dialog.chat, 'members_count', 0),
                            'is_muted': getattr(dialog, 'is_muted', False)
                        }

                        if group_info['is_muted']:
                            muted_groups += 1
                        else:
                            active_groups += 1

                        groups.append(group_info)

            finally:
                await client.stop()

            return {
                'success': True,
                'groups': groups,
                'statistics': {
                    'total_groups': total_groups,
                    'active_groups': active_groups,
                    'muted_groups': muted_groups
                }
            }

        except Exception as e:
            logger.error(f"Error getting account groups info for {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _leave_muted_groups_single_session(self, session_string: str, phone_number: str) -> Dict[str, Any]:
        """Leave muted groups for a single session"""
        try:
            from config import Config
            config = Config()

            # Create client for this session
            client = Client(
                f"group_cleanup_{phone_number.replace('+', '')}",
                session_string=session_string,
                api_id=config.API_ID,
                api_hash=config.API_HASH
            )

            await client.start()

            groups_checked = 0
            groups_left = 0

            try:
                # Get all dialogs (chats)
                async for dialog in client.get_dialogs():
                    if dialog.chat.type in ["group", "supergroup", "channel"]:
                        groups_checked += 1

                        # Check if we should leave this group
                        should_leave = await self._should_leave_group(client, dialog)

                        if should_leave:
                            try:
                                await client.leave_chat(dialog.chat.id)
                                groups_left += 1
                                logger.info(f"Left group: {dialog.chat.title} ({phone_number})")

                                # Small delay to avoid rate limits
                                await asyncio.sleep(1)

                            except Exception as e:
                                logger.warning(f"Failed to leave group {dialog.chat.title}: {e}")

            finally:
                await client.stop()

            return {
                'success': True,
                'groups_checked': groups_checked,
                'groups_left': groups_left,
                'phone_number': phone_number
            }

        except Exception as e:
            logger.error(f"Error processing account groups for {phone_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'groups_checked': 0,
                'groups_left': 0
            }