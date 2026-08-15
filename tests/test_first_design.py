from math import isclose, sqrt

import pytest

from ucd.calculations.first_design import (
    FirstDesignInputError,
    apply_candidate_to_project,
    apply_load_calculation,
    calculate_load_basis,
    generate_generic_candidates,
    suggest_voltage_class,
)
from ucd.models.project import (
    DesignBasisData,
    LOAD_MODE_ACTIVE_POWER,
    LOAD_MODE_APPARENT_POWER,
    LOAD_MODE_DIRECT_CURRENT,
    ProjectData,
)


def test_mva_load_calculation_and_n1_are_separate() -> None:
    basis = DesignBasisData(
        system_voltage_kv=154.0,
        circuit_count=2,
        active_circuit_count=2,
        n_minus_one_enabled=True,
        load_input_mode=LOAD_MODE_APPARENT_POWER,
        apparent_power_mva=200.0,
        design_margin_percent=10.0,
    )
    result = calculate_load_basis(basis)
    expected_total = 200e6 / (sqrt(3) * 154e3)
    assert isclose(result.normal_total_current_a, expected_total, rel_tol=1e-12)
    assert isclose(result.normal_current_per_active_circuit_a, expected_total / 2, rel_tol=1e-12)
    assert isclose(result.n1_current_per_circuit_a, expected_total, rel_tol=1e-12)
    assert isclose(result.design_current_per_circuit_a, expected_total * 1.10, rel_tol=1e-12)


def test_active_power_requires_power_factor() -> None:
    basis = DesignBasisData(load_input_mode=LOAD_MODE_ACTIVE_POWER, active_power_mw=100.0, power_factor=0.0)
    with pytest.raises(FirstDesignInputError):
        calculate_load_basis(basis)


def test_direct_current_mode_preserves_user_current() -> None:
    basis = DesignBasisData(load_input_mode=LOAD_MODE_DIRECT_CURRENT, direct_current_a=875.0, design_margin_percent=0.0)
    result = apply_load_calculation(basis)
    assert result.normal_total_current_a == 875.0
    assert basis.design_current_per_circuit_a == 875.0


def test_voltage_class_initial_suggestion() -> None:
    assert suggest_voltage_class(154.0) == "87/150 (170) kV"
    assert suggest_voltage_class(33.0) == "20.3/35 (40.5) kV"


def test_generic_candidates_cover_target_and_are_preliminary() -> None:
    basis = DesignBasisData(
        load_input_mode=LOAD_MODE_DIRECT_CURRENT,
        direct_current_a=850.0,
        design_margin_percent=0.0,
        installation_profile="DIRECT_BURIED_TREFOIL",
        conductor_preference="AUTO",
    )
    candidates = generate_generic_candidates(basis)
    assert 1 <= len(candidates) <= 5
    assert any(c.estimated_ampacity_a >= basis.design_current_per_circuit_a for c in candidates)
    assert all(c.maturity_level == "L1_PRELIMINARY_SCREENING" for c in candidates)
    assert all(any("Jenerik" in note for note in c.notes) for c in candidates)


def test_candidate_applies_as_snapshot_to_current_project() -> None:
    project = ProjectData()
    project.design_basis.load_input_mode = LOAD_MODE_DIRECT_CURRENT
    project.design_basis.direct_current_a = 800.0
    project.design_basis.design_margin_percent = 0.0
    candidates = generate_generic_candidates(project.design_basis)
    candidate = candidates[0]
    apply_candidate_to_project(candidate, project.design_basis, project.cable)
    assert project.cable.conductor_area_mm2 == candidate.conductor_area_mm2
    assert project.cable.conductor_material == candidate.conductor_material
    assert project.design_basis.selected_candidate_id == candidate.candidate_id


def test_design_basis_and_progress_round_trip() -> None:
    project = ProjectData()
    project.design_basis.apparent_power_mva = 275.0
    project.design_progress.maturity_level = "L3_BONDING_SHEATH"
    project.design_progress.missing_data = ["Arıza akımı"]
    generate_generic_candidates(project.design_basis)
    loaded = ProjectData.from_dict(project.to_dict())
    assert loaded.schema_version == "0.16.4"
    assert loaded.design_basis.apparent_power_mva == 275.0
    assert loaded.design_basis.candidates
    assert loaded.design_progress.maturity_level == "L3_BONDING_SHEATH"
    assert loaded.design_progress.missing_data == ["Arıza akımı"]


def test_first_single_cable_candidate_runs_existing_iec_and_bonding_stack() -> None:
    from ucd.calculations import solve_bonding, solve_project, solve_project_thermal

    project = ProjectData()
    candidate = generate_generic_candidates(project.design_basis)[0]
    assert candidate.cables_per_phase == 1
    apply_candidate_to_project(candidate, project.design_basis, project.cable)
    thermal = solve_project_thermal(project.cable, project.route_sections)
    bonding = solve_bonding(project.cable, project.bonding, project.route_sections)
    project.cable.sheath_loss_factor = bonding.lambda1
    iec = solve_project(project.cable, project.route_sections)
    assert thermal
    assert bonding.max_standing_voltage_v >= 0.0
    assert min(item.ampacity_a for item in iec) > 0.0


def test_parallel_generic_screening_has_no_hidden_point_nine_derating() -> None:
    basis = DesignBasisData()
    basis.system_voltage_kv = 34.5
    basis.load_input_mode = LOAD_MODE_DIRECT_CURRENT
    basis.direct_current_a = 300.0
    basis.active_circuit_count = 1
    basis.circuit_count = 1
    basis.design_margin_percent = 0.0
    basis.future_growth_percent = 0.0
    basis.installation_profile = "DIRECT_BURIED_TREFOIL"
    basis.conductor_preference = "AL"
    basis.cables_per_phase_preference = "2"
    candidates = generate_generic_candidates(basis, maximum_candidates=3)
    assert candidates
    candidate = candidates[0]
    assert candidate.cables_per_phase == 2
    expected = candidate.conductor_area_mm2 * 0.58 * 2.0
    assert abs(candidate.estimated_ampacity_a - expected) < 1e-9
    assert candidate.status == "GRUPLAMA_DOGRULAMASI_GEREKLI"
    assert any("grouping/derating uygulanmadı" in note for note in candidate.notes)
