from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ucd.calculations.cable_library import cable_snapshot_hash, merge_builtin_catalogs
from ucd.calculations.project_application import (
    apply_catalog_candidate_to_project,
    assess_cable_completion,
    calculate_project_voltage_drop,
    evaluate_application_iteration_gates,
    resolve_source_conflict,
)
from ucd.models.project import (
    CONFLICT_CREATE_SCENARIOS,
    CONFLICT_USE_SOURCE,
    ProjectData,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _synthetic(name: str = "synthetic_20km_audit_case.ucd.json") -> ProjectData:
    project = ProjectData.from_dict(json.loads((EXAMPLES / name).read_text(encoding="utf-8")))
    merge_builtin_catalogs(project.cable_library)
    return project


def _apply_catalog(project: ProjectData, parallel: int = 1):
    return apply_catalog_candidate_to_project(
        project,
        "SYN-MFR-A-MV40K5-AL400-35",
        f"SYN-MFR-A-MV40K5-AL400-35::P{parallel}",
        parallel,
        [section.name for section in project.route_sections],
    )


def test_catalog_candidate_applies_as_hash_valid_project_snapshot() -> None:
    project = _synthetic()
    result = _apply_catalog(project)
    assert result.snapshot_id.startswith("SNAP-")
    assert project.cable.snapshot_hash == cable_snapshot_hash(project.cable)
    assert project.cable.catalog_record_id == "SYN-MFR-A-MV40K5-AL400-35"
    assert project.cable.design_current_a == pytest.approx(project.design_basis.design_current_per_circuit_a)
    assert project.cable_application.application_status == "APPLIED_CONDITIONAL"
    assert all(item.active for item in project.cable_application.assignments)


def test_application_snapshot_is_independent_from_catalog_record_mutation() -> None:
    project = _synthetic()
    _apply_catalog(project)
    before = deepcopy(project.cable)
    record = next(item for item in project.cable_library.records if item.record_id == project.cable.catalog_record_id)
    record.catalog_electrical["conductor_rdc20_ohm_km"] = 999.0
    assert project.cable.dc_resistance_20_ohm_km == before.dc_resistance_20_ohm_km
    assert project.cable.snapshot_hash == before.snapshot_hash


def test_completion_matrix_does_not_invent_screen_wire_geometry() -> None:
    project = _synthetic()
    _apply_catalog(project)
    report = assess_cable_completion(project)
    by_key = {item.parameter_key: item for item in report.items}
    assert by_key["rdc20"].status == "CATALOG_AVAILABLE"
    assert by_key["overall_diameter"].status == "CATALOG_AVAILABLE"
    assert by_key["screen_wire_geometry"].status == "ENGINEERING_ASSUMPTION"
    assert "Ø" in by_key["screen_wire_geometry"].value
    assert by_key["heat_capacity"].status == "MANUFACTURER_CONFIRMATION_REQUIRED"
    assert report.status == "CONDITIONAL"


def test_route_assignment_can_limit_active_sections() -> None:
    project = _synthetic("synthetic_20km_line.ucd.json")
    first = project.route_sections[0].name
    apply_catalog_candidate_to_project(
        project, "SYN-MFR-A-MV40K5-AL400-35", route_section_names=[first]
    )
    active = [item.route_section_name for item in project.cable_application.assignments if item.active]
    inactive = [item.route_section_name for item in project.cable_application.assignments if not item.active]
    assert active == [first]
    assert len(inactive) == len(project.route_sections) - 1


def test_synthetic_conflict_decision_is_persistent() -> None:
    project = _synthetic()
    decision = resolve_source_conflict(
        project,
        "SYN-PF-CONFLICT",
        CONFLICT_USE_SOURCE,
        ["SYN-PF-B"],
        rationale="Sentetik kontrol değeri seçildi.",
    )
    assert decision.selected_record_ids == ["SYN-PF-B"]
    assert project.design_basis.power_factor == pytest.approx(0.92)
    loaded = ProjectData.from_dict(project.to_dict())
    assert loaded.cable_application.conflict_decisions[0].conflict_id == "SYN-PF-CONFLICT"
    assert loaded.cable_application.conflict_decisions[0].action == CONFLICT_USE_SOURCE


def test_iteration_gate_blocks_unresolved_high_conflicts() -> None:
    project = _synthetic()
    _apply_catalog(project)
    summary = evaluate_application_iteration_gates(project)
    assert summary.status == "BLOCKED"
    source_gate = next(item for item in summary.gates if item.gate_id == "SOURCE_CONFLICTS")
    assert source_gate.status == "BLOCKED"


def test_iteration_gate_becomes_conditional_after_synthetic_conflict_is_decided() -> None:
    project = _synthetic()
    _apply_catalog(project)
    for conflict in project.source_audit.conflicts:
        resolve_source_conflict(
            project,
            conflict.conflict_id,
            CONFLICT_CREATE_SCENARIOS,
            conflict.record_ids,
            rationale="Sentetik değerler ayrı kontrol senaryolarında korunacak.",
        )
    summary = evaluate_application_iteration_gates(project)
    assert summary.status == "CONDITIONAL_READY"
    assert summary.voltage_drop is not None
    assert summary.voltage_drop.voltage_drop_percent > 0


def test_voltage_drop_scales_with_synthetic_route_length() -> None:
    full = _synthetic("synthetic_20km_line.ucd.json")
    half = deepcopy(full)
    _apply_catalog(full)
    _apply_catalog(half)
    for section in half.route_sections:
        section.length_m *= 0.5
    half.design_basis.total_route_length_m = 10_000.0
    half.thermal_design.route_length_m = 10_000.0
    full_result = calculate_project_voltage_drop(full)
    half_result = calculate_project_voltage_drop(half)
    assert full_result.length_m == pytest.approx(20_000.0)
    assert half_result.length_m == pytest.approx(10_000.0)
    assert full_result.voltage_drop_percent / half_result.voltage_drop_percent == pytest.approx(2.0)


def test_application_data_round_trip_preserves_assignments_and_completion() -> None:
    project = _synthetic("synthetic_20km_line.ucd.json")
    _apply_catalog(project)
    loaded = ProjectData.from_dict(project.to_dict())
    assert loaded.schema_version == "0.16.4"
    assert loaded.cable_application.applied_snapshot_id == project.cable.snapshot_id
    assert len(loaded.cable_application.assignments) == len(project.route_sections)
    assert len(loaded.cable_application.completion_items) >= 10


def test_packaged_synthetic_application_results_are_stable() -> None:
    expected = json.loads((EXAMPLES / "synthetic_20km_application_expected.json").read_text(encoding="utf-8"))
    assert expected["scope"] == "UNDERGROUND_ONLY"
    assert len(expected["results"]) == 3
    assert all(item["route_length_m"] == pytest.approx(20_000.0) for item in expected["results"])
    assert all(item["iteration_gate_status"] in {"CONDITIONAL_READY", "BLOCKED"} for item in expected["results"])
