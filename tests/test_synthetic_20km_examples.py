from __future__ import annotations

import json
from pathlib import Path

import pytest

from ucd.calculations import (
    audit_project_sources,
    materialize_route_sections,
    solve_bonding,
    solve_project,
    solve_thermal_route,
)
from ucd.models.project import ProjectData


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _load(name: str) -> ProjectData:
    return ProjectData.from_dict(json.loads((EXAMPLES / name).read_text(encoding="utf-8")))


def test_regression_manifest_contains_only_synthetic_20km_cases() -> None:
    manifest = json.loads((EXAMPLES / "synthetic_20km_regression_suite.json").read_text(encoding="utf-8"))
    assert manifest["scope"] == "UNDERGROUND_ONLY"
    assert manifest["source_type"] == "GENERATED_SYNTHETIC_DATA"
    assert len(manifest["cases"]) == 3
    assert all(item["route_length_m"] == pytest.approx(20_000.0) for item in manifest["cases"])
    assert all(item["project_file"].startswith("synthetic_20km_") for item in manifest["cases"])


def test_primary_example_is_exactly_20km_and_two_circuits() -> None:
    project = _load("synthetic_20km_line.ucd.json")
    assert project.design_basis.total_route_length_m == pytest.approx(20_000.0)
    assert sum(section.length_m for section in project.route_sections) == pytest.approx(20_000.0)
    assert project.design_basis.circuit_count == 2
    assert project.design_basis.active_circuit_count == 2
    assert "sentetik" in project.description.lower()


def test_synthetic_audit_case_is_explicitly_non_external() -> None:
    project = _load("synthetic_20km_audit_case.ucd.json")
    report = audit_project_sources(project)
    assert report.status == "HIGH_CONFLICTS"
    assert report.high_count == 1
    assert project.source_audit.source_file == ""
    assert all(record.source_reference.startswith("SYNTHETIC_") for record in project.source_audit.records)


@pytest.mark.parametrize(
    "filename",
    [
        "synthetic_20km_line.ucd.json",
        "synthetic_20km_audit_case.ucd.json",
        "synthetic_20km_applied.ucd.json",
    ],
)
def test_synthetic_cases_run_bonding_iec_and_route_thermal(filename: str) -> None:
    project = _load(filename)
    bonding = solve_bonding(project.cable, project.bonding, project.route_sections)
    sections = materialize_route_sections(project.thermal_design, project.cable)
    iec = solve_project(project.cable, sections)
    route = solve_thermal_route(project, bonding)
    assert bonding.total_length_m == pytest.approx(20_000.0)
    assert iec[0].ampacity_a > 0
    assert route.active.status in {"UYGUN", "UYGUN DEĞİL", "PASS", "CONDITIONAL"}
    assert route.active.route_ampacity_a > 0
    assert route.active.critical_region_id


def test_primary_example_contains_no_external_source_file() -> None:
    project = _load("synthetic_20km_line.ucd.json")
    assert project.source_audit.source_file == ""
    assert not project.cad_source
    assert project.project_code == "DITUS-DEMO-20KM"


def test_synthetic_report_metadata_is_neutral_and_unsigned() -> None:
    payload = json.loads((EXAMPLES / "synthetic_20km_project_report.latest.json").read_text(encoding="utf-8"))
    metadata = payload["metadata"]
    assert metadata["client"] == "Sentetik 20 km Örnek Hat"
    assert metadata["prepared_by"] == ""
