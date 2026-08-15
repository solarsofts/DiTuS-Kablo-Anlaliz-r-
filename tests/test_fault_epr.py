from __future__ import annotations

from ucd.calculations.fault_epr import solve_fault_study, transfer_fault_tov_to_svl
from ucd.models.project import ProjectData


def test_fault_study_solves_three_default_scenarios_and_cim_nv_agree() -> None:
    project = ProjectData()
    result = solve_fault_study(
        project.cable, project.bonding, project.route_sections, project.fault_study
    )
    assert len(result.scenario_results) == 3
    assert result.all_methods_agree
    assert result.governing_tov_rms_v > 0
    assert result.maximum_sheath_current_a > 0


def test_single_phase_ground_fault_produces_epr_and_ground_current() -> None:
    project = ProjectData()
    result = solve_fault_study(
        project.cable, project.bonding, project.route_sections, project.fault_study
    )
    slg = next(item for item in result.scenario_results if item.scenario_id == "F-SLG")
    assert slg.maximum_epr_v > 0
    assert slg.maximum_earth_electrode_current_a > 0
    assert slg.maximum_sheath_current_a > 100
    assert slg.ground_points


def test_three_phase_and_phase_phase_faults_do_not_create_zero_sequence_epr_in_balanced_example() -> None:
    project = ProjectData()
    result = solve_fault_study(
        project.cable, project.bonding, project.route_sections, project.fault_study
    )
    three = next(item for item in result.scenario_results if item.scenario_id == "F-3PH")
    pp = next(item for item in result.scenario_results if item.scenario_id == "F-PP")
    slg = next(item for item in result.scenario_results if item.scenario_id == "F-SLG")
    assert three.maximum_epr_v < 1e-6
    assert pp.maximum_epr_v < 1e-6
    assert slg.maximum_epr_v > 1000


def test_fault_tov_transfer_updates_svl_duty_with_duration_multiplier() -> None:
    project = ProjectData()
    project.fault_study.tov_duration_multiplier = 2.0
    result = solve_fault_study(
        project.cable, project.bonding, project.route_sections, project.fault_study
    )
    voltage, duration = transfer_fault_tov_to_svl(project.fault_study, result, project.svl)
    assert voltage == result.governing_tov_rms_v
    assert duration == result.governing_duration_s * 2.0
    assert project.svl.fault_tov_rms_v == voltage


def test_gcc_changes_single_phase_ground_return_distribution() -> None:
    project = ProjectData()
    base = solve_fault_study(
        project.cable, project.bonding, project.route_sections, project.fault_study
    )
    base_slg = next(item for item in base.scenario_results if item.scenario_id == "F-SLG")
    project.bonding.gcc_enabled = True
    with_gcc = solve_fault_study(
        project.cable, project.bonding, project.route_sections, project.fault_study
    )
    gcc_slg = next(item for item in with_gcc.scenario_results if item.scenario_id == "F-SLG")
    assert gcc_slg.maximum_gcc_current_a > 0
    assert abs(gcc_slg.maximum_sheath_current_a - base_slg.maximum_sheath_current_a) > 1.0
