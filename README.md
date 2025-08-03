elegram-broadcast-dmbot/README.md
</path>
<\content>
# Telegram Broadcasting Bot (DM-Only Commands)

A high-performance, production-grade Telegram broadcasting bot with multi-account support, optimized for speed and security.

## Features

### Core Features:
- **OTP-based Login**: Secure login with OTP, 2FA support
- **Multi-Account Management**: Manage multiple Telegram accounts
- **Broadcasting**: Send messages to all groups with a single command
- **Group Management**: Leave muted/read-only groups
- **Session & Account Management**: Full session lifecycle with cleanup

### Security & Privacy:
- **Access Control**: Only the bot owner can issue commands
- **Secure Session Storage**: File-based encrypted session storage
- **Audit Logging**: Every command is logged for security
- **Rate Limiting & CAPTCHA**: Rate limiting and CAPTCHA for OTP requests

### Performance & Scalability:
- **Optimized for Speed**: Built with asyncio for high performance
- **Session Expiry & Migration**: Automatic session expiry and migration
- **Background Task Management**: Asynchronous operations with proper error handling

## Tech Stack
- **Python 3.10+**: Core language
- **Pyrogram**: Telegram API framework
- **Asyncio**: For asynchronous operations
- **File-based session storage**: No database required
- **Heroku or Ubuntu VPC**: Deployment with auto-restart and persistent uptime

## Deployment

### Heroku Deployment:
1. Create a new app in your Heroku dashboard
2. Connect your GitHub repository
3. Enable automatic deploys from the `main` branch
4. Add the following buildpacks in the settings:
   - `https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git`
5. Add the following environment variables in the "Config Vars" of your app:
   - `BOT_TOKEN`: Your bot token from @BotFather
   - `API_ID`: Your API ID from my.telegram.org
   - `API_HASH`: Your API hash from my.telegram.org
   - `OWNER_ID`: Your Telegram user ID
6. Deploy the app

### Ubuntu VPS Deployment:
1. Install dependencies:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip
   pip3 install -r requirements.txt
   ```
2. Create a `.env` file with your credentials
3. Run the bot:
   ```bash
   python3 main.py
   ```

### Ubuntu VPS Deployment with tmux (Persistent Operation):
1. Install dependencies:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip tmux
   pip3 install -r requirements.txt
   ```
2. Create a `.env` file with your credentials
3. Run the bot with the provided script:
   ```bash
   ./run.sh
   ```

### Ubuntu VPS Deployment with systemd (Automatic Restart):
1. Install dependencies:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip
   pip3 install -r requirements.txt
   ```
2. Create a `.env` file with your credentials
3. Copy the service file to systemd:
   ```bash
   sudo cp telegram-bot.service /etc/systemd/system/
   ```
4. Update the service file with your credentials:
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```
5. Enable and start the service:
   ```bash
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   ```

### Docker Deployment:
1. Install Docker and Docker Compose
2. Create a `.env` file with your credentials
3. Run the bot:
   ```bash
   docker-compose up -d
   ```

### Docker Build and Run:
1. Build the Docker image:
   ```bash
   docker build -t telegram-broadcast-bot .
   ```
2. Run the container:
   ```bash
   docker run -d --name telegram-broadcast-bot \
     -v ./sessions:/app/sessions \
     -v ./.env:/app/.env \
     -e BOT_TOKEN=$BOT_TOKEN \
     -e API_ID=$API_ID \
     -e API_HASH=$API_HASH \
     -e OWNER_ID=$OWNER_ID \
     telegram-broadcast-bot
   ```

## Usage

1. Start the bot:
   - For Heroku: The bot will start automatically
   - For VPS: `python3 main.py`

2. Use the following commands:
   - `/start` - Show available commands
   - `/addid <phone_number>` - Add a new account
   - `/otp <code>` - Verify OTP
   - `/password <2fa_password>` - 2FA authentication
   - `/broadcast <message>` - Broadcast a message to all groups
   - `/left` - Leave muted/read-only groups
   - `/status` - Show session status
   - `/removeid <phone_number>` - Remove an account
   - `/clearall` - Clear all sessions

## Project Structure
```
telegram-broadcast-dmbot/
├── main.py               # Main bot logic and command handling
├── session_manager.py    # Session management
├── otp_handler.py        # OTP handling
├── broadcast.py          # Broadcasting functionality
├── group_utils.py        # Group management
├── config.py             # Configuration
├── requirements.txt      # Dependencies
├── Procfile              # Heroku deployment
├── runtime.txt           # Python version for Heroku
├── README.md             # This file
├── LICENSE               # License file
├── setup.py              # Setup file for packaging
├── .env                  # Environment variables (not in repo)
├── .gitignore            # Git ignore file
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── run.sh                # tmux startup script
├── telegram-bot.service  # systemd service file
└── sessions/             # Session files
```

## Environment Variables

Create a `.env` file with the following content:
```
BOT_TOKEN=your_bot_token_from_@BotFather
API_ID=25387587
API_HASH=7b8e2e5bb84c617a474656ad7439ea6a
OWNER_ID=7784241637
```

To get your `BOT_TOKEN`:
1. Open Telegram and search for @BotFather
2. Start a chat with @BotFather
3. Send `/newbot` command
4. Follow the instructions to create a new bot
5. Copy the token provided by @BotFather

## Troubleshooting

### Common Issues:

1. **"You are not authorized to use this bot"**:
   - Check that your `OWNER_ID` in the `.env` file matches your Telegram user ID.
   - Restart the bot after updating the `.env` file.

2. **"Failed to send OTP"**:
   - Verify that your `API_ID` and `API_HASH` are correct.
   - Ensure the phone number is in international format (e.g., +1234567890).

3. **"Rate limit exceeded"**:
   - Wait for a minute before sending more commands.
   - The bot allows 10 commands per minute per user.

4. **"No active sessions found"**:
   - Add an account using `/addid <phone_number>` first.
   - Ensure the account login was successful.

5. **Docker issues**:
   - Ensure the `.env` file exists in the project directory.
   - Check that Docker and Docker Compose are properly installed.

### Logs and Debugging:

- Check the terminal output for error messages.
- For systemd deployment, check logs with:
  ```bash
  sudo journalctl -u telegram-bot -f
  ```
- For Docker deployment, check logs with:
  ```bash
  docker logs telegram-broadcast-bot
  ```

## License

This project is licensed under the MIT License.
