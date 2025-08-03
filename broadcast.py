import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait, PeerFlood, UserPrivacyRestricted, ChatWriteForbidden
import time

class BroadcastManager:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.broadcast_logs = {}
        
    async def broadcast_to_groups(self, message_text, parse_mode="markdown"):
        """Broadcast message to all groups of all active sessions"""
        all_results = {}
        
        for phone_number, client in self.session_manager.get_all_sessions().items():
            try:
                results = await self._broadcast_to_session_groups(client, message_text, parse_mode)
                all_results[phone_number] = results
                self.session_manager.update_last_broadcast(phone_number)
            except Exception as e:
                all_results[phone_number] = {"error": str(e)}
                
        # Save broadcast logs
        timestamp = time.time()
        self.broadcast_logs[timestamp] = all_results
        
        return all_results
        
    async def _broadcast_to_session_groups(self, client, message_text, parse_mode):
        """Broadcast message to groups of a specific session with improved accuracy"""
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            async for dialog in client.get_dialogs():
                # Check if it's a group or supergroup
                if dialog.chat and dialog.chat.type in ["group", "supergroup"]:
                    # Check if bot is admin in the group and can send messages
                    try:
                        bot_member = await client.get_chat_member(dialog.chat.id, "me")
                        is_admin = bot_member.status in ["administrator", "creator"]
                        can_send_messages = getattr(bot_member, 'can_send_messages', True)
                        
                        # Skip if bot cannot send messages
                        if not can_send_messages:
                            results["failed"] += 1
                            results["errors"].append(f"{dialog.chat.title}: Cannot send messages")
                            continue
                    except:
                        # If we can't get bot member status, assume we can send messages
                        pass
                    
                    try:
                        await client.send_message(
                            chat_id=dialog.chat.id,
                            text=message_text,
                            parse_mode=parse_mode
                        )
                        results["success"] += 1
                    except FloodWait as e:
                        # Wait for the specified time before retrying
                        await asyncio.sleep(e.value)
                        try:
                            await client.send_message(
                                chat_id=dialog.chat.id,
                                text=message_text,
                                parse_mode=parse_mode
                            )
                            results["success"] += 1
                        except Exception as e2:
                            results["failed"] += 1
                            results["errors"].append(f"{dialog.chat.title}: {str(e2)}")
                    except (PeerFlood, UserPrivacyRestricted, ChatWriteForbidden) as e:
                        results["failed"] += 1
                        results["errors"].append(f"{dialog.chat.title}: {str(e)}")
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(f"{dialog.chat.title}: {str(e)}")
                        
        except Exception as e:
            results["error"] = str(e)
            
        return results
        
    def get_broadcast_logs(self):
        """Get broadcast logs"""
        return self.broadcast_logs
        
    async def get_group_list(self, client):
        """Get list of groups for a client with detailed information"""
        groups = []
        try:
            async for dialog in client.get_dialogs():
                # Check if it's a group or supergroup
                if dialog.chat and dialog.chat.type in ["group", "supergroup"]:
                    # Get additional group information
                    try:
                        # Get chat member count
                        member_count = await client.get_chat_members_count(dialog.chat.id)
                    except:
                        member_count = "Unknown"
                    
                    # Check if bot is admin in the group
                    try:
                        bot_member = await client.get_chat_member(dialog.chat.id, "me")
                        is_admin = bot_member.status in ["administrator", "creator"]
                    except:
                        is_admin = False
                    
                    groups.append({
                        "id": dialog.chat.id,
                        "title": dialog.chat.title,
                        "type": dialog.chat.type,
                        "member_count": member_count,
                        "is_admin": is_admin,
                        "username": getattr(dialog.chat, 'username', None)
                    })
        except Exception as e:
            print(f"Error getting group list: {e}")
            pass
        return groups
