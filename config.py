"""
Configuration module for Twitch Timestamp Bot.
Loads and validates environment variables from the .env file.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current base directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # If .env is missing, attempt to load any available environment variables
    load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ProtocolBot")

# Core Twitch configuration
raw_token = os.getenv("TWITCH_TOKEN", "").strip()
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "").strip()
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "").strip().lower().lstrip("@")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!").strip() or "!"
DELETE_COMMAND_MESSAGE = os.getenv("DELETE_COMMAND_MESSAGE", "false").strip().lower() in ("true", "1", "yes")
OUTPUT_DIR_NAME = os.getenv("OUTPUT_DIR", "timestamps").strip() or "timestamps"
OUTPUT_DIR = BASE_DIR / OUTPUT_DIR_NAME

# Web server & Render hosting configuration
HOST = os.getenv("HOST", "0.0.0.0").strip()
PORT = int(os.getenv("PORT", "8080").strip())
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
if not PUBLIC_BASE_URL:
    PUBLIC_BASE_URL = f"http://localhost:{PORT}"

# Discord Webhook integration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

# Background stream status check interval (seconds)
STREAM_CHECK_INTERVAL = int(os.getenv("STREAM_CHECK_INTERVAL", "60").strip())

# Token formatting
if raw_token.startswith("oauth:"):
    TWITCH_TOKEN = raw_token
    RAW_ACCESS_TOKEN = raw_token.replace("oauth:", "")
else:
    TWITCH_TOKEN = f"oauth:{raw_token}" if raw_token else ""
    RAW_ACCESS_TOKEN = raw_token

# Create timestamps directory if it does not exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def validate_config() -> bool:
    """Validates required configuration parameters."""
    errors = []
    if not RAW_ACCESS_TOKEN or RAW_ACCESS_TOKEN == "your_oauth_token_here":
        errors.append("TWITCH_TOKEN is not set or contains the default placeholder!")
    if not TWITCH_CHANNEL or TWITCH_CHANNEL == "your_channel_name":
        errors.append("TWITCH_CHANNEL is not set or contains the default placeholder!")

    if errors:
        logger.error("❌ Configuration error in .env file:")
        for err in errors:
            logger.error(f"   - {err}")
        logger.error("Please configure the .env file according to .env.example and README.md.")
        return False
    return True
