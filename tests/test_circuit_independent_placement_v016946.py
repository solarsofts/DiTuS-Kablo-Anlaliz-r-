from pathlib import Path

from ucd.calculations.cable_channel_templates import (
    infer_circuit_placement,
    reposition_circuit_cables,
)
from ucd.calculations.installation import generate_standard_cross_section


ROOT = Path(__file__).resolve().parents[1]


def test_each_circuit_can_use_independent_formation_and_xy_reference() -> None:
    section = generate_standard_cross_section(
        cross_section_id="ICS-T",
        name="Bağımsız devre testi",
        arrangement="TREFOIL",
        circuit_count=2,
        parallel_cables_per_phase=1,
        outer_diameter_m=0.105,
    )
    reposition_circuit_cables(
        section,
        "C1",
        "TREFOIL",
        center_x_m=-0.45,
        reference_depth_m=1.10,
        phase_spacing_m=0.15,
        parallel_spacing_m=0.25,
        cable_outer_diameter_m=0.105,
    )
    c1_before = {
        item.physical_cable_id: (item.x_m, item.depth_m)
        for item in section.physical_cables
        if item.circuit_id == "C1"
    }
    reposition_circuit_cables(
        section,
        "C2",
        "FLAT",
        center_x_m=0.55,
        reference_depth_m=1.32,
        phase_spacing_m=0.20,
        parallel_spacing_m=0.30,
        cable_outer_diameter_m=0.105,
    )
    c1_after = {
        item.physical_cable_id: (item.x_m, item.depth_m)
        for item in section.physical_cables
        if item.circuit_id == "C1"
    }
    assert c1_after == c1_before
    assert section.arrangement_label == "CUSTOM"

    c1 = infer_circuit_placement(section, "C1")
    c2 = infer_circuit_placement(section, "C2")
    assert c1.arrangement == "TREFOIL"
    assert c2.arrangement == "FLAT"
    assert abs(c1.center_x_m + 0.45) < 1e-12
    assert abs(c2.center_x_m - 0.55) < 1e-12
    assert abs(c1.reference_depth_m - 1.10) < 1e-12
    assert abs(c2.reference_depth_m - 1.32) < 1e-12


def test_circuit_placement_uses_existing_physical_xy_without_new_project_object() -> None:
    model = (ROOT / "src" / "ucd" / "models" / "project.py").read_text(encoding="utf-8")
    ui = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    helper = (ROOT / "src" / "ucd" / "calculations" / "cable_channel_templates.py").read_text(encoding="utf-8")
    assert "class CircuitPlacementData" not in model
    assert "``PhysicalCableData`` coordinates" in helper
    assert "Seçili devre yerleşimini bağımsız uygula" in ui
    assert '"Bağımsız formasyon", "X merkezi [m]", "Referans derinliği [m]"' in ui
    assert "reposition_circuit_cables(" in ui


def test_canvas_annotations_are_separated_from_engineering_geometry() -> None:
    source = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "Keep the legend outside the engineering section" in source
    assert "ItemIgnoresTransformations" in source
    assert "Üst kum örtüsü" in source
    assert "Alt kum örtüsü" in source
    assert "Karma devre yerleşimi" in source
    assert "Kablo dış çapı eksik" in source


def test_independent_trefoil_spacing_is_outer_diameter_and_user_value_is_ignored() -> None:
    from math import hypot

    diameter = 0.105
    section = generate_standard_cross_section(
        cross_section_id="ICS-T",
        name="Bağımsız trefoil temas testi",
        arrangement="TREFOIL",
        circuit_count=1,
        parallel_cables_per_phase=1,
        outer_diameter_m=diameter,
    )
    reposition_circuit_cables(
        section,
        "C1",
        "TREFOIL",
        center_x_m=0.0,
        reference_depth_m=1.20,
        phase_spacing_m=0.75,
        parallel_spacing_m=0.25,
        cable_outer_diameter_m=diameter,
    )
    by_phase = {item.phase: item for item in section.physical_cables}
    distances = (
        hypot(by_phase["A"].x_m - by_phase["B"].x_m, by_phase["A"].depth_m - by_phase["B"].depth_m),
        hypot(by_phase["B"].x_m - by_phase["C"].x_m, by_phase["B"].depth_m - by_phase["C"].depth_m),
        hypot(by_phase["C"].x_m - by_phase["A"].x_m, by_phase["C"].depth_m - by_phase["A"].depth_m),
    )
    assert all(abs(value - diameter) < 1e-12 for value in distances)
    placement = infer_circuit_placement(section, "C1")
    assert placement.arrangement == "TREFOIL"
    assert abs(placement.phase_spacing_m - diameter) < 1e-12
