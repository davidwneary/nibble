"""Nibble Orchestrator — Screenshot capture via Playwright.

Captures screenshots of the web app after implementation for UI verification.
Used by the Implement stage when the issue has UI-related labels.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Labels that trigger screenshot capture
UI_LABELS = {"ui", "frontend", "web", "design"}

# Pages to screenshot (relative paths in the web app)
DEFAULT_PAGES = ["/"]

DEV_SERVER_START_TIMEOUT = 15  # seconds to wait for dev server


def should_capture_screenshots(labels: list[str]) -> bool:
    """Check if an issue's labels indicate UI work that needs screenshots."""
    return bool(set(l.lower() for l in labels) & UI_LABELS)


def capture_screenshots(
    workspace: Path,
    pages: Optional[list[str]] = None,
    port: int = 5173,
) -> list[Path]:
    """Capture screenshots of the web app running in the workspace.

    1. Starts the dev server (npm run dev)
    2. Waits for it to be ready
    3. Captures a screenshot of each specified page
    4. Kills the dev server
    5. Returns list of screenshot file paths

    Returns empty list if Playwright is not installed or capture fails.
    """
    if pages is None:
        pages = DEFAULT_PAGES

    web_dir = workspace / "web"
    if not web_dir.exists():
        logger.warning("No web/ directory found, skipping screenshots")
        return []

    # Check if playwright is available
    try:
        subprocess.run(
            ["python3", "-c", "import playwright"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Playwright not installed, skipping screenshots")
        return []

    screenshots: list[Path] = []
    dev_server = None

    try:
        # Start dev server
        dev_server = subprocess.Popen(
            ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", str(port)],
            cwd=web_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to be ready
        if not _wait_for_server(port):
            logger.warning("Dev server failed to start, skipping screenshots")
            return []

        # Capture screenshots using playwright
        for page_path in pages:
            url = f"http://localhost:{port}{page_path}"
            screenshot_path = workspace / f"screenshot_{page_path.strip('/') or 'home'}.png"

            success = _take_screenshot(url, screenshot_path)
            if success:
                screenshots.append(screenshot_path)
                logger.info(f"Captured screenshot: {screenshot_path}")

    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
    finally:
        if dev_server:
            dev_server.terminate()
            dev_server.wait(timeout=5)

    return screenshots


def _wait_for_server(port: int, timeout: int = DEV_SERVER_START_TIMEOUT) -> bool:
    """Wait for the dev server to be responsive."""
    import socket

    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False


def _take_screenshot(url: str, output_path: Path) -> bool:
    """Take a screenshot using Playwright's CLI."""
    try:
        # Use playwright's Python API via a subprocess script
        script = f"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={{'width': 1280, 'height': 720}})
        await page.goto('{url}', wait_until='networkidle')
        await page.screenshot(path='{output_path}')
        await browser.close()

asyncio.run(main())
"""
        result = subprocess.run(
            ["python3", "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to take screenshot of {url}: {e}")
        return False
