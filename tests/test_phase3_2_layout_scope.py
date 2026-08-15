from __future__ import annotations

from dataclasses import replace

import pytest

from ucd.calculations.bonding import _phase_positions as bonding_phase_positions, solve_bonding
from ucd.calculations.iec60287 import classify_calculation_error
from ucd.calculations.installation import generate_standard_cross_section
from ucd.calculations.installation_coupling import _arrangement
from ucd.calculations.thermal_resistance import (
    ThermalInputError,
    cable_positions_m,
    resolve_external_thermal_resistance,
)
from ucd.calculations.thermal_route import solve_thermal_route, validate_thermal_design
from ucd.models.project import (
    EXTERNAL_THERMAL_AUTO,
    CableData,
    ProjectData,
    RouteSection,
    THERMAL_INSTALL_DIRECT_BURIED,
    THERMAL_INSTALL_DUCT_BANK,
)


def test_vertical_analytical_positions_use_shallowest_axis_and_adjacent_pitch() -> None:
    cable = CableData(arrangement="Vertical", overall_diameter_mm=100.0)
    section = RouteSection(
        "Vertical",
        1.0,
        section_type=THERMAL_INSTALL_DIRECT_BURIED,
        burial_depth_m=1.20,
        phase_spacing_m=0.15,
        external_thermal_mode=EXTERNAL_THERMAL_AUTO,
    )
    positions = cable_positions_m(cable, section)
    assert [item[0] for item in positions] == pytest.approx([0.0, 0.0, 0.0])
    assert [item[1] for item in positions] == pytest.approx([1.20, 1.35, 1.50])
    result = resolve_external_thermal_resistance(cable, section)
    assert [item[0] for item in result.positions_m] == pytest.approx([0.0, 0.0, 0.0])
    assert [item[1] for item in result.positions_m] == pytest.approx([1.20, 1.35, 1.50])


def test_vertical_direct_buried_overlap_is_rejected() -> None:
    cable = CableData(arrangement="Vertical", overall_diameter_mm=105.0)
    section = RouteSection(
        "Vertical overlap",
        1.0,
        section_type=THERMAL_INSTALL_DIRECT_BURIED,
        burial_depth_m=1.20,
        phase_spacing_m=0.08,
        external_thermal_mode=EXTERNAL_THERMAL_AUTO,
    )
    with pytest.raises(ThermalInputError, match="VERTICAL_PHASE_OVERLAP"):
        cable_positions_m(cable, section)


def test_bonding_vertical_uses_same_relative_slot_contract() -> None:
    positions = bonding_phase_positions("Vertical", 0.20, "BCA")
    assert positions["B"] == complex(0.0, 0.0)
    assert positions["C"] == complex(0.0, 0.20)
    assert positions["A"] == complex(0.0, 0.40)




def test_full_bonding_solver_accepts_vertical_fallback_geometry() -> None:
    project = ProjectData()
    project.cable.arrangement = "Vertical"
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert result.max_standing_voltage_v > 0.0


def test_custom_requires_explicit_positions_but_accepts_real_xy() -> None:
    cable = CableData(arrangement="Custom", overall_diameter_mm=100.0)
    section = RouteSection(
        "Custom",
        1.0,
        section_type=THERMAL_INSTALL_DIRECT_BURIED,
        external_thermal_mode=EXTERNAL_THERMAL_AUTO,
    )
    with pytest.raises(ThermalInputError, match="CUSTOM_POSITIONS_REQUIRED"):
        resolve_external_thermal_resistance(cable, section)
    explicit = ((-0.2, 1.1), (0.0, 1.3), (0.25, 1.2))
    result = resolve_external_thermal_resistance(cable, section, explicit)
    assert result.positions_m == explicit




@pytest.mark.parametrize("installation_type", ["DUCT_BANK", "HDD", "CONCRETE_TROUGH", "TUNNEL"])
def test_non_direct_installations_reject_auto_analytical_t4(installation_type: str) -> None:
    cable = CableData(arrangement="Trefoil")
    section = RouteSection(
        installation_type,
        1.0,
        section_type=installation_type,
        external_thermal_mode=EXTERNAL_THERMAL_AUTO,
    )
    with pytest.raises(ThermalInputError, match="ANALYTIC_MODEL_SCOPE_REQUIRES_NODAL"):
        resolve_external_thermal_resistance(cable, section)


def test_auto_analytical_scope_is_direct_buried_only_and_not_physical_rejection() -> None:
    project = ProjectData()
    project.thermal_design.regions[1].overrides["external_thermal_mode"] = EXTERNAL_THERMAL_AUTO
    issues = validate_thermal_design(project.thermal_design, project.cable)
    issue = next(item for item in issues if item.region_id == "TR-02" and item.code == "ANALYTIC_MODEL_SCOPE_REQUIRES_NODAL")
    assert issue.severity == "ERROR"
    result = solve_thermal_route(project).active
    outcome = next(item for item in result.region_outcomes if item.region_id == "TR-02")
    assert not outcome.success
    assert outcome.error_code == "ANALYTIC_MODEL_SCOPE_REQUIRES_NODAL"
    assert outcome.physical_rejection is False
    assert result.completion_status == "PARTIAL"
    assert result.suitability_status == "INDETERMINATE"
    assert classify_calculation_error(outcome.error_message) == (
        "ANALYTIC_MODEL_SCOPE_REQUIRES_NODAL", False
    )


def test_legacy_duct_arrangement_is_preserved_as_custom_xy_not_flat() -> None:
    section = generate_standard_cross_section(
        cross_section_id="ICS-DUCT", name="Duct", arrangement="DUCT_BANK",
        installation_type=THERMAL_INSTALL_DUCT_BANK,
        circuit_count=1, parallel_cables_per_phase=1,
    )
    assert section.installation_type == THERMAL_INSTALL_DUCT_BANK
    assert section.arrangement_label == "CUSTOM"
    assert _arrangement(section) == "Custom"
