"""
Twitch Timestamp Bot (Protocol Bot)
Main module for starting the bot and processing chat commands.
"""

import sys
import asyncio
from datetime import datetime, timezone
from typing import Optional

# Ensure an active asyncio event loop for Python 3.12+ / 3.14+
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import config
from config import logger
from storage import StreamStorage
from twitchio.ext import commands
from twitchio import errors


class ProtocolBot(commands.Bot):
    """Bot for capturing and storing live stream timestamps."""

    def __init__(self):
        super().__init__(
            token=config.TWITCH_TOKEN,
            prefix=config.BOT_PREFIX,
            initial_channels=[config.TWITCH_CHANNEL]
        )
        self.channel_name = config.TWITCH_CHANNEL
        self.storage = StreamStorage(self.channel_name)
        self.bot_user_id: Optional[str] = None
        self.broadcaster_user_id: Optional[str] = None

    async def event_ready(self):
        """Triggered upon successful connection to Twitch IRC and joined channel."""
        logger.info("=" * 60)
        logger.info("🚀 Twitch Timestamp Bot successfully connected!")
        logger.info(f"   • Bot Account: @{self.nick}")
        logger.info(f"   • Target Channel: #{self.channel_name}")
        logger.info(f"   • Command: {config.BOT_PREFIX}time [comment]")
        logger.info(f"   • Auto-delete commands: {'Enabled' if config.DELETE_COMMAND_MESSAGE else 'Disabled'}")
        logger.info(f"   • Timestamps Directory: {config.OUTPUT_DIR}")
        logger.info("=" * 60)

        # Token validation and user ID retrieval
        try:
            val_data = await self._http.validate()
            self.bot_user_id = str(val_data.get("user_id") or "")
            if config.TWITCH_CLIENT_ID:
                self._http.client_id = config.TWITCH_CLIENT_ID
            logger.info(f"🔑 Token validated (Client ID: {self._http.client_id or val_data.get('client_id')})")
        except Exception as e:
            logger.warning(f"⚠️ Could not validate token details via validate(): {e}")

        # Fetch broadcaster user ID for API calls (e.g. message deletion)
        try:
            users = await self.fetch_users(names=[self.channel_name])
            if users:
                self.broadcaster_user_id = str(users[0].id)
                logger.info(f"📺 Channel found (Broadcaster ID: {self.broadcaster_user_id})")
        except Exception as e:
            logger.debug(f"Could not retrieve channel user information: {e}")

    async def event_message(self, message):
        """Handles incoming chat messages."""
        # Ignore messages sent by the bot itself
        if message.echo:
            return

        # Forward message to registered command handlers
        await self.handle_commands(message)

    @commands.command(name="time")
    async def time_command(self, ctx: commands.Context, *, comment: str = ""):
        """
        !time command to record stream timestamp.
        Restricted to broadcaster and channel moderators.
        """
        # Permission check: broadcaster or channel moderator
        is_allowed = ctx.author.is_mod or ctx.author.is_broadcaster
        if not is_allowed:
            # Silently ignore regular viewers
            return

        # Query live stream status via Twitch Helix API
        try:
            streams = await self.fetch_streams(user_logins=[self.channel_name])
        except Exception as e:
            logger.error(f"❌ Error querying stream status via Twitch API: {e}")
            return

        # If stream is offline, silently ignore per specification
        if not streams:
            logger.info(f"⏸️ [OFFLINE] Command !time from @{ctx.author.name} ignored (channel offline)")
            return

        stream = streams[0]
        started_at = stream.started_at
        now_utc = datetime.now(timezone.utc)

        # Save timestamp to Markdown file
        try:
            uptime_str, real_time_str, file_path = self.storage.record_timestamp(
                stream_started_at=started_at,
                recorded_at=now_utc,
                author_name=ctx.author.name,
                comment=comment
            )
            note_text = f": {comment.strip()}" if comment.strip() else ""
            logger.info(f"⏱️ [RECORDED] [{uptime_str}] ({real_time_str}) @{ctx.author.name}{note_text}")
        except Exception as e:
            logger.error(f"❌ Error writing timestamp to file: {e}")
            return

        # Send only the stream uptime to chat
        try:
            await ctx.send(uptime_str)
        except Exception as e:
            logger.error(f"❌ Error sending uptime to chat: {e}")

        # If auto-delete is enabled, attempt to delete the command message
        if config.DELETE_COMMAND_MESSAGE:
            await self._try_delete_message(ctx)

    async def _try_delete_message(self, ctx: commands.Context):
        """Attempts to delete the command message from chat."""
        if not ctx.message or not ctx.message.id:
            return

        if not self.broadcaster_user_id or not self.bot_user_id:
            return

        try:
            await self._http.delete_chat_messages(
                token=self._http.token,
                broadcaster_id=self.broadcaster_user_id,
                moderator_id=self.bot_user_id,
                message_id=ctx.message.id
            )
            logger.debug(f"Command message {ctx.message.id} deleted from chat.")
        except Exception as e:
            logger.debug(f"Could not delete message from chat (bot might lack moderator permissions): {e}")

    async def event_command_error(self, ctx: commands.Context, error: Exception):
        """Command error handler."""
        # Silently ignore calls to unknown commands
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"⚠️ Command execution error: {error}")


def main():
    """Entry point for running the bot."""
    print("=" * 60)
    print("        Twitch Timestamp Bot (Protocol Bot)        ")
    print("=" * 60)

    if not config.validate_config():
        sys.exit(1)

    bot = ProtocolBot()
    try:
        bot.run()
    except errors.AuthenticationError:
        logger.error("❌ Authentication Error: Invalid or expired TWITCH_TOKEN.")
        logger.error("Please update your token in the .env file (see README.md for instructions).")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"❌ Fatal error while running the bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
