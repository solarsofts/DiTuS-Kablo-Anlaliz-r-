from __future__ import annotations

from copy import deepcopy

import pytest

from ucd.calculations.electrothermal_coupled import (
    COUPLING_MODE,
    solve_electrothermal_ampacity,
    solve_electrothermal_coupled,
)
from ucd.calculations.installation import generate_standard_cross_section
from ucd.calculations.multiconductor_global_network import solve_global_multiconductor_network
from ucd.models.project import (
    InstallationDesignData,
    ProjectData,
    RouteSection,
    ThermalRegion,
    default_bonding_system,
)


def _two_circuit_project() -> ProjectData:
    project = ProjectData()
    section = generate_standard_cross_section(
        cross_section_id="ICS-ET-CLOSED",
        name="İki devre iki paralel kapalı çevrim",
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
        region_ids=["TR-ET-CLOSED"],
    )
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    project.route_sections = [RouteSection("R-ET-CLOSED", 300.0, thermal_region_id="TR-ET-CLOSED")]
    project.thermal_design.route_length_m = 300.0
    project.thermal_design.regions = [
        ThermalRegion(
            "TR-ET-CLOSED",
            "Kapalı çevrim bölgesi",
            0.0,
            300.0,
            project.thermal_design.templates[0].template_id,
        )
    ]
    project.bonding = default_bonding_system(300.0)
    return project


def test_default_closed_loop_converges_with_all_gates() -> None:
    result = solve_electrothermal_coupled(
        ProjectData(),
        mesh_scale=2.5,
        maximum_iterations=15,
        temperature_tolerance_c=0.08,
    )
    assert result.coupling_mode == COUPLING_MODE
    assert result.converged
    assert 2 <= result.iteration_count <= 15
    last = result.iterations[-1]
    assert last.maximum_temperature_residual_c <= result.temperature_tolerance_c
    assert last.maximum_core_current_change_percent <= result.current_tolerance_percent
    assert last.maximum_sheath_current_change_percent <= result.current_tolerance_percent
    assert last.active_loss_change_percent <= result.loss_tolerance_percent
    assert last.em_methods_agree
    assert last.thermal_regions_converged
    assert result.final_design_ready is False


def test_two_circuit_closed_loop_keeps_global_unequal_current_sharing() -> None:
    result = solve_electrothermal_coupled(
        _two_circuit_project(),
        mesh_scale=3.0,
        maximum_iterations=15,
        temperature_tolerance_c=0.10,
    )
    assert result.converged
    assert len(result.final_global_em.core_results) == 12
    assert result.final_global_em.maximum_core_current_imbalance_percent > 1.0
    assert result.final_global_em.total_sheath_metal_loss_w > 0.0
    assert result.final_thermal.maximum_nodal_conductor_temperature_c > 20.0


def test_temperature_feedback_changes_global_resistance_loss_state() -> None:
    project = _two_circuit_project()
    section = project.installation_design.cross_sections[0]
    cold = {
        section.cross_section_id: {
            item.physical_cable_id: 25.0 for item in section.physical_cables if item.active
        }
    }
    hot = {
        section.cross_section_id: {
            item.physical_cable_id: 85.0 for item in section.physical_cables if item.active
        }
    }
    cold_result = solve_global_multiconductor_network(
        project,
        core_temperatures_c_by_cross_section=cold,
        sheath_temperatures_c_by_cross_section=cold,
        gcc_temperature_c=25.0,
    )
    hot_result = solve_global_multiconductor_network(
        project,
        core_temperatures_c_by_cross_section=hot,
        sheath_temperatures_c_by_cross_section=hot,
        gcc_temperature_c=85.0,
    )
    assert hot_result.total_core_metal_loss_w > cold_result.total_core_metal_loss_w
    assert hot_result.matrix_blocks[0].unknown_metallic_resistance_ohm[0] > (
        cold_result.matrix_blocks[0].unknown_metallic_resistance_ohm[0]
    )
    assert hot_result.total_sheath_metal_loss_w != pytest.approx(cold_result.total_sheath_metal_loss_w)
    assert any(issue.code == "TEMPERATURE_DEPENDENT_RESISTANCE_ACTIVE" for issue in hot_result.issues)



def test_closed_loop_ampacity_finds_temperature_limited_common_factor() -> None:
    result = solve_electrothermal_ampacity(
        ProjectData(),
        mesh_scale=3.0,
        maximum_closed_loop_iterations=15,
        maximum_rating_iterations=10,
        temperature_tolerance_c=0.30,
        current_tolerance_a=6.0,
    )
    assert result.converged
    assert result.rating_factor > 0.0
    assert result.circuit_rating_currents_a["C1"] > 0.0
    assert abs(
        result.final_coupled_result.final_thermal.maximum_nodal_conductor_temperature_c
        - result.temperature_limit_c
    ) < 1.0
    assert result.final_design_ready is False

def test_closed_loop_shadow_does_not_mutate_project_or_lambda1() -> None:
    project = _two_circuit_project()
    before = deepcopy(project.to_dict())
    lambda_before = project.cable.sheath_loss_factor
    solve_electrothermal_coupled(
        project,
        mesh_scale=3.0,
        maximum_iterations=12,
        temperature_tolerance_c=0.12,
    )
    assert project.to_dict() == before
    assert project.cable.sheath_loss_factor == lambda_before


def test_closed_loop_ui_contract_is_additive_and_shadow_only() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    dialog = (root / "src/ucd/ui/electrothermal_coupled_dialog.py").read_text(encoding="utf-8")
    window = (root / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    assert "Elektro-Termal Kapalı Çevrimi Çalıştır" in dialog
    assert "Yakınsama İzi" in dialog
    assert "Kapalı Çevrim Ampacity Gölge Çözümü" in dialog
    assert "SHADOW_COMPARE" in dialog
    assert "Elektro-Termal Kapalı Çevrim Gölge Çözümü" in window
