#!/usr/bin/env python3
"""Screenshot the extracted-data table for three sample PDFs (Playwright)."""

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
ARTIFACTS = REPO / "artifacts" / "table-shots"
UPLOADS = Path("/home/ubuntu/.cursor/projects/workspace/uploads")

SHOTS: list[tuple[str, str, dict[str, str]]] = [
    (
        "BR-2287-202201-Brock-EVEREST-Storage-Capacities-Fact-Sheet-EM.pdf",
        "brock_table.png",
        {},
    ),
    (
        "BUCKET-ELEVATOR-lr.pdf",
        "bucket_elevator_table.png",
        {"ocr_lang": "eng+fra"},
    ),
    (
        "1809_Langman.pdf",
        "langman_table.png",
        {},
    ),
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
    missing = [name for name, _, _ in SHOTS if not (UPLOADS / name).is_file()]
    if missing:
        print("Missing PDF(s):", missing, file=sys.stderr)
        return 1

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    opt = Path("/opt/cursor/artifacts")
    if opt.is_dir():
        (opt / "table-shots").mkdir(parents=True, exist_ok=True)

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

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 900})

            for pdf_name, out_name, opts in SHOTS:
                page.goto(base, wait_until="networkidle")
                page.locator("details.advanced summary").click()
                if opts.get("ocr_lang"):
                    page.fill("#ocr_lang", opts["ocr_lang"])
                else:
                    page.fill("#ocr_lang", "eng")
                page.set_input_files("#file", str(UPLOADS / pdf_name))
                page.click("#submit")
                page.wait_for_selector("#preview-section:not(.hidden)", timeout=180_000)
                page.wait_for_selector(".status.ok")
                time.sleep(0.6)
                out_path = ARTIFACTS / out_name
                page.locator("#preview-section").screenshot(path=str(out_path))
                print(f"Wrote {out_path}")
                if opt.is_dir():
                    shutil.copy(out_path, opt / "table-shots" / out_name)

            browser.close()

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
