from __future__ import annotations

from copy import deepcopy

import pytest

from ucd.calculations.installation import generate_standard_cross_section
from ucd.calculations.multiconductor_bonding_network import solve_multiconductor_bonding_network
from ucd.calculations.multiconductor_global_network import (
    CORE_SHARING_MODE,
    solve_global_multiconductor_network,
)
from ucd.models.project import (
    InstallationDesignData,
    ProjectData,
    RouteSection,
    default_bonding_system,
)


def _two_circuit_project() -> ProjectData:
    project = ProjectData()
    section = generate_standard_cross_section(
        cross_section_id="ICS-GLOBAL",
        name="İki devre iki paralel global ağ",
        arrangement="FLAT",
        circuit_count=2,
        parallel_cables_per_phase=2,
        phase_orders=["ABC", "CBA"],
        circuit_load_currents_a=[900.0, 600.0],
        phase_spacing_m=0.25,
        circuit_spacing_m=1.60,
        parallel_group_spacing_m=0.80,
        burial_depth_m=1.25,
        outer_diameter_m=0.105,
        region_ids=["TR-GLOBAL"],
    )
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    project.route_sections = [RouteSection("R-GLOBAL", 300.0, thermal_region_id="TR-GLOBAL")]
    project.bonding = default_bonding_system(300.0)
    return project


def test_default_global_network_solves_core_and_sheath_by_two_methods() -> None:
    result = solve_global_multiconductor_network(ProjectData())
    assert result.core_sharing_mode == CORE_SHARING_MODE
    assert result.methods_agree
    assert len(result.core_results) == 3
    assert len(result.section_results) == 3
    assert result.direct.phase_constraint_residual_a < 1e-9
    assert result.direct.sheath_kcl_residual_a < 1e-9
    assert result.direct.sheath_branch_residual_v < 1e-8
    assert result.direct.core_voltage_residual_v < 1e-8
    assert result.maximum_method_core_current_difference_a < 1e-8
    assert result.maximum_method_sheath_current_difference_a < 1e-8
    assert result.final_design_ready is False


def test_single_parallel_global_solution_matches_locked_section_local_network() -> None:
    project = ProjectData()
    global_result = solve_global_multiconductor_network(project)
    locked = solve_multiconductor_bonding_network(project)
    assert global_result.maximum_sheath_current_a == pytest.approx(
        locked.maximum_sheath_current_a, rel=1e-10, abs=1e-10
    )
    assert global_result.maximum_sheath_to_earth_voltage_v == pytest.approx(
        locked.maximum_sheath_to_earth_voltage_v, rel=1e-10, abs=1e-10
    )
    assert global_result.total_sheath_metal_loss_w == pytest.approx(
        locked.total_sheath_metal_loss_w, rel=1e-10, abs=1e-10
    )


def test_two_circuit_parallel_currents_are_global_and_sum_to_terminal_targets() -> None:
    result = solve_global_multiconductor_network(_two_circuit_project())
    assert result.methods_agree
    assert len(result.core_results) == 12
    assert len(result.group_results) == 6
    assert all(item.current_sum_residual_a < 1e-8 for item in result.group_results)
    assert result.maximum_core_current_imbalance_percent > 1.0
    keys = [item.key for item in result.core_results]
    assert len(keys) == len(set(keys))
    assert all(item.core_metal_loss_w > 0.0 for item in result.core_results)


def test_global_solution_uses_one_route_current_per_physical_core() -> None:
    result = solve_global_multiconductor_network(_two_circuit_project())
    core_by_key = {item.key: item.core_current_a for item in result.core_results}
    assert len(core_by_key) == 12
    # Every minor section reports sheath results against the same canonical core set.
    for section in result.section_results:
        assert {item.key for item in section.sheath_results} == set(core_by_key)


def test_global_shadow_does_not_mutate_project_or_lambda1() -> None:
    project = _two_circuit_project()
    before = deepcopy(project.to_dict())
    lambda_before = project.cable.sheath_loss_factor
    result = solve_global_multiconductor_network(project)
    assert result.lambda1 > 0.0
    assert project.cable.sheath_loss_factor == lambda_before
    assert project.to_dict() == before


def test_global_ui_contract_is_additive_and_shadow_only() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    dialog = (root / "src/ucd/ui/multiconductor_em_dialog.py").read_text(encoding="utf-8")
    assert "Global Core + Bonding Çözümünü Çalıştır" in dialog
    assert "Global · Core Sürekliliği" in dialog
    assert "solve_global_multiconductor_network" in dialog
    assert "SHADOW_COMPARE" in dialog
