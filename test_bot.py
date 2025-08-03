import asyncio
import sys
import os

# Add the current directory to the path so we can import the bot modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from session_manager import SessionManager
from otp_handler import OTPHandler
from broadcast import BroadcastManager
from group_utils import GroupManager

async def test_session_manager():
    """Test the session manager"""
    print("Testing SessionManager...")
    session_manager = SessionManager()
    print("SessionManager initialized successfully")

async def test_otp_handler():
    """Test the OTP handler"""
    print("Testing OTPHandler...")
    session_manager = SessionManager()
    otp_handler = OTPHandler(session_manager)
    print("OTPHandler initialized successfully")

async def test_broadcast_manager():
    """Test the broadcast manager"""
    print("Testing BroadcastManager...")
    session_manager = SessionManager()
    broadcast_manager = BroadcastManager(session_manager)
    print("BroadcastManager initialized successfully")

async def test_group_manager():
    """Test the group manager"""
    print("Testing GroupManager...")
    session_manager = SessionManager()
    group_manager = GroupManager(session_manager)
    print("GroupManager initialized successfully")

async def main():
    """Main test function"""
    print("Running bot tests...")
    
    try:
        await test_session_manager()
        await test_otp_handler()
        await test_broadcast_manager()
        await test_group_manager()
        
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
