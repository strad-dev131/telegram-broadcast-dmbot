import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, SESSION_DIR

class OTPHandler:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.pending_logins = {}  # Store pending logins with phone numbers
        
    async def send_otp(self, phone_number):
        """Send OTP to the provided phone number"""
        try:
            # Create a temporary client for login
            temp_client = Client(
                f"{SESSION_DIR}/{phone_number}",
                api_id=API_ID,
                api_hash=API_HASH,
                phone_number=phone_number
            )
            
            # Send code request
            sent_code = await temp_client.send_code(phone_number)
            
            # Store the client for later use in OTP verification
            self.pending_logins[phone_number] = {
                "client": temp_client,
                "phone_code_hash": sent_code.phone_code_hash
            }
            
            return True, "OTP sent successfully. Please use /otp <code> to complete login."
        except Exception as e:
            return False, f"Failed to send OTP: {str(e)}"
            
    async def verify_otp(self, phone_number, otp_code):
        """Verify OTP and complete login"""
        try:
            if phone_number not in self.pending_logins:
                return False, "No pending login for this phone number. Please use /addid first."
                
            login_data = self.pending_logins[phone_number]
            temp_client = login_data["client"]
            phone_code_hash = login_data["phone_code_hash"]
            
            # Try to sign in with the provided OTP
            try:
                signed_in_user = await temp_client.sign_in(
                    phone_number=phone_number,
                    phone_code_hash=phone_code_hash,
                    phone_code=otp_code
                )
                
                # Login successful, add to session manager
                await self.session_manager.add_session(phone_number, temp_client)
                del self.pending_logins[phone_number]
                
                # Get group count
                groups = await self.get_group_count(temp_client)
                await self.session_manager.update_session_groups(phone_number, groups)
                
                return True, f"Login successful for {signed_in_user.first_name}!"
            except Exception as e:
                return False, f"Failed to verify OTP: {str(e)}"
                
        except Exception as e:
            return False, f"Error during OTP verification: {str(e)}"
            
    async def handle_2fa(self, phone_number, password):
        """Handle 2FA authentication"""
        try:
            if phone_number not in self.pending_logins:
                return False, "No pending login for this phone number."
                
            login_data = self.pending_logins[phone_number]
            temp_client = login_data["client"]
            
            # Try to sign in with password
            try:
                signed_in_user = await temp_client.check_password(password)
                
                # Login successful, add to session manager
                await self.session_manager.add_session(phone_number, temp_client)
                del self.pending_logins[phone_number]
                
                # Get group count
                groups = await self.get_group_count(temp_client)
                await self.session_manager.update_session_groups(phone_number, groups)
                
                return True, f"2FA successful! Logged in as {signed_in_user.first_name}."
            except Exception as e:
                return False, f"Failed to authenticate with password: {str(e)}"
                
        except Exception as e:
            return False, f"Error during 2FA: {str(e)}"
            
    async def get_group_count(self, client):
        """Get the number of groups the account is in with improved accuracy"""
        try:
            count = 0
            async for dialog in client.get_dialogs():
                # Check if it's a group or supergroup
                if dialog.chat and dialog.chat.type in ["group", "supergroup"]:
                    # Check if bot is admin in the group and can send messages
                    try:
                        bot_member = await client.get_chat_member(dialog.chat.id, "me")
                        can_send_messages = getattr(bot_member, 'can_send_messages', True)
                        
                        # Only count groups where bot can send messages
                        if can_send_messages:
                            count += 1
                    except:
                        # If we can't get bot member status, count the group anyway
                        count += 1
            return count
        except Exception as e:
            print(f"Error getting group count: {e}")
            return 0
