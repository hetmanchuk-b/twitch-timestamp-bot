"""
Storage module for timestamp management.
Creates structured Markdown files for each distinct stream broadcast.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from config import OUTPUT_DIR, logger


def format_duration(seconds: float) -> str:
    """Formats a duration in seconds into HH:MM:SS format."""
    total_seconds = max(0, int(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class StreamStorage:
    """Manages recording timestamps for the current stream into a dedicated Markdown file."""

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.current_stream_started_at: Optional[datetime] = None
        self.current_file_path: Optional[Path] = None

    def get_or_create_file(self, stream_started_at: datetime) -> Path:
        """
        Returns the file path for the given stream start time.
        If the file does not exist, creates it and writes the header.
        """
        # Convert stream start time to local timezone
        if stream_started_at.tzinfo is None:
            utc_started = stream_started_at.replace(tzinfo=timezone.utc)
        else:
            utc_started = stream_started_at

        local_started = utc_started.astimezone()

        # Generate file name: stream_YYYY-MM-DD_HH-MM.md
        file_name = f"stream_{local_started.strftime('%Y-%m-%d_%H-%M')}.md"
        file_path = OUTPUT_DIR / file_name

        if not file_path.exists():
            header = (
                f"# 🎬 Stream Timestamps: {local_started.strftime('%Y-%m-%d %H:%M')}\n"
                f"- **Channel**: {self.channel_name}\n"
                f"- **Stream Started**: {local_started.strftime('%Y-%m-%d %H:%M:%S')} (local time)\n\n"
                f"---\n\n"
            )
            file_path.write_text(header, encoding="utf-8")
            logger.info(f"📁 Created new timestamp file: {file_path}")

        self.current_stream_started_at = stream_started_at
        self.current_file_path = file_path
        return file_path

    def record_timestamp(
        self,
        stream_started_at: datetime,
        recorded_at: datetime,
        author_name: str,
        comment: str = ""
    ) -> tuple[str, str, Path]:
        """
        Records a new timestamp entry into the stream file.

        Returns a tuple of (uptime_str, real_time_str, file_path).
        """
        file_path = self.get_or_create_file(stream_started_at)

        # Calculate stream uptime
        if stream_started_at.tzinfo is None:
            stream_started_utc = stream_started_at.replace(tzinfo=timezone.utc)
        else:
            stream_started_utc = stream_started_at

        if recorded_at.tzinfo is None:
            recorded_utc = recorded_at.replace(tzinfo=timezone.utc)
        else:
            recorded_utc = recorded_at

        uptime_seconds = (recorded_utc - stream_started_utc).total_seconds()
        uptime_str = format_duration(uptime_seconds)

        # Local real-world time of entry
        local_recorded = recorded_utc.astimezone()
        real_time_str = local_recorded.strftime("%H:%M:%S")

        # Format record line
        clean_comment = comment.strip()
        if clean_comment:
            entry_line = f"- **[{uptime_str}]** ({real_time_str}) @{author_name}: {clean_comment}\n"
        else:
            entry_line = f"- **[{uptime_str}]** ({real_time_str}) @{author_name}\n"

        # Append entry to the file
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(entry_line)

        return uptime_str, real_time_str, file_path
