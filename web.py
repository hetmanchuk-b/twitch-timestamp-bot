"""
Embedded Web Server for Twitch Timestamp Bot.
Provides an HTML interface to browse, view, and download stream timestamp files,
as well as a /healthz endpoint for keep-alive monitoring (Render / UptimeRobot).
"""

import html
from pathlib import Path
from aiohttp import web
from datetime import datetime
import config
from config import logger


def get_safe_file_path(filename: str) -> Path | None:
    """Sanitizes filename and checks if it exists in the OUTPUT_DIR."""
    safe_name = Path(filename).name
    if not safe_name.endswith(".md"):
        return None
    file_path = config.OUTPUT_DIR / safe_name
    if file_path.exists() and file_path.is_file():
        return file_path
    return None


async def handle_healthz(request: web.Request) -> web.Response:
    """Healthcheck endpoint for Render and uptime monitoring."""
    return web.Response(text="OK", status=200, content_type="text/plain")


async def handle_index(request: web.Request) -> web.Response:
    """Renders the main page listing all recorded stream timestamp files."""
    files = sorted(
        config.OUTPUT_DIR.glob("stream_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    items_html = []
    for file_path in files:
        name = file_path.name
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_kb = max(1, round(file_path.stat().st_size / 1024, 1))

        # Count total recorded timestamps in file
        try:
            content = file_path.read_text(encoding="utf-8")
            count = sum(1 for line in content.splitlines() if line.startswith("- **["))
        except Exception:
            count = 0

        items_html.append(f"""
        <div class="stream-card">
            <div class="stream-info">
                <div class="stream-name">🎬 {html.escape(name)}</div>
                <div class="stream-meta">
                    <span>🕒 Last Updated: {mtime}</span> • 
                    <span>📊 Moments: <strong>{count}</strong></span> • 
                    <span>💾 Size: {size_kb} KB</span>
                </div>
            </div>
            <div class="stream-actions">
                <a href="/stream/{html.escape(name)}" class="btn btn-view">👁️ View</a>
                <a href="/download/{html.escape(name)}" class="btn btn-download">📥 Download .md</a>
            </div>
        </div>
        """)

    content_list = "\n".join(items_html) if items_html else """
        <div class="empty-state">
            <p>No stream timestamps recorded yet.</p>
            <p class="empty-sub">Once a stream starts and moderators trigger <code>!time</code>, files will appear here automatically.</p>
        </div>
    """

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Twitch Timestamps — #{html.escape(config.TWITCH_CHANNEL)}</title>
    <style>
        :root {{
            --bg-dark: #0e0e10;
            --bg-card: #18181b;
            --bg-hover: #1f1f23;
            --primary: #9146ff;
            --primary-hover: #772ce8;
            --text-main: #efeff1;
            --text-muted: #adadb8;
            --border-color: #2e2e35;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            padding: 2rem 1rem;
        }}
        .container {{
            max-width: 860px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        h1 {{
            font-size: 1.6rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .badge {{
            background: var(--primary);
            color: white;
            font-size: 0.8rem;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-weight: bold;
        }}
        .stream-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            transition: border-color 0.2s, background-color 0.2s;
        }}
        .stream-card:hover {{
            background-color: var(--bg-hover);
            border-color: var(--primary);
        }}
        .stream-name {{
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 0.3rem;
            color: #ffffff;
        }}
        .stream-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        .stream-actions {{
            display: flex;
            gap: 0.6rem;
        }}
        .btn {{
            display: inline-block;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-view {{
            background-color: var(--bg-hover);
            color: var(--text-main);
            border: 1px solid var(--border-color);
        }}
        .btn-view:hover {{
            background-color: #27272c;
            border-color: #4b4b54;
        }}
        .btn-download {{
            background-color: var(--primary);
            color: white;
            border: 1px solid transparent;
        }}
        .btn-download:hover {{
            background-color: var(--primary-hover);
        }}
        .empty-state {{
            background: var(--bg-card);
            border: 1px dashed var(--border-color);
            padding: 3rem 1.5rem;
            border-radius: 8px;
            text-align: center;
            color: var(--text-muted);
        }}
        .empty-sub {{
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🎬 Twitch Timestamps <span class="badge">#{html.escape(config.TWITCH_CHANNEL)}</span></h1>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.3rem;">Video editing highlight moments saved automatically during live streams.</p>
            </div>
            <div>
                <span style="font-size: 0.85rem; color: #4ade80;">● Bot Active</span>
            </div>
        </header>

        <main>
            {content_list}
        </main>

        <footer>
            Twitch Timestamp Bot • Auto-refreshed from live broadcasts
        </footer>
    </div>
</body>
</html>
"""
    return web.Response(text=html_page, content_type="text/html")


async def handle_view_stream(request: web.Request) -> web.Response:
    """Renders a viewer page for a specific stream's markdown notes."""
    filename = request.match_info.get("filename", "")
    file_path = get_safe_file_path(filename)
    if not file_path:
        return web.Response(text="File not found", status=404)

    content = file_path.read_text(encoding="utf-8")

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(filename)} — Twitch Timestamps</title>
    <style>
        :root {{
            --bg-dark: #0e0e10;
            --bg-card: #18181b;
            --primary: #9146ff;
            --primary-hover: #772ce8;
            --text-main: #efeff1;
            --text-muted: #adadb8;
            --border-color: #2e2e35;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            padding: 2rem 1rem;
        }}
        .container {{
            max-width: 860px;
            margin: 0 auto;
        }}
        .nav-bar {{
            margin-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        a.back-link {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 600;
            font-size: 0.95rem;
        }}
        a.back-link:hover {{
            text-decoration: underline;
        }}
        .btn {{
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            border: none;
        }}
        .btn-download {{
            background-color: var(--primary);
            color: white;
        }}
        .btn-download:hover {{
            background-color: var(--primary-hover);
        }}
        .btn-copy {{
            background-color: #27272c;
            color: var(--text-main);
            border: 1px solid var(--border-color);
        }}
        .btn-copy:hover {{
            background-color: #333339;
        }}
        pre {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            color: #f1f1f1;
            font-family: "JetBrains Mono", Consolas, "Courier New", monospace;
            font-size: 0.95rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-bar">
            <a href="/" class="back-link">← Back to All Streams</a>
            <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-copy" onclick="copyText()">📋 Copy Content</button>
                <a href="/download/{html.escape(filename)}" class="btn btn-download">📥 Download .md</a>
            </div>
        </div>

        <pre id="content-block">{html.escape(content)}</pre>
    </div>

    <script>
        function copyText() {{
            const text = document.getElementById('content-block').innerText;
            navigator.clipboard.writeText(text).then(() => {{
                alert('Copied timestamps to clipboard!');
            }});
        }}
    </script>
</body>
</html>
"""
    return web.Response(text=html_page, content_type="text/html")


async def handle_download_stream(request: web.Request) -> web.Response:
    """Direct download of the specified stream markdown file."""
    filename = request.match_info.get("filename", "")
    file_path = get_safe_file_path(filename)
    if not file_path:
        return web.Response(text="File not found", status=404)

    return web.FileResponse(
        file_path,
        headers={
            "Content-Disposition": f'attachment; filename="{file_path.name}"'
        }
    )


def create_web_app() -> web.Application:
    """Creates the aiohttp web application with defined routes."""
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/healthz", handle_healthz)
    app.router.add_get("/stream/{filename}", handle_view_stream)
    app.router.add_get("/download/{filename}", handle_download_stream)
    return app


async def start_web_server(host: str, port: int) -> web.AppRunner:
    """Starts the embedded web server on the given host and port."""
    app = create_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"🌐 Embedded web server running at http://{host}:{port}")
    logger.info(f"🔗 Public Base URL configured as: {config.PUBLIC_BASE_URL}")
    return runner
