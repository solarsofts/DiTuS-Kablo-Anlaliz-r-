from __future__ import annotations

from copy import deepcopy

import pytest

from ucd.calculations.installation import generate_standard_cross_section
from ucd.calculations.multiconductor_thermal import (
    COUPLING_MODE,
    solve_multiconductor_thermal,
)
from ucd.models.project import (
    ExternalHeatSourceData,
    InstallationDesignData,
    ProjectData,
    RouteSection,
    ThermalRegion,
    default_bonding_system,
)


def _two_circuit_project() -> ProjectData:
    project = ProjectData()
    section = generate_standard_cross_section(
        cross_section_id="ICS-THERMAL-N",
        name="İki devre iki paralel gerçek x-y termal",
        arrangement="FLAT",
        circuit_count=2,
        parallel_cables_per_phase=2,
        phase_orders=["ABC", "CBA"],
        circuit_load_currents_a=[900.0, 600.0],
        phase_spacing_m=0.25,
        circuit_spacing_m=2.50,
        parallel_group_spacing_m=0.75,
        burial_depth_m=1.25,
        outer_diameter_m=0.105,
        region_ids=["TR-N"],
    )
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    project.route_sections = [RouteSection("R-N", 300.0, thermal_region_id="TR-N")]
    project.thermal_design.route_length_m = 300.0
    project.thermal_design.regions = [
        ThermalRegion("TR-N", "N-kablo termal", 0.0, 300.0, project.thermal_design.templates[0].template_id)
    ]
    project.bonding = default_bonding_system(300.0)
    return project


def test_default_real_xy_multiconductor_thermal_solves_all_regions() -> None:
    result = solve_multiconductor_thermal(ProjectData(), mesh_scale=2.0, max_iterations=25, tolerance_c=0.05)
    assert result.coupling_mode == COUPLING_MODE
    assert len(result.regions) == 3
    assert all(region.cables for region in result.regions)
    assert all(len(region.analytical_matrix_km_w) == len(region.cables) for region in result.regions)
    assert all(region.nodal_converged for region in result.regions)
    assert result.maximum_nodal_conductor_temperature_c > 20.0
    assert result.final_design_ready is False


def test_two_circuit_parallel_thermal_uses_all_physical_cables_and_nonuniform_losses() -> None:
    result = solve_multiconductor_thermal(_two_circuit_project(), mesh_scale=2.5, max_iterations=25, tolerance_c=0.05)
    region = result.regions[0]
    assert len(region.cables) == 12
    currents = [abs(item.current_a) for item in region.cables]
    assert max(currents) - min(currents) > 1.0
    losses = [item.conductor_loss_w_m for item in region.cables]
    assert max(losses) - min(losses) > 0.01
    assert region.nodal_cell_count > 0
    assert region.nodal_energy_balance_error_percent < 0.5


def test_real_xy_coordinates_change_analytical_and_nodal_results() -> None:
    compact = _two_circuit_project()
    spread = deepcopy(compact)
    for item in spread.installation_design.cross_sections[0].physical_cables:
        item.x_m *= 1.7
    a = solve_multiconductor_thermal(compact, mesh_scale=2.5, max_iterations=25, tolerance_c=0.05)
    b = solve_multiconductor_thermal(spread, mesh_scale=2.5, max_iterations=25, tolerance_c=0.05)
    assert b.maximum_analytical_conductor_temperature_c != pytest.approx(
        a.maximum_analytical_conductor_temperature_c, abs=0.02
    )
    assert b.maximum_nodal_conductor_temperature_c != pytest.approx(
        a.maximum_nodal_conductor_temperature_c, abs=0.02
    )


def test_external_heat_source_is_applied_at_real_coordinate() -> None:
    base = _two_circuit_project()
    heated = deepcopy(base)
    heated.installation_design.cross_sections[0].external_heat_sources = [
        ExternalHeatSourceData("HS-1", "Sıcak boru", 0.0, 1.25, 80.0, 0.08, True)
    ]
    cold_result = solve_multiconductor_thermal(base, mesh_scale=2.5, max_iterations=25, tolerance_c=0.05)
    hot_result = solve_multiconductor_thermal(heated, mesh_scale=2.5, max_iterations=25, tolerance_c=0.05)
    assert hot_result.maximum_nodal_conductor_temperature_c > cold_result.maximum_nodal_conductor_temperature_c
    assert hot_result.maximum_analytical_conductor_temperature_c > cold_result.maximum_analytical_conductor_temperature_c
    assert any(issue.code == "EXTERNAL_HEAT_SOURCE_INCLUDED" for issue in hot_result.issues)


def test_multiconductor_thermal_shadow_does_not_mutate_project() -> None:
    project = _two_circuit_project()
    before = deepcopy(project.to_dict())
    lambda_before = project.cable.sheath_loss_factor
    solve_multiconductor_thermal(project, mesh_scale=2.5, max_iterations=20, tolerance_c=0.08)
    assert project.to_dict() == before
    assert project.cable.sheath_loss_factor == lambda_before


def test_multiconductor_thermal_ui_contract_is_additive_and_shadow_only() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    dialog = (root / "src/ucd/ui/multiconductor_thermal_dialog.py").read_text(encoding="utf-8")
    window = (root / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    assert "Gerçek x-y Termal Gölge Çözümünü Çalıştır" in dialog
    assert "Fiziksel Kablo Kayıp/Sıcaklık" in dialog
    assert "SHADOW_COMPARE" in dialog
    assert "Gerçek x-y Çoklu Kablo Termal Gölge Çözümü" in window
