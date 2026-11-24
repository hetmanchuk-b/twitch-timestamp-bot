"""
Discord Webhook notification module.
Sends rich embed messages for recorded timestamps and end-of-stream summaries.
"""

from typing import Optional
import aiohttp
from datetime import datetime, timezone
import config
from config import logger


async def send_timestamp_embed(
    uptime_str: str,
    real_time_str: str,
    author_name: str,
    comment: str,
    channel_name: str
) -> bool:
    """
    Sends a rich Discord embed when a new timestamp is recorded during a stream.
    """
    webhook_url = config.DISCORD_WEBHOOK_URL
    if not webhook_url:
        return False

    clean_comment = comment.strip() if comment else "(No description provided)"

    payload = {
        "embeds": [
            {
                "title": "🎬 Highlight Timestamp Recorded",
                "color": 0x9146FF,  # Twitch Purple
                "fields": [
                    {
                        "name": "⏱️ Stream Uptime",
                        "value": f"`{uptime_str}`",
                        "inline": True
                    },
                    {
                        "name": "🕒 Real Time",
                        "value": f"`{real_time_str}`",
                        "inline": True
                    },
                    {
                        "name": "👤 Moderator",
                        "value": f"@{author_name}",
                        "inline": True
                    },
                    {
                        "name": "📝 Note",
                        "value": clean_comment,
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"Twitch Channel: #{channel_name}"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status in (200, 204):
                    logger.debug("Discord timestamp embed delivered successfully.")
                    return True
                else:
                    text = await resp.text()
                    logger.warning(f"⚠️ Discord Webhook returned status {resp.status}: {text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Failed to deliver Discord webhook notification: {e}")
        return False


async def send_stream_ended_summary(
    channel_name: str,
    total_timestamps: int,
    stream_duration_str: str,
    filename: str
) -> bool:
    """
    Sends an end-of-stream summary embed to Discord with links to the public page.
    """
    webhook_url = config.DISCORD_WEBHOOK_URL
    if not webhook_url:
        return False

    base_url = config.PUBLIC_BASE_URL.rstrip("/")
    view_url = f"{base_url}/stream/{filename}"
    download_url = f"{base_url}/download/{filename}"
    list_url = f"{base_url}/"

    payload = {
        "embeds": [
            {
                "title": "🏁 Stream Ended — Timestamps Ready!",
                "description": (
                    f"The broadcast on **#{channel_name}** has finished. "
                    "The highlight timestamps have been saved and are ready for editing."
                ),
                "color": 0x00FF7F,  # Spring Green / Success
                "fields": [
                    {
                        "name": "📊 Total Moments Recorded",
                        "value": f"**{total_timestamps}**",
                        "inline": True
                    },
                    {
                        "name": "⏱️ Broadcast Duration",
                        "value": f"`{stream_duration_str}`",
                        "inline": True
                    },
                    {
                        "name": "📄 Output File",
                        "value": f"`{filename}`",
                        "inline": False
                    },
                    {
                        "name": "🔗 Quick Links",
                        "value": (
                            f"🌐 [**View Timestamps Online**]({view_url})\n"
                            f"📥 [**Download .md File**]({download_url})\n"
                            f"📁 [**Browse All Streams**]({list_url})"
                        ),
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"Twitch Timestamp Bot • #{channel_name}"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status in (200, 204):
                    logger.info(f"📢 Discord end-of-stream summary posted for {filename} ({total_timestamps} moments).")
                    return True
                else:
                    text = await resp.text()
                    logger.warning(f"⚠️ Discord Webhook returned status {resp.status}: {text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Failed to deliver Discord end-of-stream summary: {e}")
        return False
