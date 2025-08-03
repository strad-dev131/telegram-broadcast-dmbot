import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait

class GroupManager:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        
    async def leave_muted_groups(self):
        """Leave groups marked as read-only or muted"""
        all_results = {}
        
        for phone_number, client in self.session_manager.get_all_sessions().items():
            try:
                results = await self._leave_muted_groups_for_session(client)
                all_results[phone_number] = results
            except Exception as e:
                all_results[phone_number] = {"error": str(e)}
                
        return all_results
        
    async def _leave_muted_groups_for_session(self, client):
        """Leave muted groups for a specific session with improved accuracy"""
        results = {
            "left": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            async for dialog in client.get_dialogs():
                if dialog.chat and dialog.chat.type in ["group", "supergroup"]:
                    # Check if group is muted or read-only
                    try:
                        # Check notification settings
                        notifications = getattr(dialog.chat, 'notifications', None)
                        # Check if group is read-only
                        try:
                            bot_member = await client.get_chat_member(dialog.chat.id, "me")
                            is_admin = bot_member.status in ["administrator", "creator"]
                            can_send_messages = getattr(bot_member, 'can_send_messages', True)
                        except:
                            is_admin = False
                            can_send_messages = True
                        
                        # Leave group if it's muted or read-only
                        if (notifications is not None and not notifications) or not can_send_messages:
                            try:
                                await client.leave_chat(dialog.chat.id)
                                results["left"] += 1
                            except FloodWait as e:
                                # Wait for the specified time before retrying
                                await asyncio.sleep(e.value)
                                try:
                                    await client.leave_chat(dialog.chat.id)
                                    results["left"] += 1
                                except Exception as e2:
                                    results["failed"] += 1
                                    results["errors"].append(f"{dialog.chat.title}: {str(e2)}")
                            except Exception as e:
                                results["failed"] += 1
                                results["errors"].append(f"{dialog.chat.title}: {str(e)}")
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(f"{dialog.chat.title}: {str(e)}")
                        
        except Exception as e:
            results["error"] = str(e)
            
        return results
        
    async def get_group_status(self, client):
        """Get detailed status of groups (muted, read-only, etc.)"""
        groups = []
        try:
            async for dialog in client.get_dialogs():
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
                        # Check if bot can send messages
                        can_send_messages = getattr(bot_member, 'can_send_messages', True)
                    except:
                        is_admin = False
                        can_send_messages = False
                    
                    # Check notification settings
                    try:
                        # This is a simplified check - in reality, you'd want to check
                        # actual notification settings
                        notifications = "enabled" if dialog.chat.notifications else "disabled"
                    except:
                        notifications = "unknown"
                    
                    groups.append({
                        "id": dialog.chat.id,
                        "title": dialog.chat.title,
                        "type": dialog.chat.type,
                        "member_count": member_count,
                        "is_admin": is_admin,
                        "can_send_messages": can_send_messages,
                        "notifications": notifications,
                        "username": getattr(dialog.chat, 'username', None)
                    })
        except Exception as e:
            print(f"Error getting group status: {e}")
            pass
        return groups
