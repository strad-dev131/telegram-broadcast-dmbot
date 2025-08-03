#!/bin/bash

# Check if tmux is installed
if ! command -v tmux &> /dev/null
then
    echo "tmux could not be found. Installing tmux..."
    sudo apt update && sudo apt install -y tmux
fi

# Create a new tmux session and run the bot
tmux new-session -d -s telegram-bot 'python3 main.py'

echo "Telegram bot is now running in a tmux session named 'telegram-bot'"
echo "To attach to the session, run: tmux attach -t telegram-bot"
echo "To detach from the session, press Ctrl+B then D"
