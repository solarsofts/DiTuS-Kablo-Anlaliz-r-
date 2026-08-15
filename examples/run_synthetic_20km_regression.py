from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations import (  # noqa: E402
    audit_project_sources,
    solve_fault_study,
    solve_nodal_route,
    solve_production_electrothermal_study,
    solve_project_bonding,
)
from ucd.models.project import ProjectData  # noqa: E402


def main() -> int:
    examples = Path(__file__).resolve().parent
    manifest = json.loads((examples / "synthetic_20km_regression_suite.json").read_text(encoding="utf-8"))
    results = {
        "suite_id": manifest["suite_id"],
        "scope": manifest["scope"],
        "source_type": manifest["source_type"],
        "results": [],
    }
    representative_nodal = None
    representative_production = None
    representative_case_id = ""
    for case in manifest["cases"]:
        project = ProjectData.from_dict(json.loads((examples / case["project_file"]).read_text(encoding="utf-8")))
        audit = audit_project_sources(project)
        bonding = solve_project_bonding(project)
        # The three bundled cases share the same electrical/thermal geometry;
        # only source-audit and catalog-application workflow state differs.
        # Run the expensive 2D nodal route once and reuse that representative
        # physical result for the metadata/workflow variants.
        if representative_nodal is None:
            representative_nodal = solve_nodal_route(project, bonding, "DESIGN")
            representative_production = solve_production_electrothermal_study(project)
            representative_case_id = case["case_id"]
        nodal = representative_nodal
        production = representative_production
        fault = solve_fault_study(project.cable, project.bonding, project.route_sections, project.fault_study)
        results["results"].append({
            "case_id": case["case_id"],
            "purpose": case["purpose"],
            "route_length_m": case["route_length_m"],
            "source_audit_status": audit.status,
            "source_conflict_count": audit.issue_count,
            "normal_current_per_active_circuit_a": project.design_basis.normal_current_per_active_circuit_a,
            "n1_current_per_circuit_a": project.design_basis.n1_current_per_circuit_a,
            "bonding_scheme": bonding.scheme,
            "maximum_standing_voltage_v": bonding.max_standing_voltage_v,
            "lambda1": bonding.lambda1,
            "nodal_route_ampacity_per_cable_a": nodal.active.route_ampacity_per_cable_a,
            "nodal_status": nodal.active.status,
            "nodal_result_basis_case_id": representative_case_id,
            "production_active_scenario_id": production.active.scenario.scenario_id,
            "production_completion_status": production.active.completion_status,
            "production_suitability_status": production.active.suitability_status,
            "production_maximum_conductor_temperature_c": production.active.maximum_conductor_temperature_c,
            "production_global_lambda1": production.active.global_lambda1,
            "production_loss_vector_fingerprint": production.active.loss_vector_fingerprint,
            "governing_fault_scenario_id": fault.governing_scenario_id,
            "maximum_epr_v": fault.maximum_epr_v,
            "maximum_sheath_current_a": fault.maximum_sheath_current_a,
            "final_design_status": "NOT_READY_SYNTHETIC_EXAMPLE",
        })
    output = examples / "synthetic_20km_regression_results.latest.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nYazıldı: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
