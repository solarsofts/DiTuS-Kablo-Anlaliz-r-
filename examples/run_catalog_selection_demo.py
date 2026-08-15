from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.cable_library import merge_builtin_catalogs  # noqa: E402
from ucd.calculations.cable_selection import evaluate_catalog_candidates  # noqa: E402
from ucd.models.project import ProjectData  # noqa: E402
from synthetic_catalog_factory import merge_synthetic_catalogs  # noqa: E402


def main() -> int:
    cases = [
        "synthetic_20km_line.ucd.json",
        "synthetic_20km_audit_case.ucd.json",
        "synthetic_20km_applied.ucd.json",
    ]
    output = {"format": "DITUS_CATALOG_SELECTION_DEMO", "version": "0.16.9.4.27", "cases": []}
    for name in cases:
        project = ProjectData.from_dict(json.loads((ROOT / "examples" / name).read_text(encoding="utf-8")))
        merge_builtin_catalogs(project.cable_library)
        merge_synthetic_catalogs(project.cable_library)
        result = evaluate_catalog_candidates(project.cable_library, project.design_basis, maximum_parallel_cables=1)
        output["cases"].append({
            "case": name,
            "system_voltage_kv": project.design_basis.system_voltage_kv,
            "route_length_m": project.design_basis.total_route_length_m,
            "design_current_a": project.design_basis.design_current_per_circuit_a,
            "candidates": [asdict(item) for item in result.evaluations],
            "trace": list(result.trace),
        })
    target = ROOT / "examples" / "catalog_selection_results.latest.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)
    for case in output["cases"]:
        first = case["candidates"][0] if case["candidates"] else None
        print(case["case"], "->", first["candidate_id"] if first else "NO_CANDIDATE",
              "dV%", None if not first else first["voltage_drop_percent"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
