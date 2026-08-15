from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_circuit_panel_is_visible_through_lower_accordion_header() -> None:
    source = _source()
    assert 'QPushButton("▸ Devre / Kablo / Duct Yerleşimi")' in source
    assert 'QPushButton("Devre Yerleşimini Aç")' not in source
    assert "lower_panel.setMinimumHeight(180)" in source
    assert "self.tabs.setCurrentIndex(0)" in source
    assert "def _initialise_right_panel_layout" in source
    assert "def _show_circuit_placement_panel" in source
    assert 'self._open_right_panel_section("lower")' in source


def test_independent_neighbor_line_spacings_are_supported() -> None:
    source = _source()
    assert "Komşu hat merkez aralıkları [m] (tablo sırası):" in source
    assert "def _apply_neighbor_circuit_gaps" in source
    assert "current_x += gap" in source
    assert "self.circuit_table.setItem(row, 7" in source
    assert "Hat aralıkları:" in source
    assert "C1-C2, C2-C3, C3-C4" in source


def test_irrelevant_spacing_and_duct_fields_are_conditional() -> None:
    source = _source()
    assert "def _update_preset_field_visibility" in source
    assert "parallel_active = int(self.preset_parallel.value()) > 1" in source
    assert "multiple_circuits = int(self.preset_circuits.value()) > 1" in source
    assert 'duct_active = bool(section and str(section.installation_type).upper() == THERMAL_INSTALL_DUCT_BANK)' in source
    assert "self._set_preset_field_visible(self.preset_parallel_spacing, parallel_active)" in source
    assert "self._set_preset_field_visible(self.preset_duct_cols, duct_active)" in source
    assert "Farklı hat/devreler arasındaki mesafe değildir" in source
