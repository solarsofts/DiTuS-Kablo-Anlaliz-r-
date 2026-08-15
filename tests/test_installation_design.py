from __future__ import annotations

from pathlib import Path

from ucd.calculations.installation import (
    generate_standard_cross_section,
    resolved_physical_cables,
    validate_installation_design,
)
from ucd.models.project import ExternalHeatSourceData, InstallationDesignData, ProjectData


ROOT = Path(__file__).resolve().parents[1]


def test_default_project_migrates_legacy_layout_into_physical_objects() -> None:
    project = ProjectData()
    design = project.installation_design
    assert design.model_revision == "0.16.9.4.34"
    assert design.solver_coupling_mode == "PRODUCTION_LINKED"
    assert len(design.cross_sections) == len(project.thermal_design.regions)
    assert {tuple(item.region_ids) for item in design.cross_sections} == {(item.region_id,) for item in project.thermal_design.regions}
    section = design.cross_sections[0]
    assert {item.phase for item in section.physical_cables} == {"A", "B", "C"}
    assert all(item.depth_m > 0 for item in section.physical_cables)
    assert not [item for item in validate_installation_design(project) if item.severity == "ERROR"]


def test_two_circuit_parallel_phase_orders_create_explicit_physical_cables() -> None:
    section = generate_standard_cross_section(
        cross_section_id="ICS-ANNEX-F",
        name="2 devre / 2 paralel",
        arrangement="FLAT",
        circuit_count=2,
        parallel_cables_per_phase=2,
        phase_orders=["ABC", "CBA"],
        circuit_load_currents_a=[900.0, 600.0],
        phase_spacing_m=0.25,
        circuit_spacing_m=1.5,
        parallel_group_spacing_m=0.35,
        burial_depth_m=1.2,
        outer_diameter_m=0.11,
    )
    assert len(section.circuits) == 2
    assert len(section.physical_cables) == 12
    assert len({item.physical_cable_id for item in section.physical_cables}) == 12
    c2 = [item for item in section.physical_cables if item.circuit_id == "C2" and item.parallel_index == 1]
    assert [item.phase for item in c2] == ["C", "B", "A"]
    resolved = resolved_physical_cables(section)
    assert {round(item.current_a, 6) for item in resolved if item.circuit_id == "C1"} == {450.0}
    assert {round(item.current_a, 6) for item in resolved if item.circuit_id == "C2"} == {300.0}


def test_partial_current_overrides_allocate_remaining_phase_current() -> None:
    section = generate_standard_cross_section(
        cross_section_id="ICS-CURRENT",
        name="Akım paylaşımı",
        arrangement="TREFOIL",
        circuit_count=1,
        parallel_cables_per_phase=2,
        circuit_load_currents_a=[1000.0],
        outer_diameter_m=0.10,
    )
    a = [item for item in section.physical_cables if item.phase == "A"]
    a[0].current_override_a = 620.0
    resolved = {item.physical_cable_id: item for item in resolved_physical_cables(section)}
    assert resolved[a[0].physical_cable_id].current_a == 620.0
    assert resolved[a[1].physical_cable_id].current_a == 380.0


def test_duct_bank_generation_assigns_unique_slots() -> None:
    section = generate_standard_cross_section(
        cross_section_id="ICS-DUCT",
        name="Duct bank",
        arrangement="DUCT_BANK",
        circuit_count=2,
        parallel_cables_per_phase=1,
        phase_orders=["ABC", "CBA"],
        duct_rows=2,
        duct_columns=3,
        burial_depth_m=1.5,
        phase_spacing_m=0.22,
        outer_diameter_m=0.10,
    )
    assert len(section.duct_slots) == 6
    assert len(section.physical_cables) == 6
    assert len({item.duct_slot_id for item in section.physical_cables}) == 6
    slot_map = {item.slot_id: item for item in section.duct_slots}
    for cable in section.physical_cables:
        slot = slot_map[cable.duct_slot_id]
        assert cable.x_m == slot.x_m
        assert cable.depth_m == slot.depth_m


def test_validation_detects_overlap_and_unknown_circuit() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.physical_cables[1].x_m = section.physical_cables[0].x_m
    section.physical_cables[1].depth_m = section.physical_cables[0].depth_m
    section.physical_cables[2].circuit_id = "UNKNOWN"
    codes = {item.code for item in validate_installation_design(project)}
    assert "CABLE_OVERLAP" in codes
    assert "UNKNOWN_CIRCUIT" in codes


def test_installation_round_trip_preserves_arbitrary_geometry_and_external_heat() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.physical_cables[0].x_m = -1.2345
    section.physical_cables[0].depth_m = 2.3456
    section.region_ids = ["TR-001", "TR-002"]
    section.external_heat_sources.append(
        ExternalHeatSourceData("HS-01", "Komşu boru", 0.75, 1.8, 45.0, 0.08)
    )
    loaded = ProjectData.from_dict(project.to_dict())
    loaded_section = loaded.installation_design.cross_sections[0]
    assert loaded.schema_version == "0.16.4"
    assert loaded_section.physical_cables[0].x_m == -1.2345
    assert loaded_section.physical_cables[0].depth_m == 2.3456
    assert loaded_section.region_ids == ["TR-001", "TR-002"]
    assert loaded_section.external_heat_sources[0].heat_w_m == 45.0


def test_ui_exposes_production_linked_installation_designer_without_replacing_solver_equations() -> None:
    source = (ROOT / "src" / "ucd" / "ui" / "main_window.py").read_text(encoding="utf-8")
    dialog_source = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "Kablo-Kanal Düzeni" in source
    assert "InstallationDesignerDialog" in source
    assert "solver_coupling_mode" in dialog_source
    assert "üretim hesaplarına bağlanır" in dialog_source
    assert "Geometri kaydı mevcut sonuçları geçersiz kılar" in dialog_source


def test_packaged_v0163_installation_example_loads_without_validation_errors() -> None:
    import json

    path = ROOT / "examples" / "sample_installation_v0.16.3.ucd.json"
    project = ProjectData.from_dict(json.loads(path.read_text(encoding="utf-8")))
    assert len(project.installation_design.cross_sections) == 3
    errors = [item for item in validate_installation_design(project) if item.severity == "ERROR"]
    assert not errors


def test_legacy_projection_uses_region_specific_depth_and_installation_type() -> None:
    project = ProjectData()
    by_region = {section.region_ids[0]: section for section in project.installation_design.cross_sections}
    assert by_region["TR-01"].installation_type == "DIRECT_BURIED"
    assert by_region["TR-02"].installation_type == "DUCT_BANK"
    assert by_region["TR-03"].installation_type == "HDD"
    assert min(item.depth_m for item in by_region["TR-03"].physical_cables) >= 6.0
    assert "Duct slot" in by_region["TR-02"].notes


def test_section_double_click_does_not_mutate_live_active_section_before_save() -> None:
    source = (ROOT / "src" / "ucd" / "ui" / "main_window.py").read_text(encoding="utf-8")
    dialog_source = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "self.project.installation_design.active_cross_section_id = str(data)" not in source
    assert "initial_section_id=initial_section_id" in source
    assert "self.design.active_cross_section_id = initial_section_id" in dialog_source


def test_default_and_legacy_generated_trefoil_use_touching_outer_diameter_centres() -> None:
    from math import hypot

    project = ProjectData()
    diameter = project.cable.overall_diameter_mm / 1000.0
    section = project.installation_design.cross_sections[0]
    points = {item.phase: (item.x_m, item.depth_m) for item in section.physical_cables if item.circuit_id == "C1"}
    distances = [hypot(points[a][0] - points[b][0], points[a][1] - points[b][1]) for a, b in (("A", "B"), ("B", "C"), ("C", "A"))]
    assert all(abs(value - diameter) < 1e-12 for value in distances)

    raw = project.to_dict()
    raw["installation_design"]["model_revision"] = "0.16.9.4.10"
    raw["installation_design"]["solver_coupling_mode"] = "DESIGN_ONLY"
    legacy_section = raw["installation_design"]["cross_sections"][0]
    legacy_section["source_reference"] = "LEGACY_PROJECT_PROJECTION"
    for item in legacy_section["physical_cables"]:
        if item["circuit_id"] == "C1":
            if item["phase"] == "A": item["x_m"], item["depth_m"] = 0.0, 1.20
            if item["phase"] == "B": item["x_m"], item["depth_m"] = -0.075, 1.3299038105676657
            if item["phase"] == "C": item["x_m"], item["depth_m"] = 0.075, 1.3299038105676657
    loaded = ProjectData.from_dict(raw)
    points = {item.phase: (item.x_m, item.depth_m) for item in loaded.installation_design.cross_sections[0].physical_cables if item.circuit_id == "C1"}
    distances = [hypot(points[a][0] - points[b][0], points[a][1] - points[b][1]) for a, b in (("A", "B"), ("B", "C"), ("C", "A"))]
    assert all(abs(value - diameter) < 1e-12 for value in distances)
    assert loaded.installation_design.solver_coupling_mode == "PRODUCTION_LINKED"
