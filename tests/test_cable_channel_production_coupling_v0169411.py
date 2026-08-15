from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ucd.calculations.installation_coupling import (
    PRODUCTION_GEOMETRY_ENGINE_IDS,
    synchronize_installation_geometry,
)
from ucd.calculations.nodal_thermal import solve_nodal_region
from ucd.calculations.procurement import build_procurement_package
from ucd.calculations.project_workflow import engine_input_signature
from ucd.calculations.thermal_route import solve_thermal_route
from ucd.models.project import ExternalHeatSourceData, ProjectData


ROOT = Path(__file__).resolve().parents[1]


def _line(package, item_id: str):
    return next(item for item in package.lines if item.item_id == item_id)


def test_geometry_sync_projects_channel_to_legacy_scalar_inputs() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.channel_geometry.trench_width_m = 1.73
    section.channel_geometry.trench_depth_m = 1.88
    section.physical_cables[0].depth_m = 1.31
    section.physical_cables[1].depth_m = 1.31
    section.physical_cables[2].depth_m = 1.31

    changed = synchronize_installation_geometry(project)

    assert "TR-01" in changed
    region = project.thermal_design.regions[0]
    route = project.route_sections[0]
    assert region.overrides["trench_width_m"] == 1.73
    assert region.overrides["trench_depth_m"] == 1.88
    assert route.burial_depth_m == 1.31
    assert route.phase_spacing_m == region.overrides["phase_spacing_m"]
    assert route.cross_section_id == section.cross_section_id
    assert region.source_reference == f"INSTALLATION_PRODUCTION_LINK:{section.cross_section_id}"


def test_geometry_change_invalidates_every_dependent_engine_signature() -> None:
    baseline = ProjectData()
    edited = deepcopy(baseline)
    edited.installation_design.cross_sections[0].channel_geometry.trench_width_m += 0.17

    for engine_id in PRODUCTION_GEOMETRY_ENGINE_IDS:
        assert engine_input_signature(baseline, engine_id) != engine_input_signature(edited, engine_id)


def test_channel_geometry_changes_production_iec_and_civil_quantity() -> None:
    baseline = ProjectData()
    edited = deepcopy(baseline)
    geometry = edited.installation_design.cross_sections[0].channel_geometry
    geometry.trench_width_m = 2.0
    geometry.thermal_backfill_height_m += 0.35

    base_iec = solve_thermal_route(baseline).active.regions[0].iec
    edited_iec = solve_thermal_route(edited).active.regions[0].iec
    assert abs(edited_iec.ampacity_a - base_iec.ampacity_a) > 1.0
    assert abs(
        edited_iec.conductor_temperature_at_design_c
        - base_iec.conductor_temperature_at_design_c
    ) > 0.1

    base_package = build_procurement_package(ProjectData())
    edited_package = build_procurement_package(deepcopy(edited))
    assert _line(edited_package, "CIV-EXC-001").final_quantity != _line(base_package, "CIV-EXC-001").final_quantity
    assert _line(edited_package, "CIV-TBF-001").final_quantity != _line(base_package, "CIV-TBF-001").final_quantity


def test_external_heat_source_from_channel_reaches_production_nodal_solver() -> None:
    baseline = ProjectData()
    heated = deepcopy(baseline)
    heated.installation_design.cross_sections[0].external_heat_sources.append(
        ExternalHeatSourceData("HS-PROD", "Komşu sıcak hat", 0.0, 1.0, 100.0, 0.10)
    )

    base_iec = solve_thermal_route(baseline).active.regions[0].iec
    heated_iec = solve_thermal_route(heated).active.regions[0].iec
    base_result = solve_nodal_region(
        baseline, "TR-01", 800.0, 1, 0.05, base_iec, calculate_ampacity=False
    )
    heated_result = solve_nodal_region(
        heated, "TR-01", 800.0, 1, 0.05, heated_iec, calculate_ampacity=False
    )
    assert heated_result.maximum_conductor_temperature_c > base_result.maximum_conductor_temperature_c + 10.0
    assert any("Kablo-Kanal gerçek x-y" in line for line in heated_result.trace)


def test_ui_save_marks_results_stale_and_offers_combined_recalculation() -> None:
    source = (ROOT / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    assert "Geometri değişti — yeniden hesap gerekli" in source
    assert "Birleşik hesap akışı şimdi başlatılsın mı?" in source
    assert "mark_engine_runs_stale" in source
    assert "QTimer.singleShot(0, self.run_combined_calculation)" in source
