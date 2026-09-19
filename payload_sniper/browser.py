"""
Browser discovery and Chrome DevTools Protocol (CDP) controller for PayloadSniper.
"""

import asyncio
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from typing import Dict, Any, Optional, List
import websockets

CANDIDATE_BROWSER_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "brave-browser",
]


def find_browser_executable() -> Optional[str]:
    """Find local Chromium-based browser executable."""
    for path in CANDIDATE_BROWSER_PATHS:
        if os.path.isabs(path):
            if os.path.exists(path) and os.path.isfile(path):
                return path
        else:
            resolved = shutil.which(path)
            if resolved:
                return resolved
    return None


def find_free_port(start_port: int = 9650) -> int:
    """Find unbound local port for Chrome remote debugging."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


class CDPClient:
    """Lightweight Chrome DevTools Protocol WebSocket client."""

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self._msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=25 * 1024 * 1024)

    async def send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(msg))

        while True:
            raw = await self.ws.recv()
            resp = json.loads(raw)
            if resp.get("id") == self._msg_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP error on {method}: {resp['error']}")
                return resp.get("result", {})

    async def close(self):
        if self.ws:
            await self.ws.close()


class ChromeRunner:
    """Manages headless Chromium process for performance profiling."""

    def __init__(self, browser_path: Optional[str] = None):
        self.browser_path = browser_path or find_browser_executable()
        self.proc: Optional[subprocess.Popen] = None
        self.port: Optional[int] = None
        self.user_data_dir: Optional[str] = None

    def start(self, port: Optional[int] = None):
        if not self.browser_path:
            raise RuntimeError("No Chromium browser executable found on system.")

        self.port = port or find_free_port()
        self.user_data_dir = os.path.join(
            os.environ.get("TEMP", "/tmp"), f"payloadsniper_chrome_{self.port}_{int(time.time())}"
        )
        os.makedirs(self.user_data_dir, exist_ok=True)

        cmd = [
            self.browser_path,
            "--headless=new",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-translate",
            "--hide-scrollbars",
            "--disable-gpu",
            "about:blank",
        ]

        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        for _ in range(40):
            time.sleep(0.1)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version", timeout=1) as resp:
                    if resp.status == 200:
                        return
            except Exception:
                continue

        self.stop()
        raise TimeoutError("Timed out waiting for Chromium remote debugging endpoint to become ready.")

    def get_tab_ws_url(self) -> str:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list", timeout=2) as resp:
            tabs = json.loads(resp.read().decode())
            for t in tabs:
                if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                    return t["webSocketDebuggerUrl"]
        raise RuntimeError("No open tab found in Chromium process.")

    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None

        if self.user_data_dir and os.path.exists(self.user_data_dir):
            try:
                shutil.rmtree(self.user_data_dir, ignore_errors=True)
            except Exception:
                pass
