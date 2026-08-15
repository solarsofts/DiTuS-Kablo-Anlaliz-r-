from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_right_panel_is_accordion_not_vertical_splitter() -> None:
    source = _source()
    assert 'QPushButton("▾ Kesit ve Katman Ayarları")' in source
    assert 'QPushButton("▸ Devre / Kablo / Duct Yerleşimi")' in source
    assert 'ui/kablo_kanal/right_panel_section' in source
    assert 'self.parameter_scroll.setVisible(target == "upper")' in source
    assert 'self.lower_panel.setVisible(target == "lower")' in source
    assert 'self.right_splitter' not in source


def test_read_only_canvas_supports_pan_and_cursor_centred_zoom() -> None:
    source = _source()
    assert 'self.setDragMode(QGraphicsView.ScrollHandDrag)' in source
    assert 'self.setCursor(Qt.OpenHandCursor)' in source
    assert 'self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)' in source
    assert 'self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)' in source
    assert 'scene_before = self.mapToScene(cursor_pos)' in source
    assert 'scene_after = self.mapToScene(cursor_pos)' in source
    assert 'self.translate(correction.x(), correction.y())' in source
    assert 'super().mousePressEvent(event)' in source
