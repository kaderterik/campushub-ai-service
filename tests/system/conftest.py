"""T18 sistem testleri için ortak yardımcılar.

Servis gerçek bir uvicorn süreci olarak ayağa kaldırılır ve testler ona
gerçek HTTP istekleri gönderir (Grup 3'ün Event Service'i gibi).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
APPS_DIR = Path(__file__).resolve().parent / "apps"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_server(app_path: str, port: int, extra_env: dict[str, str] | None = None) -> subprocess.Popen:
    env = os.environ.copy()
    env["CLASSIFIER_BACKEND"] = "fake"
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT), str(APPS_DIR)])
    if extra_env:
        env.update(extra_env)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", app_path, "--host", "127.0.0.1", "--port", str(port)],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def stop_server(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def wait_until_healthy(base_url: str, process: subprocess.Popen, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read().decode(errors="replace") if process.stdout else ""
            raise RuntimeError(f"Servis beklenmedik şekilde kapandı:\n{output}")
        try:
            if httpx.get(f"{base_url}/health", timeout=1.0).status_code == 200:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.1)
    raise TimeoutError(f"{base_url}/health {timeout} sn içinde 200 dönmedi")


@pytest.fixture(scope="session")
def running_service():
    """FakeClassifier ile çalışan gerçek bir uvicorn süreci."""
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    process = start_server("app.main:app", port)
    try:
        wait_until_healthy(base_url, process)
        yield base_url
    finally:
        stop_server(process)
