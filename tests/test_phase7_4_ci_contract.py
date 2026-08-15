from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_matrix_covers_windows_linux_and_supported_python_versions():
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "ubuntu-latest" in text and "windows-latest" in text
    assert "'3.11'" in text and "'3.12'" in text
    assert "QT_QPA_PLATFORM: offscreen" in text
    assert "python -m pytest" in text


def test_ci_does_not_restore_legacy_pythonpath_hack():
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "PYTHONPATH" not in text
