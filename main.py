import asyncio
import time
import os
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID
from session_manager import SessionManager
from otp_handler import OTPHandler
from broadcast import BroadcastManager
from group_utils import GroupManager

# Initialize managers
session_manager = SessionManager()
otp_handler = OTPHandler(session_manager)
broadcast_manager = BroadcastManager(session_manager)
group_manager = GroupManager(session_manager)

# Bot start time
bot_start_time = time.time()

# Rate limiting storage
user_last_command = {}
user_command_count = {}

# Initialize the bot client
app = Client(
    "telegram-broadcast-dmbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def is_owner(func):
    """Decorator to check if user is owner"""
    async def wrapper(client, message: Message):
        if message.from_user.id != OWNER_ID:
            await message.reply("You are not authorized to use this bot.")
            return
        return await func(client, message)
    return wrapper

def rate_limit(func):
    """Decorator for rate limiting"""
    async def wrapper(client, message: Message):
        user_id = message.from_user.id
        current_time = time.time()
        
        # Check if user has previous command time
        if user_id in user_last_command:
            # Reset count if window has passed
            if current_time - user_last_command[user_id] > 60:  # 60 seconds window
                user_command_count[user_id] = 0
                
        # Initialize if not exists
        if user_id not in user_command_count:
            user_command_count[user_id] = 0
            
        # Check rate limit
        if user_command_count[user_id] >= 10:  # Max 10 commands per minute
            await message.reply("Rate limit exceeded. Please wait before sending more commands.")
            return
            
        # Update command count
        user_command_count[user_id] += 1
        user_last_command[user_id] = current_time
        
        return await func(client, message)
    return wrapper

@app.on_message(filters.command("start"))
@is_owner
@rate_limit
async def start_command(client, message: Message):
    """Handle /start command"""
    start_text = """
🤖 **Telegram Broadcasting Bot** 🤖

**Available Commands:**
/addid <phone_number> - Add new account
/otp <code> - Verify OTP
/password <2fa_password> - 2FA authentication
/scan - Scan all groups for added accounts
/broadcast <message> - Broadcast message to groups
/left - Leave muted/read-only groups
/status - Show session status
/removeid <phone_number> - Remove account
/clearall - Clear all sessions

🔒 *Only the bot owner can use these commands.*
"""
    await message.reply(start_text, parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.command("addid"))
@is_owner
@rate_limit
async def addid_command(client, message: Message):
    """Handle /addid command"""
    if len(message.command) < 2:
        await message.reply("Please provide a phone number. Usage: /addid <phone_number>")
        return
        
    phone_number = message.command[1]
    
    # Check if session already exists
    if session_manager.get_session(phone_number):
        await message.reply(f"Account with phone number {phone_number} is already added.")
        return
        
    # Send OTP
    success, response = await otp_handler.send_otp(phone_number)
    await message.reply(response)

@app.on_message(filters.command("otp"))
@is_owner
@rate_limit
async def otp_command(client, message: Message):
    """Handle /otp command"""
    if len(message.command) < 2:
        await message.reply("Please provide the OTP code. Usage: /otp <code>")
        return
        
    # Get the latest pending login
    pending_logins = list(otp_handler.pending_logins.keys())
    if not pending_logins:
        await message.reply("No pending login found. Please use /addid first.")
        return
        
    phone_number = pending_logins[0]  # Get the first pending login
    otp_code = message.command[1]
    
    # Verify OTP
    success, response = await otp_handler.verify_otp(phone_number, otp_code)
    await message.reply(response)

@app.on_message(filters.command("password"))
@is_owner
@rate_limit
async def password_command(client, message: Message):
    """Handle /password command for 2FA"""
    if len(message.command) < 2:
        await message.reply("Please provide the 2FA password. Usage: /password <password>")
        return
        
    # Get the latest pending login
    pending_logins = list(otp_handler.pending_logins.keys())
    if not pending_logins:
        await message.reply("No pending login found. Please use /addid first.")
        return
        
    phone_number = pending_logins[0]  # Get the first pending login
    password = message.text[len("/password "):]  # Get everything after the command
    
    # Handle 2FA
    success, response = await otp_handler.handle_2fa(phone_number, password)
    await message.reply(response)

@app.on_message(filters.command("broadcast"))
@is_owner
@rate_limit
async def broadcast_command(client, message: Message):
    """Handle /broadcast command"""
    if len(message.command) < 2:
        await message.reply("Please provide a message to broadcast. Usage: /broadcast <message>")
        return
        
    broadcast_text = message.text[len("/broadcast "):]
    
    if not broadcast_text:
        await message.reply("Please provide a message to broadcast.")
        return
        
    # Check if there are any active sessions
    if not session_manager.get_all_sessions():
        await message.reply("No active sessions found. Please add an account first using /addid.")
        return
        
    # Send processing message
    processing_msg = await message.reply("Broadcasting message to all groups...")
    
    # Broadcast message
    results = await broadcast_manager.broadcast_to_groups(broadcast_text)
    
    # Format results
    result_text = "**Broadcast Results:**\n\n"
    total_success = 0
    total_failed = 0
    
    for phone_number, result in results.items():
        if "error" in result:
            result_text += f"📱 {phone_number}: Error - {result['error']}\n"
        else:
            result_text += f"📱 {phone_number}:\n"
            result_text += f"   ✅ Success: {result['success']}\n"
            result_text += f"   ❌ Failed: {result['failed']}\n"
            total_success += result['success']
            total_failed += result['failed']
            
            if result['errors']:
                result_text += f"   Errors: {', '.join(result['errors'][:3])}"  # Show first 3 errors
                if len(result['errors']) > 3:
                    result_text += f" (and {len(result['errors']) - 3} more...)"
                result_text += "\n"
        result_text += "\n"
        
    result_text += f"📊 **Total:**\n✅ Success: {total_success}\n❌ Failed: {total_failed}"
    
    # Edit the processing message with results
    await processing_msg.edit(result_text, parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.command("left"))
@is_owner
@rate_limit
async def left_command(client, message: Message):
    """Handle /left command"""
    # Check if there are any active sessions
    if not session_manager.get_all_sessions():
        await message.reply("No active sessions found. Please add an account first using /addid.")
        return
        
    # Send processing message
    processing_msg = await message.reply("Leaving muted/read-only groups...")
    
    # Leave muted groups
    results = await group_manager.leave_muted_groups()
    
    # Format results
    result_text = "**Left Groups Results:**\n\n"
    
    for phone_number, result in results.items():
        if "error" in result:
            result_text += f"📱 {phone_number}: Error - {result['error']}\n"
        else:
            result_text += f"📱 {phone_number}:\n"
            result_text += f"   ✅ Left: {result['left']}\n"
            result_text += f"   ❌ Failed: {result['failed']}\n"
            if result['errors']:
                result_text += f"   Errors: {', '.join(result['errors'][:3])}\n"
        result_text += "\n"
        
    # Edit the processing message with results
    await processing_msg.edit(result_text, parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.command("status"))
@is_owner
@rate_limit
async def status_command(client, message: Message):
    """Handle /status command"""
    # Get bot uptime
    uptime_seconds = int(time.time() - bot_start_time)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_seconds = uptime_seconds % 60
    
    # Get session status
    session_status = session_manager.get_session_status()
    
    # Format status message
    status_text = f"**Bot Status**\n"
    status_text += f"⏱ Uptime: {uptime_hours}h {uptime_minutes}m {uptime_seconds}s\n\n"
    
    if not session_status:
        status_text += "No active sessions.\n"
    else:
        status_text += "**Active Sessions:**\n"
        for phone_number, data in session_status.items():
            status_text += f"📱 {phone_number}\n"
            status_text += f"   📚 Groups: {data['groups']}\n"
            if data['last_broadcast']:
                status_text += f"   📢 Last Broadcast: {data['last_broadcast']}\n"
            else:
                status_text += f"   📢 Last Broadcast: Never\n"
            status_text += f"   ⏰ Expired: {'Yes' if data['expired'] else 'No'}\n"
            status_text += "\n"
            
    await message.reply(status_text, parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.command("removeid"))
@is_owner
@rate_limit
async def removeid_command(client, message: Message):
    """Handle /removeid command"""
    if len(message.command) < 2:
        await message.reply("Please provide a phone number. Usage: /removeid <phone_number>")
        return
        
    phone_number = message.command[1]
    
    # Check if session exists
    if not session_manager.get_session(phone_number):
        await message.reply(f"No session found for phone number {phone_number}.")
        return
        
    # Remove session
    await session_manager.remove_session(phone_number)
    await message.reply(f"Session for {phone_number} removed successfully.")

@app.on_message(filters.command("scan"))
@is_owner
@rate_limit
async def scan_command(client, message: Message):
    """Handle /scan command"""
    # Check if there are any active sessions
    if not session_manager.get_all_sessions():
        await message.reply("No active sessions found. Please add an account first using /addid.")
        return
        
    # Send processing message
    processing_msg = await message.reply("Scanning all groups for added accounts...")
    
    # Scan groups for each session
    results = {}
    for phone_number, client in session_manager.get_all_sessions().items():
        try:
            # Get group list
            groups = await broadcast_manager.get_group_list(client)
            
            # Count groups
            group_count = len(groups)
            
            # Update session group count
            await session_manager.update_session_groups(phone_number, group_count)
            
            results[phone_number] = {
                "groups": group_count,
                "group_list": groups
            }
        except Exception as e:
            results[phone_number] = {"error": str(e)}
    
    # Format results
    result_text = "**Scan Results:**\n\n"
    
    for phone_number, result in results.items():
        if "error" in result:
            result_text += f"📱 {phone_number}: Error - {result['error']}\n"
        else:
            result_text += f"📱 {phone_number}:\n"
            result_text += f"   📚 Groups: {result['groups']}\n"
            if result['groups'] > 0:
                result_text += "   Group List:\n"
                for group in result['group_list'][:10]:  # Show first 10 groups
                    result_text += f"   - {group['title']} ({group['type']})\n"
                if result['groups'] > 10:
                    result_text += f"   ... and {result['groups'] - 10} more groups\n"
            result_text += "\n"
            
    # Edit the processing message with results
    await processing_msg.edit(result_text, parse_mode=enums.ParseMode.MARKDOWN)

@app.on_message(filters.command("clearall"))
@is_owner
@rate_limit
async def clearall_command(client, message: Message):
    """Handle /clearall command"""
    # Confirm with user
    confirm_msg = await message.reply("Are you sure you want to clear all sessions? This will remove all accounts. Reply with 'YES' to confirm.")
    
    # Wait for confirmation
    try:
        response = await client.listen.Message(
            filters.text & filters.user(OWNER_ID),
            timeout=30,
            chat_id=message.chat.id
        )
        
        if response and response.text.strip().upper() == "YES":
            # Clear all sessions
            await session_manager.clear_all_sessions()
            await message.reply("All sessions cleared successfully.")
        else:
            await message.reply("Operation cancelled.")
            
    except asyncio.TimeoutError:
        await message.reply("No confirmation received. Operation cancelled.")

async def main():
    """Main function to start the bot"""
    # Load session data
    await session_manager.load_session_data()
    
    # Start the bot
    await app.start()
    print("Telegram Broadcasting Bot started!")
    
    # Run forever
    await asyncio.idle()
    
    # Stop the bot
    await app.stop()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
