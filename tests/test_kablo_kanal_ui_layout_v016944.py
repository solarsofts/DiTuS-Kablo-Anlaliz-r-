from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_native_soil_background_stays_below_engineered_layers() -> None:
    source = _source()
    assert "native_soil.setZValue(-30)" in source
    assert "soil_hatch.setZValue(-29)" in source
    assert 'QPen(QColor("#5d452f"), 3.2), -20' in source
    assert "_draw_layer_boundary" in source


def test_toolbar_is_multiline_and_does_not_use_single_overflow_row() -> None:
    source = _source()
    assert 'view_toolbar = QGroupBox("Görünüm ve gölge sonuçlar")' in source
    assert "view_grid = QGridLayout(view_toolbar)" in source
    assert "view_grid.addWidget(self.contour_status_label, 2, 0, 1, 9)" in source
    assert "view_row = QHBoxLayout()" not in source


def test_right_panel_uses_two_accordion_sections_and_keeps_tables_visible() -> None:
    source = _source()
    assert 'QPushButton("▾ Kesit ve Katman Ayarları")' in source
    assert 'QPushButton("▸ Devre / Kablo / Duct Yerleşimi")' in source
    assert "def _open_right_panel_section" in source
    assert 'self.parameter_scroll.setVisible(target == "upper")' in source
    assert 'self.lower_panel.setVisible(target == "lower")' in source
    assert "right_splitter = QSplitter(Qt.Vertical)" not in source
    assert "self.tabs.setMinimumHeight(150)" in source
    assert "tab_specs = (" in source
    assert "Fiziksel Kablolar" not in source
    assert "Duct Slotları" not in source
    assert '(self.duct_table, "Duct"' in source
    assert "validation_scroll.setMaximumHeight(92)" in source


def test_contrast_safe_palette_v2_is_used() -> None:
    source = _source()
    assert 'layer_palette_version", 2' in source
    assert 'layer_color_v2/' in source
    assert '"GENERAL_BACKFILL": QColor("#eee5d2")' in source
    assert '"THERMAL_BACKFILL": QColor("#f0ca4e")' in source
