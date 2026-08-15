from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py"


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_direct_buried_and_duct_bank_have_separate_width_controls() -> None:
    source = _source()
    assert '"trench_width_m", "Hendek alt genişliği [m]"' in source
    assert '"duct_bank_width_m", "Duct bank blok genişliği [m]"' in source
    assert 'self.geometry_labels["trench_width_m"].setText("Kazı alt genişliği [m]")' in source
    assert "def _required_trench_bottom_width" in source
    assert "def _apply_required_trench_width" in source
    assert "Fiziksel minimum genişliği uygula" in source
    assert "duct/grout blok + toplam 0,30 m kazı yan payı" in source


def test_installation_scope_is_explicit_and_irrelevant_fields_are_hidden() -> None:
    source = _source()
    assert "DIRECT_BURIED — doğrudan gömülü" in source
    assert "DUCT_BANK — boru / kanal bankası" in source
    assert "def _set_geometry_field_visible" in source
    assert "def _set_material_field_visible" in source
    assert "direct_only =" in source
    assert "duct_only =" in source
    assert "Doğrudan gömülü bedding/thermal-backfill alanları bu modda kullanılmaz" in source


def test_dimension_text_uses_same_scene_transform_as_geometry() -> None:
    source = _source()
    block = source.split("def _add_horizontal_dimension", 1)[1].split("def _add_geometry_handle", 1)[0]
    assert "Dimension labels deliberately scale together with their extension lines" in block
    assert ".setFlag(QGraphicsItem.ItemIgnoresTransformations" not in block
    assert "Hendek alt genişliği" in source
    assert "Duct bank blok genişliği =" in source


def test_duct_objects_are_not_rendered_in_direct_buried_mode() -> None:
    source = _source()
    assert "for slot in (section.duct_slots if installation_kind == THERMAL_INSTALL_DUCT_BANK else [])" in source
    assert 'installation_text = f"{installation_kind} / {INSTALLATION_TYPE_TR.get' in source
