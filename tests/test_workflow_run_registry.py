from __future__ import annotations

from ucd.calculations.project_workflow import (
    STATUS_COMPLETE,
    STATUS_READY,
    STATUS_STALE,
    evaluate_project_workflow,
    record_engine_run,
)
from ucd.models.project import ProjectData


def test_defined_bonding_and_fault_inputs_are_ready_before_first_run() -> None:
    project = ProjectData()
    result = evaluate_project_workflow(project)
    assert result.stage("bonding").status == STATUS_READY
    assert result.stage("fault_epr").status == STATUS_READY
    assert any("motor çalıştırılabilir" in note for note in result.stage("fault_epr").notes)


def test_fault_run_record_completes_stage_and_survives_round_trip() -> None:
    project = ProjectData()
    record_engine_run(
        project,
        "fault_epr",
        STATUS_COMPLETE,
        result_count=len(project.fault_study.scenarios),
        message="Arıza/EPR sonucu üretildi.",
    )
    result = evaluate_project_workflow(project)
    assert result.stage("fault_epr").status == STATUS_COMPLETE
    assert any("Arıza/EPR sonucu üretildi" in note for note in result.stage("fault_epr").notes)

    loaded = ProjectData.from_dict(project.to_dict())
    loaded_result = evaluate_project_workflow(loaded)
    assert loaded_result.stage("fault_epr").status == STATUS_COMPLETE
    assert "fault_epr" in loaded.workflow.engine_runs


def test_fault_input_change_marks_completed_result_stale_with_reason() -> None:
    project = ProjectData()
    record_engine_run(project, "fault_epr", STATUS_COMPLETE, result_count=3)
    project.fault_study.scenarios[0].duration_s += 0.1

    stage = evaluate_project_workflow(project).stage("fault_epr")
    assert stage.status == STATUS_STALE
    assert any("arıza senaryosu veya topraklama girdileri" in note for note in stage.notes)


def test_thermal_stage_reports_changed_input_component_instead_of_bare_stale() -> None:
    project = ProjectData()
    record_engine_run(project, "iec60287", STATUS_COMPLETE, result_count=3)
    record_engine_run(project, "thermal_route", STATUS_COMPLETE, result_count=3)
    record_engine_run(project, "nodal", STATUS_COMPLETE, result_count=3)
    assert evaluate_project_workflow(project).stage("steady_thermal").status == STATUS_COMPLETE

    project.thermal_design.regions[0].overrides["phase_spacing_m"] = 0.25
    stage = evaluate_project_workflow(project).stage("steady_thermal")
    assert stage.status == STATUS_STALE
    assert any("termal bölge, kesit veya malzeme verileri" in note for note in stage.notes)


def test_blocked_run_does_not_keep_stage_blocked_after_inputs_change() -> None:
    project = ProjectData()
    record_engine_run(project, "fault_epr", "BLOCKED", warning_count=1, message="Eksik veri")
    project.fault_study.scenarios[0].duration_s += 0.2
    stage = evaluate_project_workflow(project).stage("fault_epr")
    assert stage.status == STATUS_READY
    assert any("yeniden çalıştırılabilir" in note for note in stage.notes)
