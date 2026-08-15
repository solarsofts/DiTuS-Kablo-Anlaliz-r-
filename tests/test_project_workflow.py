from __future__ import annotations

from ucd.calculations.project_workflow import (
    STATUS_BLOCKED,
    STATUS_COMPLETE,
    STATUS_CONDITIONAL,
    STATUS_MISSING_DATA,
    STATUS_READY,
    evaluate_project_workflow,
    workflow_stage_specs,
)
from ucd.models.project import ProjectData


def test_workflow_has_twelve_ordered_design_stages() -> None:
    specs = workflow_stage_specs()
    assert len(specs) == 12
    assert [item.number for item in specs] == list(range(1, 13))
    assert specs[0].stage_id == "system_load"
    assert specs[-1].stage_id == "deliverables"
    assert specs[5].engines == (
        "IEC 60287",
        "2D nodal kararlı durum",
        "Bölgesel termal optimizasyon",
    )


def test_default_project_recommends_verified_system_and_load_input() -> None:
    project = ProjectData()
    result = evaluate_project_workflow(project)
    system = result.stage("system_load")
    assert system.status == STATUS_MISSING_DATA
    assert result.recommended_stage_id == "system_load"
    assert any("doğrulanmış sistem/yük" in item for item in system.missing_inputs)


def test_missing_route_blocks_later_iteration_without_mutating_project() -> None:
    project = ProjectData()
    project.design_progress.system_load = "COMPLETE"
    project.route_sections = []
    before = project.to_dict()
    result = evaluate_project_workflow(project)
    assert result.stage("route").status == STATUS_MISSING_DATA
    assert result.stage("iteration").status == STATUS_BLOCKED
    after = project.to_dict()
    # to_dict timestamps change; the workflow evaluator itself must not alter the
    # project data model or add synthetic route/cable records.
    assert before["route_sections"] == after["route_sections"] == []
    assert before["cable"]["name"] == after["cable"]["name"]


def test_runtime_results_drive_engine_stages_without_persisted_fake_results() -> None:
    project = ProjectData()
    project.design_progress.system_load = "COMPLETE"
    project.design_progress.route = "COMPLETE"
    project.design_progress.cable = "COMPLETE"
    project.cable_application.applied_snapshot_hash = "abc123"
    project.cable_application.application_status = "APPLIED"
    runtime = {
        "iec60287": True,
        "thermal_route": True,
        "nodal": True,
        "bonding": True,
        "fault_epr": True,
        "svl": True,
        "transient": True,
    }
    result = evaluate_project_workflow(project, runtime)
    assert result.stage("steady_thermal").status == STATUS_COMPLETE
    assert result.stage("bonding").status == STATUS_COMPLETE
    assert result.stage("fault_epr").status == STATUS_COMPLETE
    assert result.stage("svl").status == STATUS_COMPLETE
    assert result.stage("transient").status == STATUS_COMPLETE
    assert project.design_progress.thermal == "NOT_RUN"


def test_low_reliability_thermal_materials_are_explicitly_conditional() -> None:
    project = ProjectData()
    project.design_progress.system_load = "COMPLETE"
    result = evaluate_project_workflow(project)
    installation = result.stage("installation")
    assert installation.status == STATUS_CONDITIONAL
    assert any("düşük güvenli" in note for note in installation.notes)


def test_workflow_position_round_trip_and_legacy_default() -> None:
    project = ProjectData()
    project.workflow.current_stage_id = "bonding"
    loaded = ProjectData.from_dict(project.to_dict())
    assert loaded.schema_version == "0.16.4"
    assert loaded.workflow.current_stage_id == "bonding"

    legacy = ProjectData.from_dict({"schema_version": "0.16.1", "project_name": "Legacy"})
    assert legacy.schema_version == "0.16.4"
    assert legacy.workflow.current_stage_id == "system_load"


def test_mascot_asset_is_packaged_as_rgba_png() -> None:
    import struct
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    asset = root / "assets" / "ditus_mascot.png"
    raw = asset.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    width, height, bit_depth, color_type = struct.unpack(">IIBB", raw[16:26])
    assert (width, height) == (512, 512)
    assert bit_depth == 8
    assert color_type == 6  # RGBA


def test_not_run_runtime_does_not_hide_ready_precheck() -> None:
    project = ProjectData()
    project.cable.design_current_a = 120.0
    project.cable.conductor_area_mm2 = 400.0
    project.cable_application.last_iteration_status = "NOT_RUN"
    result = evaluate_project_workflow(project, {"precheck": "NOT_RUN"})
    assert result.stage("precheck").status == STATUS_READY


def test_passed_first_iteration_completes_precheck_stage() -> None:
    project = ProjectData()
    project.cable.design_current_a = 120.0
    project.cable.conductor_area_mm2 = 400.0
    project.cable_application.last_iteration_status = "PASS"
    result = evaluate_project_workflow(project, {"precheck": "PASS"})
    assert result.stage("precheck").status == STATUS_COMPLETE
