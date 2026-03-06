# Copyright 2026 James G Willmore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Pytest configuration and shared fixtures for pytasktracker tests."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

_GUI_HOST = "127.0.0.1"
_GUI_PORT = 8989
_PROJECT_ROOT = Path(__file__).parent.parent
_MAIN_PY = _PROJECT_ROOT / "main.py"
_SRC_DIR = _PROJECT_ROOT / "src"


def _wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    """Block until the given TCP port is accepting connections or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


@pytest.fixture(scope="session")
def gui_server():
    """Start the NiceGUI app as a subprocess for the entire test session.

    Using a subprocess avoids NiceGUI's pytest-detection logic which would
    otherwise require NICEGUI_SCREEN_TEST_PORT instead of starting normally.

    Yields the temporary directory path so tests can access the database if needed.
    """
    with TemporaryDirectory() as tmp_dir:
        database_path = Path(tmp_dir) / "test_gui.duckdb"

        env = {
            **os.environ,
            "DATABASE_URL": f"duckdb:///{database_path}",
            "RECREATE_DB": "true",
            "PYTHONPATH": str(_SRC_DIR),
            "NICEGUI_SCREEN_TEST_PORT": str(_GUI_PORT),
        }

        process = subprocess.Popen(
            [
                sys.executable,
                str(_MAIN_PY),
                "--mode",
                "gui",
                "--port",
                str(_GUI_PORT),
                "--database-url",
                f"duckdb:///{database_path}",
                "--recreate-db",
            ],
            env=env,
            cwd=str(_PROJECT_ROOT),
        )

        assert _wait_for_port(
            _GUI_HOST, _GUI_PORT
        ), f"GUI server did not start on {_GUI_HOST}:{_GUI_PORT} within timeout"

        yield tmp_dir

        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture(scope="session")
def base_url(gui_server):  # noqa: ARG001
    """Base URL for the running GUI application (overrides pytest-playwright default)."""
    return f"http://{_GUI_HOST}:{_GUI_PORT}"
