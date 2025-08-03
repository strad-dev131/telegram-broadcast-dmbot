import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv('API_ID', '25387587'))
API_HASH = os.getenv('API_HASH', '7b8e2e5bb84c617a474656ad7439ea6a')
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_from_@BotFather')

# Bot owner ID
OWNER_ID = int(os.getenv('OWNER_ID', '7784241637'))

# Session directory
SESSION_DIR = 'sessions'

# Rate limiting settings
RATE_LIMIT_WINDOW = 60  # seconds
MAX_COMMANDS_PER_WINDOW = 10

# Session expiry settings
SESSION_EXPIRY_HOURS = 24

# Default values
DEFAULT_PARSE_MODE = 'markdown'
