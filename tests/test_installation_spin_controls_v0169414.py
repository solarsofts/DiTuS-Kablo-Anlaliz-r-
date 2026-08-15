from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_installation_spinboxes_use_dedicated_controls_and_explicit_button_regions() -> None:
    source = _source()
    assert "class _InstallationDoubleSpinBox" in source
    assert "class _InstallationIntegerSpinBox" in source
    assert "self.width() - 26.0" in source
    assert "self.stepBy(1 if event.position().y() < self.height() / 2.0 else -1)" in source
    assert "height: 14px" in source


def test_installation_spinbox_wheel_is_forwarded_to_scroll_container() -> None:
    source = _source()
    block = source[source.index("class _InstallationSpinControlMixin"):source.index("class _InstallationDoubleSpinBox")]
    assert "def wheelEvent" in block
    assert "event.ignore()" in block
    assert "setAccelerated(False)" in block


def test_installation_canvas_zoom_is_less_aggressive() -> None:
    source = _source()
    assert "factor = 1.08 if zoom_in else 1 / 1.08" in source
    assert "factor = 1.15" not in source
