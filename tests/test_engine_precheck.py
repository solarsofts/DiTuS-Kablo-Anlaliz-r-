from __future__ import annotations

from ucd.calculations.engine_precheck import (
    PRECHECK_BLOCKED,
    PRECHECK_CONDITIONAL,
    evaluate_engine_precheck,
)
from ucd.calculations.project_workflow import (
    STATUS_COMPLETE,
    evaluate_project_workflow,
    record_engine_run,
)
from ucd.models.project import ProjectData


def test_bonding_precheck_preserves_ieee_cigre_method_and_allows_conditional_run() -> None:
    project = ProjectData()
    result = evaluate_engine_precheck(project, "bonding")
    assert result.can_run
    assert result.status == PRECHECK_CONDITIONAL
    assert "CIGRE TB 797" in result.method.display_name
    assert any("SIMPLIFIED_CARSON" in item for item in result.assumptions)


def test_bonding_hard_gate_blocks_without_screen_electrical_path() -> None:
    project = ProjectData()
    project.cable.sheath_cross_section_mm2 = 0.0
    project.cable.sheath_dc_resistance_20_ohm_km = 0.0
    project.cable.sheath_mean_diameter_mm = 0.0
    result = evaluate_engine_precheck(project, "bonding")
    assert not result.can_run
    assert result.status == PRECHECK_BLOCKED
    assert any(item.item_id == "screen_electrical" for item in result.hard_missing)


def test_nodal_can_run_as_conditional_front_end_model() -> None:
    project = ProjectData()
    result = evaluate_engine_precheck(project, "nodal")
    assert result.can_run
    assert result.status == PRECHECK_CONDITIONAL
    assert result.method.stage_id == "steady_thermal"


def test_svl_is_hard_blocked_until_fault_tov_is_available() -> None:
    project = ProjectData()
    project.svl.fault_tov_rms_v = 0.0
    project.svl.fault_tov_duration_s = 0.0
    result = evaluate_engine_precheck(project, "svl")
    assert result.status == PRECHECK_BLOCKED
    labels = {item.label for item in result.hard_missing}
    assert "Arıza TOV görevi" in labels
    assert "TOV süresi" in labels


def test_workflow_exposes_run_freshness_and_maturity_separately() -> None:
    project = ProjectData()
    precheck = evaluate_engine_precheck(project, "bonding")
    record_engine_run(
        project,
        "bonding",
        STATUS_COMPLETE,
        result_count=1,
        precheck=precheck.to_dict(),
    )
    workflow = evaluate_project_workflow(project)
    stage = workflow.stage("bonding")
    assert stage.run_status == "SUCCESS"
    assert stage.freshness == "CURRENT"
    assert stage.maturity == "CONDITIONAL"

    project.cable.sheath_cross_section_mm2 += 1.0
    changed = evaluate_project_workflow(project).stage("bonding")
    assert changed.freshness == "STALE"


def test_main_calculation_entry_points_call_common_precheck() -> None:
    from pathlib import Path

    source = (Path(__file__).parents[1] / "src" / "ucd" / "ui" / "main_window.py").read_text(encoding="utf-8")
    for engine_id in ("precheck", "thermal_route", "nodal", "bonding", "fault_epr", "svl", "transient", "iteration"):
        assert f'_confirm_engine_precheck("{engine_id}")' in source
