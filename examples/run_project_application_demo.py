from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations import solve_production_electrothermal_study
from ucd.calculations.cable_library import merge_builtin_catalogs
from ucd.calculations.project_application import (
    apply_catalog_candidate_to_project,
    evaluate_application_iteration_gates,
    resolve_source_conflict,
)
from ucd.models.project import CONFLICT_CREATE_SCENARIOS, ProjectData
from synthetic_catalog_factory import merge_synthetic_catalogs


CASES = [
    "synthetic_20km_line.ucd.json",
    "synthetic_20km_audit_case.ucd.json",
    "synthetic_20km_applied.ucd.json",
]
RECORD_ID = "SYN-MFR-A-MV40K5-AL400-35"


def run_case(path: Path) -> tuple[ProjectData, dict]:
    project = ProjectData.from_dict(json.loads(path.read_text(encoding="utf-8")))
    merge_builtin_catalogs(project.cable_library)
    merge_synthetic_catalogs(project.cable_library)
    applied = apply_catalog_candidate_to_project(
        project,
        RECORD_ID,
        f"{RECORD_ID}::P1",
        1,
        [section.name for section in project.route_sections],
    )
    for conflict in project.source_audit.conflicts:
        if conflict.disposition and conflict.disposition != "UNRESOLVED":
            continue
        resolve_source_conflict(
            project,
            conflict.conflict_id,
            CONFLICT_CREATE_SCENARIOS,
            conflict.record_ids,
            rationale="Sentetik demo: alternatif girdiler ayrı doğrulama senaryolarında korunur.",
            decided_by="DiTuS demo",
        )
    gates = evaluate_application_iteration_gates(project)
    voltage = gates.voltage_drop
    production = solve_production_electrothermal_study(project)
    result = {
        "project": path.name,
        "route_length_m": float(project.design_basis.total_route_length_m),
        "snapshot_id": applied.snapshot_id,
        "snapshot_hash": applied.snapshot_hash,
        "application_status": applied.status,
        "completion_status": applied.completion.status,
        "assigned_route_sections": list(applied.assigned_route_sections),
        "iteration_gate_status": gates.status,
        "voltage_drop_percent": voltage.voltage_drop_percent if voltage else None,
        "voltage_drop_v": voltage.voltage_drop_v if voltage else None,
        "production_active_scenario_id": production.active.scenario.scenario_id,
        "production_completion_status": production.active.completion_status,
        "production_suitability_status": production.active.suitability_status,
        "production_maximum_conductor_temperature_c": production.active.maximum_conductor_temperature_c,
        "production_global_lambda1": production.active.global_lambda1,
        "production_loss_vector_fingerprint": production.active.loss_vector_fingerprint,
        "unresolved_blocking_gates": [
            gate.gate_id for gate in gates.gates if gate.blocking and gate.status == "BLOCKED"
        ],
        "trace": list(gates.trace),
    }
    return project, result


def main() -> None:
    results = []
    applied_project = None
    for name in CASES:
        project, result = run_case(ROOT / "examples" / name)
        results.append(result)
        if name == CASES[0]:
            applied_project = project
    output = {
        "format": "DITUS_PROJECT_APPLICATION_DEMO",
        "version": "0.16.9.4.27",
        "catalog_record_id": RECORD_ID,
        "scope": "UNDERGROUND_ONLY",
        "results": results,
    }
    result_path = ROOT / "examples" / "synthetic_20km_application_results.latest.json"
    result_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
