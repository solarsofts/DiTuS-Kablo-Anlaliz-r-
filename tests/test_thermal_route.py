from __future__ import annotations

from dataclasses import replace

import pytest

from ucd.calculations.thermal_route import (
    ThermalRouteInputError,
    materialize_route_sections,
    resolve_thermal_region,
    solve_thermal_route,
    validate_thermal_design,
)
from ucd.calculations.thermal_resistance import resolve_external_thermal_resistance
from ucd.models.project import (
    ProjectData,
    ThermalRegion,
    THERMAL_STATE_AS_BUILT,
    THERMAL_STATE_TESTED,
)


def test_default_thermal_regions_cover_the_route_without_errors() -> None:
    project = ProjectData()
    issues = validate_thermal_design(project.thermal_design, project.cable)
    assert not [issue for issue in issues if issue.severity == "ERROR"]
    assert project.thermal_design.regions[0].start_m == 0.0
    assert project.thermal_design.regions[-1].end_m == project.thermal_design.route_length_m


def test_gap_and_overlap_are_detected() -> None:
    project = ProjectData()
    project.thermal_design.regions = [
        ThermalRegion("R1", "A", 0.0, 100.0, "TPL-DG-TREFOIL-TB01"),
        ThermalRegion("R2", "B", 90.0, 150.0, "TPL-DG-TREFOIL-TB01"),
        ThermalRegion("R3", "C", 200.0, 300.0, "TPL-DG-TREFOIL-TB01"),
    ]
    project.thermal_design.route_length_m = 300.0
    codes = {issue.code for issue in validate_thermal_design(project.thermal_design, project.cable)}
    assert "REGION_OVERLAP" in codes
    assert "COVERAGE_GAP" in codes


def test_region_materialization_preserves_chainage_and_template() -> None:
    project = ProjectData()
    sections = materialize_route_sections(project.thermal_design, project.cable)
    assert sections[0].start_chainage_m == 0.0
    assert sections[-1].end_chainage_m == project.thermal_design.route_length_m
    assert sections[0].thermal_template_id == "TPL-DG-TREFOIL-TB01"
    assert sections[0].external_thermal_mode == "AUTO_MIXED_ZONE"


def test_lower_resistivity_backfill_reduces_mixed_zone_t4() -> None:
    project = ProjectData()
    region = project.thermal_design.regions[0]
    section = materialize_route_sections(project.thermal_design, project.cable)[0]
    baseline = resolve_external_thermal_resistance(project.cable, section)

    low = next(m for m in project.thermal_design.materials if m.material_id == "MAT-TB-01")
    low.thermal_resistivity_km_w = 0.45
    improved_section = materialize_route_sections(project.thermal_design, project.cable)[0]
    improved = resolve_external_thermal_resistance(project.cable, improved_section)
    assert improved.effective_t4_km_w < baseline.effective_t4_km_w
    assert resolve_thermal_region(project.thermal_design, region, project.cable).cable_cover.thermal_resistivity_km_w == 0.45


def test_special_installation_requires_positive_manual_t4() -> None:
    project = ProjectData()
    project.thermal_design.templates[1].manual_t4_km_w = 0.0
    project.thermal_design.regions[1].overrides["manual_t4_km_w"] = 0.0
    issues = validate_thermal_design(project.thermal_design, project.cable)
    assert any(issue.code == "MANUAL_T4" and issue.region_id == "TR-02" for issue in issues)
    with pytest.raises(ThermalRouteInputError):
        materialize_route_sections(project.thermal_design, project.cable)


def test_route_solver_identifies_lowest_ampacity_region_as_critical() -> None:
    project = ProjectData()
    project.design_basis.normal_current_per_active_circuit_a = 800.0
    project.design_basis.n1_current_per_circuit_a = 900.0
    project.design_basis.design_current_per_circuit_a = 950.0
    project.thermal_design.regions[2].overrides["manual_t4_km_w"] = 2.5
    result = solve_thermal_route(project)
    assert result.active.scenario_id == "DESIGN"
    assert result.active.critical_region_id == "TR-03"
    assert result.active.route_ampacity_a == min(r.iec.ampacity_a for r in result.active.regions)
    assert result.active.critical_reasons


def test_design_tested_as_built_layers_round_trip() -> None:
    project = ProjectData()
    project.thermal_design.active_data_state = THERMAL_STATE_AS_BUILT
    project.thermal_design.materials[0].data_state = THERMAL_STATE_TESTED
    project.thermal_design.regions[0].data_state = THERMAL_STATE_AS_BUILT
    project.thermal_design.regions[0].source_reference = "Saha Test Raporu TR-001"
    loaded = ProjectData.from_dict(project.to_dict())
    assert loaded.schema_version == "0.16.4"
    assert loaded.thermal_design.active_data_state == THERMAL_STATE_AS_BUILT
    assert loaded.thermal_design.materials[0].data_state == THERMAL_STATE_TESTED
    assert loaded.thermal_design.regions[0].source_reference == "Saha Test Raporu TR-001"


def test_legacy_v010_project_creates_thermal_regions_from_route_sections() -> None:
    raw = {
        "schema_version": "0.10",
        "route_sections": [
            {"name": "Kil", "length_m": 500.0, "soil_thermal_resistivity_km_w": 1.6},
            {"name": "HDD", "length_m": 200.0, "section_type": "HDD", "external_thermal_resistance_t4_km_w": 1.8},
        ],
    }
    project = ProjectData.from_dict(raw)
    assert project.schema_version == "0.16.4"
    assert len(project.thermal_design.regions) == 2
    assert project.thermal_design.route_length_m == 700.0
    assert project.thermal_design.regions[1].template_id == "TPL-HDD-MANUAL"
