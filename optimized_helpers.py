"""
Optimized helper functions for type-safe operations
Lightning-speed error-free implementations
"""

import asyncio
import logging
from typing import List, Optional, Any
from pyrogram.client import Client
from pyrogram.types import Dialog, Message
from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

class OptimizedHelpers:
    """Lightning-speed helper functions for error-free operation"""
    
    @staticmethod
    async def safe_get_dialogs(client: Client) -> List[Dialog]:
        """Safely get all dialogs with error handling"""
        dialogs = []
        try:
            async for dialog in client.get_dialogs():
                dialogs.append(dialog)
        except Exception as e:
            logger.error(f"Error getting dialogs: {e}")
        return dialogs
    
    @staticmethod
    async def safe_get_chat_history(client: Client, chat_id: int, limit: int = 1) -> List[Message]:
        """Safely get chat history with error handling"""
        messages = []
        try:
            async for message in client.get_chat_history(chat_id, limit=limit):
                messages.append(message)
        except Exception as e:
            logger.debug(f"Error getting chat history for {chat_id}: {e}")
        return messages
    
    @staticmethod
    async def safe_sleep_flood_wait(e: FloodWait) -> None:
        """Safely handle FloodWait errors"""
        try:
            wait_time = float(getattr(e, 'value', 1))
            await asyncio.sleep(wait_time)
        except (ValueError, TypeError):
            await asyncio.sleep(1.0)  # Default fallback
    
    @staticmethod
    def safe_get_chat_type(dialog: Dialog) -> str:
        """Safely get chat type"""
        try:
            chat_type = dialog.chat.type
            if hasattr(chat_type, 'name'):
                return chat_type.name.lower()
            else:
                return str(chat_type).lower()
        except:
            return "unknown"
    
    @staticmethod
    def is_group_or_supergroup(dialog: Dialog) -> bool:
        """Check if dialog is a group or supergroup"""
        chat_type = OptimizedHelpers.safe_get_chat_type(dialog)
        return chat_type in ["group", "supergroup"]
    
    @staticmethod
    def safe_get_attribute(obj: Any, attr: str, default: Any = None) -> Any:
        """Safely get attribute with fallback"""
        return getattr(obj, attr, default)