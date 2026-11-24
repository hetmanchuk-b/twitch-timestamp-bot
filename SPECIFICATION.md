# Project Specification: Twitch Timestamp Bot (Protocol Bot)

## 1. Overview

**Twitch Timestamp Bot** is a standalone Python-based Twitch bot designed to help streamers and video editors capture precise timestamps during live broadcasts for subsequent video production (clips, YouTube Shorts, Instagram Reels, TikToks, and full stream highlights).

Moderators and the broadcaster can trigger the `!time` command in chat (with an optional note). The bot calculates the current stream uptime relative to the broadcast start time and appends it to a structured Markdown file without spamming the public chat.

---

## 2. Key Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| **FR-1** | **`!time` Command** | The bot listens for the `!time` command in the chat of the target Twitch channel. |
| **FR-2** | **Optional Comment** | The command accepts an optional description or note after the command (e.g., `!time funny game bug`). |
| **FR-3** | **Access Control** | Only the **Broadcaster** and **Channel Moderators** are authorized to trigger the command. Messages from regular viewers are ignored. |
| **FR-4** | **Uptime Calculation** | The bot retrieves the stream start time (`started_at`) via the Twitch Helix API and computes the elapsed time in `HH:MM:SS` format, matching the VOD timeline. |
| **FR-5** | **Real-World Timestamp** | Alongside the stream uptime, the local real-world time of the command execution is recorded (`HH:MM:SS`). |
| **FR-6** | **Ignore Offline Commands** | If the stream is not live (channel is offline), the `!time` command is silently ignored and no entry is logged. |
| **FR-7** | **Chat Response** | Upon recording a timestamp, the bot sends only the current stream uptime (e.g., `01:24:35`) to chat. |
| **FR-8** | **Auto-Delete Command** | Option to automatically delete the `!time` command message from chat if the bot has moderator permissions. |
| **FR-9** | **Per-Stream File Output** | Each broadcast generates its own separate file in the `timestamps/` directory formatted as `stream_YYYY-MM-DD_HH-MM.md`. |

---

## 3. Data Storage Format

### 3.1. File Structure (`stream_YYYY-MM-DD_HH-MM.md`)
Files are stored in Markdown format:

```markdown
# 🎬 Stream Timestamps: YYYY-MM-DD HH:MM
- **Channel**: channel_name
- **Stream Started**: 2026-11-24 18:30:00 (local time)

---

- **[00:15:24]** (18:45:24) @moderator_alex: match start
- **[01:24:35]** (19:54:35) @streamer: 1v4 clutch
- **[02:10:05]** (20:40:05) @mod_olena: funny fail
```

### 3.2. Record Fields
1. **`[HH:MM:SS]`** — Stream uptime (convenient for seeking directly on video editor timelines like Premiere Pro / DaVinci Resolve).
2. **`(HH:MM:SS)`** — Real-world local time when the command was triggered.
3. **`@username`** — Username of the moderator or streamer who triggered the timestamp.
4. **`Note`** — Optional comment or description (if provided).

---

## 4. Architecture and Tech Stack

```
                    ┌─────────────────────────┐
                    │   Twitch Chat (IRC)     │
                    │   Moderator: !time      │
                    └───────────┬─────────────┘
                                │ WebSockets
                                ▼
                    ┌─────────────────────────┐
                    │     TwitchIO Bot        │
                    │   (Python Application)  │
                    └───────┬───────────┬─────┘
                            │           │
       Stream Check         │           │ Write timestamp
       Helix API (uptime)   │           │ to file
                            ▼           ▼
             ┌──────────────────┐   ┌───────────────────────────────┐
             │ Twitch Helix API │   │  timestamps/stream_*.md       │
             └──────────────────┘   └───────────────────────────────┘
```

- **Language**: Python 3.10+
- **Core Library**: `twitchio` (Twitch IRC and Helix API communication)
- **Configuration**: `python-dotenv` for loading environment variables from `.env`
- **File System**: `pathlib` for cross-platform directory and path handling.

---

## 5. Configuration Variables (`.env`)

| Variable | Purpose | Example |
|---|---|---|
| `TWITCH_TOKEN` | Bot User OAuth token (with or without `oauth:` prefix) | `oauth:abc123xyz...` |
| `TWITCH_CLIENT_ID` | Client ID of the registered Twitch Application | `gp762nu...` |
| `TWITCH_CHANNEL` | Twitch channel name where the broadcast takes place | `my_stream_channel` |
| `BOT_PREFIX` | Command prefix (defaults to `!`) | `!` |
| `DELETE_COMMAND_MESSAGE` | Whether to delete `!time` messages from chat (`true` / `false`) | `false` |
| `OUTPUT_DIR` | Directory to save timestamp files | `timestamps` |

---

## 6. Error Handling and Edge Cases

1. **Stream Offline**: The bot verifies live status via Helix API. If the stream is not active or `started_at` is absent, the command is silently ignored.
2. **Chat Reconnection**: `twitchio` automatically manages WebSocket reconnections in the event of transient network issues.
3. **Stream Restart**: If a broadcast restarts, a new `started_at` timestamp is detected and tracked in an appropriate file.
4. **Concurrent Appends**: Timestamp additions use append mode (`a`), guaranteeing atomic row persistence.
