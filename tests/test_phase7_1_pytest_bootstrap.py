from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_src_layout_and_pytest_pythonpath() -> None:
    source = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'package-dir = {"" = "src"}' in source
    assert 'where = ["src"]' in source
    assert 'pythonpath = ["src"]' in source
    assert 'testpaths = ["tests"]' in source


def test_run_tests_does_not_depend_on_manual_pythonpath() -> None:
    source = (ROOT / "run_tests.bat").read_text(encoding="utf-8")
    assert "PYTHONPATH" not in source.upper()
    assert "-m pytest -q" in source


def test_setup_registers_editable_local_package() -> None:
    source = (ROOT / "setup_venv.bat").read_text(encoding="utf-8")
    assert "-m pip install --no-deps -e ." in source


def test_fresh_checkout_style_pytest_collection_works_without_pythonpath_env() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/test_application_database.py"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, completed.stdout
    assert "test_application_database" in completed.stdout
