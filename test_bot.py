"""
Unit tests for Twitch Timestamp Bot.
Verifies duration formatting, file creation, header structure, and timestamp recording.
"""

import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import shutil

from storage import format_duration, StreamStorage


class TestTimestampBot(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test file generation
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        # Clean up temporary test files
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_format_duration(self):
        """Test formatting seconds into HH:MM:SS."""
        self.assertEqual(format_duration(0), "00:00:00")
        self.assertEqual(format_duration(59), "00:00:59")
        self.assertEqual(format_duration(60), "00:01:00")
        self.assertEqual(format_duration(3600), "01:00:00")
        self.assertEqual(format_duration(3665), "01:01:05")
        self.assertEqual(format_duration(5075), "01:24:35")
        self.assertEqual(format_duration(86400), "24:00:00")
        self.assertEqual(format_duration(90061), "25:01:01")

    def test_record_timestamp_with_comment(self):
        """Test file creation and timestamp recording with a comment."""
        import storage
        old_output_dir = storage.OUTPUT_DIR
        try:
            storage.OUTPUT_DIR = self.test_dir
            stream_storage = StreamStorage("test_channel")

            stream_start = datetime(2026, 11, 24, 18, 0, 0, tzinfo=timezone.utc)
            record_time = stream_start + timedelta(hours=1, minutes=24, seconds=35)

            uptime_str, real_time_str, file_path = stream_storage.record_timestamp(
                stream_started_at=stream_start,
                recorded_at=record_time,
                author_name="moderator_alex",
                comment="epic moment"
            )

            self.assertEqual(uptime_str, "01:24:35")
            self.assertTrue(file_path.exists())

            content = file_path.read_text(encoding="utf-8")
            self.assertIn("# 🎬 Stream Timestamps:", content)
            self.assertIn("- **Channel**: test_channel", content)
            self.assertIn("- **[01:24:35]**", content)
            self.assertIn("@moderator_alex: epic moment", content)
        finally:
            storage.OUTPUT_DIR = old_output_dir

    def test_record_timestamp_without_comment(self):
        """Test timestamp recording without a comment."""
        import storage
        old_output_dir = storage.OUTPUT_DIR
        try:
            storage.OUTPUT_DIR = self.test_dir
            stream_storage = StreamStorage("test_channel")

            stream_start = datetime(2026, 11, 24, 18, 0, 0, tzinfo=timezone.utc)
            record_time = stream_start + timedelta(minutes=15, seconds=2)

            uptime_str, real_time_str, file_path = stream_storage.record_timestamp(
                stream_started_at=stream_start,
                recorded_at=record_time,
                author_name="streamer",
                comment=""
            )

            self.assertEqual(uptime_str, "00:15:02")
            content = file_path.read_text(encoding="utf-8")
            self.assertIn("- **[00:15:02]**", content)
            self.assertIn("@streamer\n", content)
        finally:
            storage.OUTPUT_DIR = old_output_dir

    def test_multiple_records_in_same_file(self):
        """Test consecutive timestamp records within a single stream broadcast."""
        import storage
        old_output_dir = storage.OUTPUT_DIR
        try:
            storage.OUTPUT_DIR = self.test_dir
            stream_storage = StreamStorage("test_channel")

            stream_start = datetime(2026, 11, 24, 18, 0, 0, tzinfo=timezone.utc)
            t1 = stream_start + timedelta(minutes=10)
            t2 = stream_start + timedelta(minutes=45)

            _, _, path1 = stream_storage.record_timestamp(stream_start, t1, "mod1", "first clip")
            _, _, path2 = stream_storage.record_timestamp(stream_start, t2, "mod2", "second clip")

            self.assertEqual(path1, path2)
            content = path1.read_text(encoding="utf-8")
            self.assertIn("- **[00:10:00]**", content)
            self.assertIn("- **[00:45:00]**", content)
            # Header should only be written once
            self.assertEqual(content.count("# 🎬 Stream Timestamps:"), 1)
        finally:
            storage.OUTPUT_DIR = old_output_dir


if __name__ == "__main__":
    unittest.main()
