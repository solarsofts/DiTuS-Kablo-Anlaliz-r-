from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py"


def _build_ui_block() -> str:
    source = SOURCE.read_text(encoding="utf-8")
    start = source.index("    def _build_ui(self) -> None:")
    end = source.index("    def _merge_reference_materials", start)
    return source[start:end]


def test_canvas_view_buttons_do_not_resolve_canvas_before_creation() -> None:
    block = _build_ui_block()
    canvas_creation = block.index("self.canvas = InstallationCanvas()")
    fit_connection = block.index("fit_section_button.clicked.connect")
    reset_connection = block.index("zoom_reset_button.clicked.connect")
    assert fit_connection < canvas_creation
    assert reset_connection < canvas_creation
    assert "fit_section_button.clicked.connect(self.canvas.fit_to_section)" not in block[:canvas_creation]
    assert "zoom_reset_button.clicked.connect(self.canvas.zoom_reset)" not in block[:canvas_creation]
    assert "lambda _checked=False: self.canvas.fit_to_section()" in block
    assert "lambda _checked=False: self.canvas.zoom_reset()" in block
