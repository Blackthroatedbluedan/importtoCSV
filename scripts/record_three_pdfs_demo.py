#!/usr/bin/env python3
"""
Record the web UI processing three sample PDFs (preview table + status).
Expects files under uploads/ (Brock fact sheet, bucket brochure, Langman drawing).
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
UPLOADS = Path("/home/ubuntu/.cursor/projects/workspace/uploads")

SAMPLES: list[tuple[str, dict[str, str]]] = [
    ("BR-2287-202201-Brock-EVEREST-Storage-Capacities-Fact-Sheet-EM.pdf", {}),
    ("BUCKET-ELEVATOR-lr.pdf", {"ocr_lang": "eng+fra"}),
    ("1809_Langman.pdf", {}),
]


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
    missing = [name for name, _ in SAMPLES if not (UPLOADS / name).is_file()]
    if missing:
        print("Missing PDF(s) in uploads dir:", missing, file=sys.stderr)
        print(f"Expected under: {UPLOADS}", file=sys.stderr)
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
        video_dir = ARTIFACTS / "playwright-three-pdfs"
        if video_dir.exists():
            shutil.rmtree(video_dir)
        video_dir.mkdir(parents=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1100, "height": 800},
                record_video_dir=str(video_dir),
                record_video_size={"width": 1100, "height": 800},
            )
            page = context.new_page()
            page.goto(base, wait_until="networkidle")

            for pdf_name, extra_fields in SAMPLES:
                page.goto(base, wait_until="networkidle")
                path = UPLOADS / pdf_name
                page.set_input_files("#file", str(path))
                page.locator("details.advanced summary").click()
                lang = extra_fields.get("ocr_lang", "eng")
                page.fill("#ocr_lang", lang)
                page.click("#submit")
                page.wait_for_selector("#preview-section:not(.hidden)", timeout=180_000)
                page.wait_for_selector(".status.ok", timeout=10_000)
                page.locator(".table-wrap").evaluate("el => el.scrollTop = 120")
                time.sleep(1.2)
                page.locator(".table-wrap").evaluate("el => el.scrollTop = 400")
                time.sleep(1.0)

            time.sleep(0.8)
            context.close()
            browser.close()

        webms = list(video_dir.glob("*.webm"))
        if not webms:
            print("No WebM produced.", file=sys.stderr)
            return 1
        latest = max(webms, key=lambda p: p.stat().st_mtime)
        out_webm = ARTIFACTS / "importtocsv_three_files_demo.webm"
        shutil.copy(latest, out_webm)
        print(f"Wrote {out_webm}")

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            out_mp4 = ARTIFACTS / "importtocsv_three_files_demo.mp4"
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
            opt = Path("/opt/cursor/artifacts")
            if opt.is_dir():
                shutil.copy(out_mp4, opt / "importtocsv_three_files_demo.mp4")
        else:
            print("ffmpeg not found — skipped MP4.")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
