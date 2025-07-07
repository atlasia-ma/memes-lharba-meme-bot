# Discord Meme Bot Deployment Guide

## Overview
This guide documents the deployment process for the Discord Meme Bot that uses the Gradio API for meme recommendations instead of a local database.

## Architecture Changes
- **Previous**: Local meme database with sentence transformers
- **Current**: Remote Gradio API at `atlasia/moul_lmemes`
- **Benefits**: Reduced server resources, centralized meme management, improved AI recommendations

## Files Created/Modified

### 1. `gradiomeme_agent_api.py` (New)
```python
from gradio_client import Client

class GradioMemeAgent:
    def __init__(self):
        """Initialize the Gradio client for meme finding."""
        self.client = Client("atlasia/moul_lmemes")
    
    def find_relevant_meme(self, user_input):
        """
        Find a relevant meme based on user input using the Gradio API.
        
        Args:
            user_input (str): The text input to find memes for
            
        Returns:
            dict: Result from the API containing meme information
        """
        try:
            result = self.client.predict(
                user_input=user_input,
                api_name="/query_memes"
            )
            print(f"Gradio API result: {result}")
            return result
        except Exception as e:
            print(f"Error calling Gradio API: {e}")
            return None
```

### 2. `discord_meme_bot.py` (Modified)
- **Import changed**: `from meme_agent import MemeFinder` → `from gradiomeme_agent_api import GradioMemeAgent`
- **Initialization**: `MemeFinder(use_llm=True, hf_token=hf_token)` → `GradioMemeAgent()`
- **Removed**: HF token dependency for local setup

### 3. `pyproject.toml` (Modified)
- **Added dependency**: `"gradio_client"` to the dependencies list

## Local Development Setup

### Prerequisites
- Python 3.8+
- uv package manager (recommended) or pip

### Installation Steps
```bash
# 1. Clone/navigate to project directory
cd memebot

# 2. Create virtual environment with uv
uv venv .venv

# 3. Install dependencies
uv pip install -e .
# OR with pip: pip install -e .

# 4. Activate virtual environment
source .venv/bin/activate

# 5. Set up environment variables
# Create .env file with:
# DISCORD_TOKEN=your_discord_token_here
# HF_TOKEN=your_hf_token_here (optional, not used anymore)

# 6. Run the bot
python discord_meme_bot.py
```

## Server Deployment (Atlasia)

### Server Information
- **Host**: `ec2-13-38-156-22.eu-west-3.compute.amazonaws.com`
- **User**: `ubuntu`
- **SSH Key**: `/home/nyanpasu/.ssh/platform_vm.pem`
- **Project Path**: `/home/ubuntu/discord_meme_bot`

### Deployment Steps

#### 1. SSH Access
```bash
ssh -i /home/nyanpasu/.ssh/platform_vm.pem ubuntu@ec2-13-38-156-22.eu-west-3.compute.amazonaws.com
```

#### 2. Stop Previous Bot Process
```bash
# Kill any running discord bot processes
pkill -f discord_meme_bot.py

# Terminate existing screen sessions
screen -S discord-bot -X quit
```

#### 3. Clean Previous System-Wide Packages (if installed)
```bash
# Remove system-wide packages to ensure clean virtual environment
pip uninstall discord.py python-dotenv gradio_client [other-packages] -y --break-system-packages
```

#### 4. Set Up Fresh Virtual Environment
```bash
cd discord_meme_bot

# Remove old virtual environment
rm -rf .venv

# Create new virtual environment
python3 -m venv .venv

# Activate and install dependencies
source .venv/bin/activate
pip install discord.py python-dotenv gradio_client
```

#### 5. Test Bot Configuration
```bash
# Test bot startup (should connect to Discord Gateway)
cd discord_meme_bot
source .venv/bin/activate
timeout 5 python discord_meme_bot.py
# Should show: "discord.gateway: Shard ID None has connected to Gateway"
```

#### 6. Start Bot in Screen Session
```bash
# Start bot in detached screen session
cd discord_meme_bot
screen -dmS discord-bot bash -c 'source .venv/bin/activate && python discord_meme_bot.py'
```

#### 7. Verify Deployment
```bash
# Check screen sessions
screen -list
# Should show: discord-bot (Detached)

# Check running processes
ps aux | grep discord
# Should show python discord_meme_bot.py process

# Check logs (attach to screen session)
screen -r discord-bot
# Use Ctrl+A then D to detach
```

## Environment Variables Required

### `.env` file content:
```env
DISCORD_TOKEN=your_discord_bot_token_here
HF_TOKEN=optional_huggingface_token
```

## Dependencies

### Core Dependencies
- `discord.py` - Discord bot framework
- `python-dotenv` - Environment variable management
- `gradio_client` - Gradio API client for meme recommendations

### Additional Dependencies (auto-installed)
- `aiohttp` - Async HTTP client
- `httpx` - HTTP client for Gradio
- `websockets` - WebSocket support
- `huggingface-hub` - HF Hub integration
- And various sub-dependencies

## Bot Commands

### Available Commands
- `!meme [text]` - Get a relevant meme based on text or recent conversation
- `!ping` - Check bot responsiveness and latency

### Usage Examples
```
!meme funny cats
!meme
!ping
```

## Management Commands

### Screen Session Management
```bash
# List all screen sessions
screen -list

# Attach to bot session
screen -r discord-bot

# Detach from session (while attached)
Ctrl+A then D

# Kill screen session
screen -S discord-bot -X quit
```

### Bot Process Management
```bash
# Check if bot is running
ps aux | grep discord

# Kill bot process
pkill -f discord_meme_bot.py

# Restart bot
cd discord_meme_bot
screen -dmS discord-bot bash -c 'source .venv/bin/activate && python discord_meme_bot.py'
```

### Log Monitoring
```bash
# View real-time logs
screen -r discord-bot

# Check recent output (if needed)
# Logs are displayed in the screen session
```

## Troubleshooting

### Common Issues

#### 1. Bot Not Connecting
- Check Discord token in `.env` file
- Verify bot permissions in Discord Developer Portal
- Check network connectivity

#### 2. Gradio API Errors
- Verify Gradio endpoint is accessible: `atlasia/moul_lmemes`
- Check API endpoint path: `/query_memes`
- Review error logs in screen session

#### 3. Virtual Environment Issues
- Recreate virtual environment: `rm -rf .venv && python3 -m venv .venv`
- Reinstall dependencies
- Ensure proper activation before running

#### 4. Screen Session Problems
- List sessions: `screen -list`
- Kill zombie sessions: `screen -wipe`
- Restart with new session name if needed

### Debug Commands
```bash
# Test Gradio client manually
cd discord_meme_bot
source .venv/bin/activate
python3 -c "
from gradiomeme_agent_api import GradioMemeAgent
agent = GradioMemeAgent()
result = agent.find_relevant_meme('test')
print(result)
"

# Test Discord connection
timeout 10 python discord_meme_bot.py
```

## Update Deployment

### To update the bot code:
```bash
# 1. SSH to server
ssh -i /home/nyanpasu/.ssh/platform_vm.pem ubuntu@ec2-13-38-156-22.eu-west-3.compute.amazonaws.com

# 2. Stop current bot
pkill -f discord_meme_bot.py
screen -S discord-bot -X quit

# 3. Update code (git pull or rsync)
cd discord_meme_bot
git pull  # or rsync from local

# 4. Update dependencies if needed
source .venv/bin/activate
pip install -r requirements.txt  # or any new dependencies

# 5. Restart bot
screen -dmS discord-bot bash -c 'source .venv/bin/activate && python discord_meme_bot.py'
```

## Security Notes

- Discord token should be kept secure and not committed to version control
- SSH keys should have proper permissions (600)
- Virtual environment isolates dependencies from system Python
- Bot runs with limited user privileges (ubuntu user)

## Performance Monitoring

- Bot memory usage: typically 60-80MB
- CPU usage: minimal when idle, spikes during meme requests
- Network: dependent on Discord API and Gradio API calls
- Monitor screen session for any error messages

---

**Last Updated**: July 2, 2025  
**Deployment Status**: ✅ Active  
**Screen Session**: `discord-bot`  
**Process ID**: Check with `ps aux | grep discord` 