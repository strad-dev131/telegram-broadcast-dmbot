
# Telegram Multi-Account Broadcasting Bot

A production-grade Telegram bot that enables secure multi-account management and broadcasting capabilities through DM commands. This bot allows you to manage multiple Telegram accounts, broadcast messages to all groups, and perform automated group management tasks.

## 🚀 Features

### 🔐 Account Management
- **OTP-based Authentication**: Secure login system using Telegram's native OTP
- **Multi-Account Support**: Manage multiple Telegram accounts simultaneously
- **2FA Support**: Full support for two-factor authentication
- **Secure Session Storage**: Encrypted session files with enterprise-grade security

### 📢 Broadcasting
- **Mass Broadcasting**: Send messages to all groups across all accounts
- **Markdown Support**: Rich text formatting with Markdown/HTML
- **Rate Limiting Protection**: Built-in flood protection and delays
- **Broadcast Statistics**: Detailed reporting of broadcast success rates

### 👥 Group Management
- **Smart Group Cleanup**: Automatically leave muted or read-only groups
- **Group Analytics**: Get detailed statistics about group memberships
- **Permission Checking**: Intelligent detection of restricted permissions

### 🛡️ Security & Privacy
- **Multiple Owner Support**: Support for multiple authorized users
- **Encrypted Storage**: All session data encrypted at rest
- **Secure Cleanup**: Automatic cleanup of disconnected accounts
- **Privacy-First**: No data collection or external dependencies

### 🔧 Production Ready
- **24/7 Operation**: Designed for continuous operation
- **Auto-Recovery**: Automatic error handling and recovery
- **Comprehensive Logging**: Detailed logging for monitoring
- **Cloud Deployment**: Ready for Heroku, Replit, and VPS deployment

## 📋 Commands

All commands work in the bot's DM only for security:

### Account Management
- `/start` - Show welcome message and available commands
- `/addid <phone_number>` - Add a new Telegram account (e.g., `/addid +1234567890`)
- `/otp <code>` - Enter OTP code during login process
- `/password <2fa_password>` - Enter 2FA password if enabled
- `/removeid <phone_number>` - Remove a specific account
- `/clearall` - Remove all accounts and clear all data

### Broadcasting
- `/broadcast <message>` - Broadcast message to all groups across all accounts
- `/left` - Leave muted/read-only groups across all accounts

### Information
- `/status` - Show bot status, active sessions, and statistics

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Telegram API credentials (API_ID and API_HASH)
- Telegram Bot Token
- MongoDB Atlas account (free tier)I_HASH)
- Telegram Bot Token

### Getting Telegram API Credentials

1. **Get API ID and API Hash**:
   - Go to [my.telegram.org](https://my.telegram.org/auth)
   - Enter your phone number and confirm with the code sent to your Telegram
   - Go to "API development tools"
   - Create a new application
   - Note down your `API_ID` and `API_HASH`

2. **Get Bot Token**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow the instructions
   - Choose a name and username for your bot
   - Save the bot token provided

3. **Get Your User ID**:
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - Note down your user ID (this will be your `OWNER_ID`)

4. **Setup MongoDB Atlas (Free)**:
   - Go to [MongoDB Atlas](https://cloud.mongodb.com/)
   - Create a free account
   - Create a new cluster (M0 Sandbox - FREE)
   - Create a database user
   - Get your connection string
   - Replace `<password>` with your database user password
   - Note down your MongoDB URL

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/strad-dev131/telegram-broadcast-dmbot.git
   cd telegram-broadcast-dmbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run the bot**:
   ```bash
   python main.py
   ```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram API Credentials
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here

# Multiple Owner Support (NEW)
# Supports multiple owners separated by commas
OWNER_IDS=123456789,987654321

# Legacy support (if OWNER_IDS not set)
OWNER_ID=your_telegram_user_id_here

# MongoDB Configuration (NEW)
MONGO_DB_URL=mongodb+srv://username:password@cluster.mongodb.net/telegram_bot?retryWrites=true&w=majorityD=your_telegram_user_id_here

# Optional Configuration
ENCRYPTION_KEY=your_strong_encryption_key_here
SESSIONS_DIR=sessions
LOG_LEVEL=INFO
LOG_FILE=bot.log
BROADCAST_DELAY=1.0
MAX_RETRIES=3
```

## 🚀 Deployment

### Deploy on Replit
1. Fork this repository on GitHub
2. Import the repository to Replit
3. Set up environment variables in Replit Secrets
4. Click "Run" to start the bot
5. Use "Deploy" for 24/7 hosting

### Deploy on Heroku
1. Fork this repository
2. Connect to Heroku
3. Set environment variables in Heroku config
4. Deploy from GitHub

### Deploy on VPS
1. Clone the repository
2. Install Python 3.10+
3. Install requirements: `pip install -r requirements.txt`
4. Set up environment variables
5. Run with process manager: `pm2 start main.py --interpreter python3`

## 🔧 Multiple Owner Configuration

The bot now supports multiple owners for better team management:

### Single Owner (Legacy):
```env
OWNER_ID=123456789
```

### Multiple Owners (Recommended):
```env
OWNER_IDS=123456789,987654321,555666777
```

All specified owner IDs will have full access to all bot commands.

## 📊 Features Overview

### Security Features
- ✅ Encrypted session storage
- ✅ Owner-only command access
- ✅ Multiple owner support
- ✅ Secure OTP handling
- ✅ 2FA authentication support

### Broadcasting Features
- ✅ Multi-account broadcasting
- ✅ Rate limiting protection
- ✅ Success rate reporting
- ✅ Error recovery
- ✅ Markdown/HTML support

### Management Features
- ✅ Account addition/removal
- ✅ Session cleanup
- ✅ Group optimization
- ✅ Health monitoring
- ✅ Comprehensive logging

## 🔍 Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check if BOT_TOKEN is correct
   - Verify your user ID is in OWNER_IDS
   - Check bot logs for errors

2. **OTP not working**:
   - Ensure API_ID and API_HASH are correct
   - Check if phone number format is correct (+1234567890)
   - Verify you're using the latest OTP code

3. **Broadcasting fails**:
   - Check if accounts are properly authenticated
   - Verify accounts have joined groups
   - Check rate limiting delays

4. **Session errors**:
   - Clear all sessions with `/clearall`
   - Re-add accounts with `/addid`
   - Check encryption key consistency

### Performance Optimization

1. Adjust `BROADCAST_DELAY` for faster/slower broadcasting
2. Increase `MAX_RETRIES` for better reliability
3. Monitor logs for performance insights
4. Use `/status` command for health checks

## 📝 Changelog

### v2.0.0 (Latest)
- ✅ Multiple owner support
- ✅ Enhanced error handling
- ✅ Improved database management
- ✅ Better session security
- ✅ Production-ready deployment
- ✅ Comprehensive logging
- ✅ Health monitoring system

### v1.0.0
- Initial release with basic functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This bot is for educational and legitimate business purposes only. Users are responsible for complying with Telegram's Terms of Service and applicable laws. The developers are not responsible for any misuse of this software.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the documentation

---

**Made with ❤️ for the Telegram community**

🔗 **Repository**: https://github.com/strad-dev131/telegram-broadcast-dmbot
