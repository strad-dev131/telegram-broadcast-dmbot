"""
OTP handling for Telegram account authentication
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pyrogram.client import Client
from pyrogram.errors import (
    SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired,
    PhoneNumberInvalid, FloodWait, AuthKeyUnregistered
)

from config import Config

logger = logging.getLogger(__name__)

class OTPHandler:
    """Handles OTP-based authentication for Telegram accounts"""

    def __init__(self):
        self.config = Config()
        self.current_client: Optional[Client] = None
        self.current_phone: Optional[str] = None
        self.phone_code_hash: Optional[str] = None
        self.pending_2fa: bool = False

    async def send_otp(self, phone_number: str) -> Dict[str, Any]:
        """Send OTP to the specified phone number"""
        try:
            # Clean up any existing client
            await self._cleanup_client()

            # Create new client for this session
            self.current_client = Client(
                f"temp_session_{phone_number.replace('+', '')}",
                api_id=self.config.API_ID,
                api_hash=self.config.API_HASH,
                workdir="sessions"
            )

            # Connect and send code
            await self.current_client.connect()

            # Send phone code
            sent_code = await self.current_client.send_code(phone_number)

            # Store information for OTP verification
            self.current_phone = phone_number
            self.phone_code_hash = sent_code.phone_code_hash
            self.pending_2fa = False

            logger.info(f"OTP sent successfully to {phone_number}")
            return {
                'success': True,
                'message': f'OTP sent to {phone_number}',
                'type': sent_code.type
            }

        except PhoneNumberInvalid:
            await self._cleanup_client()
            return {'success': False, 'error': 'Invalid phone number format'}

        except FloodWait as e:
            await self._cleanup_client()
            return {'success': False, 'error': f'Rate limited. Try again in {e.value} seconds'}

        except Exception as e:
            logger.error(f"Error sending OTP to {phone_number}: {e}")
            await self._cleanup_client()
            return {'success': False, 'error': str(e)}

    async def verify_otp(self, otp_code: str) -> Dict[str, Any]:
        """Verify OTP code and complete authentication"""
        try:
            if not self.current_client or not self.current_phone or not self.phone_code_hash:
                return {'success': False, 'error': 'No pending OTP request'}

            # Attempt to sign in with the code
            try:
                await self.current_client.sign_in(
                    self.current_phone,
                    self.phone_code_hash,
                    otp_code
                )

                # Get session string
                session_string = await self.current_client.export_session_string()

                # Store phone before cleanup
                verified_phone = self.current_phone

                # Clean up
                await self._cleanup_client()

                logger.info(f"OTP verification successful for {verified_phone}")
                return {
                    'success': True,
                    'session_string': session_string,
                    'needs_password': False,
                    'phone_number': verified_phone
                }

            except SessionPasswordNeeded:
                # 2FA is required
                self.pending_2fa = True
                logger.info(f"2FA required for {self.current_phone}")
                return {
                    'success': True,
                    'needs_password': True,
                    'message': '2FA password required'
                }

        except PhoneCodeInvalid:
            return {'success': False, 'error': 'Invalid OTP code'}

        except PhoneCodeExpired:
            await self._cleanup_client()
            return {'success': False, 'error': 'OTP code expired. Please request a new one'}

        except FloodWait as e:
            return {'success': False, 'error': f'Rate limited. Try again in {e.value} seconds'}

        except Exception as e:
            logger.error(f"Error verifying OTP for {self.current_phone}: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            if self.current_client:
                try:
                    await self.current_client.disconnect()
                    self.current_client = None
                except:
                    pass

    async def verify_2fa(self, password: str) -> Dict[str, Any]:
        """Verify 2FA password"""
        try:
            if not self.current_client or not self.pending_2fa:
                return {'success': False, 'error': 'No pending 2FA request'}

            # Complete 2FA authentication
            await self.current_client.check_password(password)

            # Get session string
            session_string = await self.current_client.export_session_string()

            # Store phone before cleanup
            verified_phone = self.current_phone

            # Clean up
            await self._cleanup_client()

            logger.info(f"2FA verification successful for {verified_phone}")
            return {
                'success': True,
                'session_string': session_string,
                'phone_number': verified_phone
            }

        except Exception as e:
            logger.error(f"Error verifying 2FA: {e}")
            return {'success': False, 'error': 'Invalid 2FA password'}
        finally:
            if self.current_client:
                try:
                    await self.current_client.disconnect()
                    self.current_client = None
                except:
                    pass

    def has_pending_otp(self) -> bool:
        """Check if there's a pending OTP request"""
        return (self.current_client is not None and 
                self.current_phone is not None and 
                self.phone_code_hash is not None and 
                not self.pending_2fa)

    def has_pending_2fa(self) -> bool:
        """Check if there's a pending 2FA request"""
        return (self.current_client is not None and 
                self.pending_2fa)

    def get_current_phone(self) -> Optional[str]:
        """Get the current phone number being processed"""
        return self.current_phone

    async def _cleanup_client(self):
        """Clean up current client and reset state"""
        if self.current_client:
            try:
                if self.current_client.is_connected:
                    await self.current_client.disconnect()

                # Remove temporary session file
                if self.current_phone:
                    temp_session_file = f"sessions/temp_session_{self.current_phone.replace('+', '')}.session"
                    try:
                        import os
                        if os.path.exists(temp_session_file):
                            os.remove(temp_session_file)
                    except Exception:
                        pass

            except Exception as e:
                logger.warning(f"Error cleaning up client: {e}")
            finally:
                self.current_client = None

        # Reset state
        self.current_phone = None
        self.phone_code_hash = None
        self.pending_2fa = False

    async def cancel_current_request(self):
        """Cancel any pending OTP or 2FA request"""
        await self._cleanup_client()
        logger.info("Current authentication request cancelled")