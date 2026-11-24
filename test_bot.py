"""
Unit tests for Twitch Timestamp Bot.
Verifies duration formatting, file creation, header structure,
session counters, and web server endpoints.
"""

import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import shutil
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from storage import format_duration, StreamStorage
import web
import config


class TestStorageAndLogic(unittest.TestCase):
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

    def test_session_tracking_and_reset(self):
        """Test tracking session counters and resetting when stream ends."""
        import storage
        old_output_dir = storage.OUTPUT_DIR
        try:
            storage.OUTPUT_DIR = self.test_dir
            stream_storage = StreamStorage("test_channel")

            stream_start = datetime(2026, 11, 24, 18, 0, 0, tzinfo=timezone.utc)
            t1 = stream_start + timedelta(minutes=5)
            t2 = stream_start + timedelta(minutes=15)

            stream_storage.record_timestamp(stream_start, t1, "mod", "note 1")
            stream_storage.record_timestamp(stream_start, t2, "mod", "note 2")

            self.assertEqual(stream_storage.session_timestamps_count, 2)
            self.assertIsNotNone(stream_storage.session_file_name)

            stream_storage.reset_session()
            self.assertEqual(stream_storage.session_timestamps_count, 0)
            self.assertIsNone(stream_storage.session_file_name)
        finally:
            storage.OUTPUT_DIR = old_output_dir


class TestWebServer(AioHTTPTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.old_dir = config.OUTPUT_DIR
        config.OUTPUT_DIR = self.test_dir

        # Create a sample stream file
        self.sample_file = self.test_dir / "stream_2026-11-24_18-00.md"
        self.sample_file.write_text(
            "# 🎬 Stream Timestamps: 2026-11-24 18:00\n- **[00:05:00]** (18:05:00) @mod: test\n",
            encoding="utf-8"
        )

        super().setUp()

    def tearDown(self):
        super().tearDown()
        config.OUTPUT_DIR = self.old_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def get_application(self):
        return web.create_web_app()

    @unittest_run_loop
    async def test_healthz_endpoint(self):
        """Test /healthz endpoint returns 200 OK."""
        resp = await self.client.request("GET", "/healthz")
        self.assertEqual(resp.status, 200)
        text = await resp.text()
        self.assertEqual(text, "OK")

    @unittest_run_loop
    async def test_index_page(self):
        """Test / renders list with the recorded stream."""
        resp = await self.client.request("GET", "/")
        self.assertEqual(resp.status, 200)
        text = await resp.text()
        self.assertIn("Twitch Timestamps", text)
        self.assertIn("stream_2026-11-24_18-00.md", text)

    @unittest_run_loop
    async def test_view_stream_page(self):
        """Test /stream/{filename} displays the file content."""
        resp = await self.client.request("GET", "/stream/stream_2026-11-24_18-00.md")
        self.assertEqual(resp.status, 200)
        text = await resp.text()
        self.assertIn("- **[00:05:00]**", text)

    @unittest_run_loop
    async def test_download_stream(self):
        """Test /download/{filename} delivers the markdown file download."""
        resp = await self.client.request("GET", "/download/stream_2026-11-24_18-00.md")
        self.assertEqual(resp.status, 200)
        self.assertIn("attachment", resp.headers.get("Content-Disposition", ""))

    @unittest_run_loop
    async def test_api_time_auth(self):
        """Test /api/time authentication."""
        old_key = config.API_KEY
        try:
            config.API_KEY = "secret123"
            # Request without key should fail with 401
            resp = await self.client.request("POST", "/api/time")
            self.assertEqual(resp.status, 401)

            # Request with wrong key should fail with 401
            resp = await self.client.request("POST", "/api/time", headers={"X-API-Key": "wrong"})
            self.assertEqual(resp.status, 401)

            # Request with correct key should pass auth (returns 503 because dummy bot is not set in test app)
            resp = await self.client.request("POST", "/api/time", headers={"X-API-Key": "secret123"})
            self.assertIn(resp.status, (200, 503))
        finally:
            config.API_KEY = old_key


if __name__ == "__main__":
    unittest.main()
