from __future__ import annotations

import json
from pathlib import Path

from ucd.calculations.engine_precheck import evaluate_engine_precheck
from ucd.models.project import ProjectData

ROOT = Path(__file__).resolve().parent
PROJECT_FILE = ROOT / "synthetic_20km_line.ucd.json"
OUTPUT = ROOT / "engine_precheck_matrix.latest.json"


def main() -> None:
    project = ProjectData.from_dict(json.loads(PROJECT_FILE.read_text(encoding="utf-8")))
    engine_ids = (
        "precheck", "iec60287", "thermal_route", "nodal", "bonding",
        "fault_epr", "svl", "transient", "iteration", "report", "procurement",
    )
    payload = {
        "project_code": project.project_code,
        "scope": "UNDERGROUND_ONLY",
        "engines": [evaluate_engine_precheck(project, engine_id).to_dict() for engine_id in engine_ids],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUTPUT)
    for item in payload["engines"]:
        print(f"{item['engine_id']}: {item['status']} / {item['maturity']} — {item['method']['display_name']}")


if __name__ == "__main__":
    main()
