# 🎬 Twitch Timestamp Bot (Protocol Bot)

A standalone Twitch bot for streamers and video editors that captures precise timestamps of interesting moments (highlights, fails, funny scenes) during live broadcasts.

---

## ⚡ How It Works

1. During a live stream, the streamer or any channel moderator enters:
   ```text
   !time
   ```
   or with a note:
   ```text
   !time epic 1v4 clutch
   ```
2. The bot captures the moment and replies in chat mentioning the user with the stream uptime:
   - Responds in chat with the user mention and stream uptime (e.g., `@moderator 01:24:35`).
   - Calculates **stream uptime** (`01:24:35`) — exact timestamp matching the VOD/recording timeline.
   - Captures **local real-world time** (`19:54:35`).
   - Records the user who saved the timestamp (`@moderator`).
   - Adds the note (if provided).
3. The entry is automatically saved to a dedicated Markdown file in the `timestamps/` folder:
   ```markdown
   - **[01:24:35]** (19:54:35) @moderator: epic 1v4 clutch
   ```
4. After the stream, video editors open the generated file and have all timestamps ready for editing!

---

## 🛠️ Installation and Setup

### 1. Requirements
Ensure **Python 3.10+** is installed on your system.

### 2. Create Virtual Environment and Install Dependencies
In your terminal, navigate to the project directory and run:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment:
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 🔑 Obtaining Twitch Tokens

The bot requires access to the chat and Twitch API:

1. **Quickest Method (Recommended)**:
   - Visit [twitchtokengenerator.com](https://twitchtokengenerator.com/) logged in as the bot account (or streamer account).
   - Select the following scopes:
     - `chat:read` (read channel chat)
     - `chat:edit` (send chat messages, if needed)
     - `moderator:manage:chat_messages` (if you want the bot to delete `!time` messages)
   - Click **Generate Token**.
   - Copy the generated **Access Token** and **Client ID**.

2. **Via Twitch Developer Console**:
   - Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps).
   - Create a new application with OAuth Redirect URL: `http://localhost:3000`.
   - Copy the **Client ID** and generate a **Client Secret**.

---

## ⚙️ Configuring `.env`

Create a `.env` file in the project root directory (based on `.env.example`):

```env
# Twitch OAuth token (with or without 'oauth:' prefix)
TWITCH_TOKEN=oauth:your_oauth_token_here

# Twitch Application Client ID (auto-discovered if left blank)
TWITCH_CLIENT_ID=your_client_id_here

# Channel name where the stream is hosted (lowercase, no @)
TWITCH_CHANNEL=your_channel_name

# Command prefix (default: !)
BOT_PREFIX=!

# Delete the !time command message from chat (true / false)
# Note: Requires the bot to have moderator permissions
DELETE_COMMAND_MESSAGE=false

# Directory where timestamp files will be stored
OUTPUT_DIR=timestamps
```

---

## 🚀 Running the Bot

### Normal Execution:
```bash
python bot.py
```
*(or `.\venv\Scripts\python bot.py`)*

### Quick Start on Windows:
Double-click `run_bot.bat` in the project root directory.

---

## 📁 Saved File Format

For each stream, a dedicated file is created in `timestamps/`, named by the broadcast start date and time, e.g. `timestamps/stream_2026-11-24_18-30.md`:

```markdown
# 🎬 Stream Timestamps: 2026-11-24 18:30
- **Channel**: channel_name
- **Stream Started**: 2026-11-24 18:30:15 (local time)

---

- **[00:12:05]** (18:42:20) @streamer: game start
- **[01:15:40]** (19:45:55) @moderator_1: funny fail
- **[02:04:18]** (20:34:33) @moderator_2: tournament victory
```

---

## 🛡️ Security & Behavior
- Never commit your `.env` file to a public Git repository (`.gitignore` excludes it by default).
- If the stream is offline, the bot silently ignores `!time` commands.
- Only the **Broadcaster** and channel **Moderators** are authorized to trigger `!time`.
