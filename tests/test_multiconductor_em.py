from __future__ import annotations

import numpy as np
import pytest

from ucd.calculations.installation import generate_standard_cross_section
from ucd.calculations.multiconductor_em import (
    SHEATH_OPEN,
    SHEATH_SOLID_BOTH_END,
    MulticonductorEMInputError,
    solve_multiconductor_em,
)
from ucd.models.project import InstallationDesignData, ProjectData


def _project_with_section(section):
    project = ProjectData()
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    return project


def test_single_cable_per_phase_preserves_phase_total_and_two_methods_agree() -> None:
    project = ProjectData()
    result = solve_multiconductor_em(project, sheath_mode=SHEATH_OPEN)
    assert result.core_count == 3
    assert len(result.conductor_order) == 6
    assert result.methods_agree
    assert result.maximum_method_current_difference_a < 1e-9
    assert result.direct.equation_residual < 1e-12
    assert result.direct.phase_constraint_residual_a < 1e-9
    assert all(item.current_sum_residual_a < 1e-9 for item in result.group_results)
    assert {round(abs(item.core_current_a), 6) for item in result.cable_results} == {800.0}


def test_two_circuit_two_parallel_arbitrary_xy_builds_24_conductor_matrix() -> None:
    section = generate_standard_cross_section(
        cross_section_id="ICS-N24",
        name="İki devre iki paralel",
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
    )
    # Prove the engine consumes user x-y rather than regenerating a preset.
    section.physical_cables[-1].x_m += 0.17
    section.physical_cables[-1].depth_m += 0.09
    project = _project_with_section(section)
    result = solve_multiconductor_em(project, sheath_mode=SHEATH_OPEN)
    assert result.core_count == 12
    assert len(result.conductor_order) == 24
    assert np.asarray(result.primitive_impedance_ohm_km).shape == (24, 24)
    assert len(result.group_results) == 6
    assert result.methods_agree
    assert max(item.current_sum_residual_a for item in result.group_results) < 1e-8
    targets = {item.group_id: round(abs(item.target_current_a), 6) for item in result.group_results}
    assert targets == {
        "C1:A": 900.0, "C1:B": 900.0, "C1:C": 900.0,
        "C2:A": 600.0, "C2:B": 600.0, "C2:C": 600.0,
    }


def test_parallel_current_sharing_is_solved_not_equal_share_projection() -> None:
    section = generate_standard_cross_section(
        cross_section_id="ICS-SHARE",
        name="Akım paylaşımı",
        arrangement="TREFOIL",
        circuit_count=1,
        parallel_cables_per_phase=2,
        circuit_load_currents_a=[1000.0],
        phase_spacing_m=0.20,
        parallel_group_spacing_m=0.80,
        burial_depth_m=1.20,
        outer_diameter_m=0.105,
    )
    # Deliberately distort one parallel conductor to amplify the physical effect.
    next(item for item in section.physical_cables if item.physical_cable_id == "C1-A-2").x_m += 1.50
    project = _project_with_section(section)
    result = solve_multiconductor_em(project, sheath_mode=SHEATH_OPEN)
    phase_a = [item for item in result.cable_results if item.phase == "A"]
    assert len(phase_a) == 2
    assert abs(sum((item.core_current_a for item in phase_a), 0j)) == pytest.approx(1000.0, rel=1e-9)
    assert abs(abs(phase_a[0].core_current_a) - abs(phase_a[1].core_current_a)) > 100.0
    assert result.maximum_equal_share_difference_a > 100.0
    assert result.maximum_current_imbalance_percent > 20.0


def test_solid_both_end_solves_sheath_currents_and_losses() -> None:
    project = ProjectData()
    open_result = solve_multiconductor_em(project, sheath_mode=SHEATH_OPEN)
    solid_result = solve_multiconductor_em(project, sheath_mode=SHEATH_SOLID_BOTH_END)
    assert open_result.total_sheath_loss_w_km == 0.0
    assert all(abs(item.sheath_current_a) == 0.0 for item in open_result.cable_results)
    assert solid_result.total_sheath_loss_w_km > 0.0
    assert solid_result.lambda1 > 0.0
    assert max(abs(item.sheath_current_a) for item in solid_result.cable_results) > 0.0
    assert solid_result.direct.sheath_voltage_residual_v_km < 1e-8
    assert solid_result.methods_agree


def test_general_primitive_matrix_is_complex_symmetric() -> None:
    section = generate_standard_cross_section(
        cross_section_id="ICS-MATRIX",
        name="Matrix",
        arrangement="DUCT_BANK",
        circuit_count=2,
        parallel_cables_per_phase=1,
        phase_orders=["ABC", "CBA"],
        circuit_load_currents_a=[700.0, 500.0],
        duct_rows=2,
        duct_columns=3,
        burial_depth_m=1.4,
        phase_spacing_m=0.22,
        outer_diameter_m=0.10,
    )
    result = solve_multiconductor_em(_project_with_section(section), sheath_mode=SHEATH_OPEN)
    matrix = np.asarray(result.primitive_impedance_ohm_km)
    assert matrix.shape == (12, 12)
    assert np.allclose(matrix, matrix.T)
    assert result.earth_equivalent_depth_m > 100.0


def test_current_override_is_not_silently_ignored() -> None:
    project = ProjectData()
    project.installation_design.cross_sections[0].physical_cables[0].current_override_a = 100.0
    with pytest.raises(MulticonductorEMInputError, match="override"):
        solve_multiconductor_em(project)


def test_shadow_result_does_not_mutate_project_or_lambda1() -> None:
    project = ProjectData()
    before = project.to_dict()
    lambda_before = project.cable.sheath_loss_factor
    result = solve_multiconductor_em(project)
    after = project.to_dict()
    assert result.final_design_ready is False
    assert project.cable.sheath_loss_factor == lambda_before
    assert before == after


def test_ui_exposes_n_conductor_shadow_without_replacing_bonding_action() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    source = (root / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    dialog = (root / "src/ucd/ui/multiconductor_em_dialog.py").read_text(encoding="utf-8")
    assert "Genel N-İletken EM Gölge Çözümü" in source
    assert "self.act_bonding" in source
    assert "SHADOW_COMPARE" in dialog
    assert "mevcut bonding/IEC/nodal sonuçlarını" in dialog


def test_optional_gcc_is_in_general_matrix_and_solution() -> None:
    project = ProjectData()
    project.bonding.gcc_enabled = True
    result = solve_multiconductor_em(project, sheath_mode=SHEATH_SOLID_BOTH_END)
    assert result.conductor_order[-1] == "GCC"
    assert len(result.conductor_order) == 7
    assert abs(result.gcc_current_a) > 0.0
    assert result.gcc_loss_w_km >= 0.0
    assert result.direct.gcc_current_a == result.gcc_current_a
    assert result.methods_agree
