import os
import json
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client
import aiofiles
from config import SESSION_DIR, SESSION_EXPIRY_HOURS

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_data = {}
        self.ensure_session_dir()
        
    def ensure_session_dir(self):
        """Ensure the session directory exists"""
        if not os.path.exists(SESSION_DIR):
            os.makedirs(SESSION_DIR)
            
    async def load_session_data(self):
        """Load session data from file"""
        try:
            if os.path.exists(f"{SESSION_DIR}/sessions.json"):
                async with aiofiles.open(f"{SESSION_DIR}/sessions.json", 'r') as f:
                    content = await f.read()
                    if content:
                        self.session_data = json.loads(content)
        except Exception as e:
            print(f"Error loading session data: {e}")
            
    async def save_session_data(self):
        """Save session data to file"""
        try:
            async with aiofiles.open(f"{SESSION_DIR}/sessions.json", 'w') as f:
                await f.write(json.dumps(self.session_data))
        except Exception as e:
            print(f"Error saving session data: {e}")
            
    async def add_session(self, phone_number, client):
        """Add a new session"""
        self.sessions[phone_number] = client
        self.session_data[phone_number] = {
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "groups": 0,
            "last_broadcast": None
        }
        await self.save_session_data()
        
    async def remove_session(self, phone_number):
        """Remove a session"""
        if phone_number in self.sessions:
            try:
                await self.sessions[phone_number].stop()
            except:
                pass
            del self.sessions[phone_number]
            
        if phone_number in self.session_data:
            # Remove session file if it exists
            session_file = f"{SESSION_DIR}/{phone_number}.session"
            if os.path.exists(session_file):
                os.remove(session_file)
            del self.session_data[phone_number]
            
        await self.save_session_data()
        
    async def clear_all_sessions(self):
        """Clear all sessions"""
        phone_numbers = list(self.sessions.keys())
        for phone_number in phone_numbers:
            await self.remove_session(phone_number)
            
    def get_session(self, phone_number):
        """Get a session by phone number"""
        return self.sessions.get(phone_number)
        
    def get_all_sessions(self):
        """Get all active sessions"""
        return self.sessions
        
    def update_session_usage(self, phone_number):
        """Update last used timestamp for a session"""
        if phone_number in self.session_data:
            self.session_data[phone_number]["last_used"] = datetime.now().isoformat()
            
    async def update_session_groups(self, phone_number, count):
        """Update group count for a session"""
        if phone_number in self.session_data:
            self.session_data[phone_number]["groups"] = count
            await self.save_session_data()
            
    def update_last_broadcast(self, phone_number):
        """Update last broadcast timestamp for a session"""
        if phone_number in self.session_data:
            self.session_data[phone_number]["last_broadcast"] = datetime.now().isoformat()
            
    def get_session_status(self):
        """Get status information for all sessions"""
        status = {}
        for phone_number, data in self.session_data.items():
            # Check if session has expired
            last_used = datetime.fromisoformat(data["last_used"])
            expiry_time = last_used + timedelta(hours=SESSION_EXPIRY_HOURS)
            expired = datetime.now() > expiry_time
            
            status[phone_number] = {
                "groups": data["groups"],
                "last_broadcast": data["last_broadcast"],
                "expired": expired,
                "expiry_time": expiry_time.isoformat()
            }
        return status
        
    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for phone_number, data in self.session_data.items():
            last_used = datetime.fromisoformat(data["last_used"])
            expiry_time = last_used + timedelta(hours=SESSION_EXPIRY_HOURS)
            if current_time > expiry_time:
                expired_sessions.append(phone_number)
                
        for phone_number in expired_sessions:
            await self.remove_session(phone_number)
            
        if expired_sessions:
            await self.save_session_data()
