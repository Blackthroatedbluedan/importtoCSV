#!/usr/bin/env python3
"""
Record a short demo of the web UI (Playwright + uvicorn subprocess).
Outputs WebM under artifacts/ (and MP4 if ffmpeg is available).
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO / "artifacts"


def _write_temp_demo_pdf() -> Path:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS / "_record_demo_input.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(100, 750, "importtoCSV demo — equipment note Model X-100")
    c.drawString(100, 730, "Capacity: 5000 bushels")
    c.save()
    return path


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_http(url: str, timeout: float = 30.0) -> None:
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except (urllib.error.URLError, OSError):
            time.sleep(0.3)
    raise RuntimeError(f"Server did not respond: {url}")


def main() -> int:
    try:
        sample_pdf = _write_temp_demo_pdf()
    except ImportError:
        print("Install dev deps: pip install -e '.[dev]'", file=sys.stderr)
        return 1

    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "PYTHONPATH": str(REPO)}

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "importtocsv.web_app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(REPO),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    try:
        _wait_http(f"{base}/health")
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        video_dir = ARTIFACTS / "playwright-videos"
        if video_dir.exists():
            shutil.rmtree(video_dir)
        video_dir.mkdir(parents=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 960, "height": 720},
                record_video_dir=str(video_dir),
                record_video_size={"width": 960, "height": 720},
            )
            page = context.new_page()
            page.goto(base, wait_until="networkidle")
            page.wait_for_selector("#file")
            page.set_input_files("#file", str(sample_pdf))
            page.click("#submit")
            page.wait_for_selector(".status.ok", timeout=120_000)
            time.sleep(1.2)
            context.close()
            browser.close()

        webms = list(video_dir.glob("*.webm"))
        if not webms:
            print("No WebM produced.", file=sys.stderr)
            return 1
        latest = max(webms, key=lambda p: p.stat().st_mtime)
        out_webm = ARTIFACTS / "importtocsv_ui_demo.webm"
        shutil.copy(latest, out_webm)
        print(f"Wrote {out_webm}")

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            out_mp4 = ARTIFACTS / "importtocsv_ui_demo.mp4"
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(out_webm),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(out_mp4),
                ],
                check=True,
                capture_output=True,
            )
            print(f"Wrote {out_mp4}")
        else:
            print("ffmpeg not found — skipped MP4 transcode.")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
