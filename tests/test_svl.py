from __future__ import annotations

from ucd.calculations.svl import solve_svl_selection
from ucd.models.project import ProjectData, SvlCandidate


def _candidate() -> SvlCandidate:
    return SvlCandidate(
        candidate_id="C1",
        manufacturer="Test",
        model="MOV-3",
        mcov_rms_v=3000.0,
        tov_1s_rms_v=4200.0,
        tov_10s_rms_v=3600.0,
        tov_100s_rms_v=3300.0,
        residual_voltage_peak_v=9000.0,
        energy_capacity_kj=20.0,
        nominal_discharge_current_ka=10.0,
        source="TEST",
    )


def test_complete_svl_candidate_can_pass_all_checks() -> None:
    project = ProjectData()
    project.svl.candidates = [_candidate()]
    project.svl.fault_tov_rms_v = 3500.0
    project.svl.fault_tov_duration_s = 10.0
    project.svl.required_energy_kj = 10.0
    project.svl.required_discharge_current_ka = 5.0
    project.svl.current_rise_ka_per_us = 0.5
    project.svl.lead_inductance_uh_per_m = 0.2
    project.svl.joint_interrupt_impulse_withstand_peak_v = 60000.0
    project.svl.jacket_impulse_withstand_peak_v = 30000.0
    project.svl.maximum_protective_level_fraction = 0.75
    for box in project.bonding.link_boxes:
        box.lead_length_m = 3.0
    result = solve_svl_selection(project.svl, project.bonding, 150.0)
    assert result.recommended_candidate_id == "C1"
    assert result.checks[0].status == "PASS"
    assert result.checks[0].lead_inductive_drop_peak_v == 300.0


def test_missing_fault_and_emt_inputs_produce_conditional_not_false_pass() -> None:
    project = ProjectData()
    project.svl.candidates = [_candidate()]
    result = solve_svl_selection(project.svl, project.bonding, 150.0)
    check = result.checks[0]
    assert check.status == "CONDITIONAL"
    assert check.pending_checks
    assert result.recommended_candidate_id == "C1"


def test_mcov_failure_eliminates_candidate() -> None:
    project = ProjectData()
    weak = _candidate()
    weak.mcov_rms_v = 100.0
    project.svl.candidates = [weak]
    result = solve_svl_selection(project.svl, project.bonding, 150.0)
    assert result.checks[0].status == "FAIL"
    assert not result.has_recommendation


def test_tov_log_time_interpolation_and_failure() -> None:
    project = ProjectData()
    candidate = _candidate()
    project.svl.candidates = [candidate]
    project.svl.fault_tov_rms_v = 4000.0
    project.svl.fault_tov_duration_s = 10.0
    result = solve_svl_selection(project.svl, project.bonding, 150.0)
    assert result.checks[0].tov_withstand_rms_v == 3600.0
    assert result.checks[0].tov_ok is False
    assert result.checks[0].status == "FAIL"


def test_longer_lead_increases_protective_level() -> None:
    project = ProjectData()
    project.svl.candidates = [_candidate()]
    project.svl.current_rise_ka_per_us = 1.0
    project.svl.lead_inductance_uh_per_m = 1.0
    for box in project.bonding.link_boxes:
        box.lead_length_m = 3.0
    short = solve_svl_selection(project.svl, project.bonding, 150.0)
    for box in project.bonding.link_boxes:
        box.lead_length_m = 10.0
    long = solve_svl_selection(project.svl, project.bonding, 150.0)
    assert long.checks[0].lead_inductive_drop_peak_v > short.checks[0].lead_inductive_drop_peak_v
    assert long.checks[0].protective_level_peak_v > short.checks[0].protective_level_peak_v
