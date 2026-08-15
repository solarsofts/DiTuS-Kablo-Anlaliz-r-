from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations import evaluate_project_workflow  # noqa: E402
from ucd.models.project import ProjectData  # noqa: E402


def main() -> int:
    project_path = ROOT / "examples" / "synthetic_20km_line.ucd.json"
    project = ProjectData.from_dict(json.loads(project_path.read_text(encoding="utf-8")))
    result = evaluate_project_workflow(project)
    payload = {
        "project_name": project.project_name,
        "schema_version": project.schema_version,
        "current_stage_id": result.current_stage_id,
        "recommended_stage_id": result.recommended_stage_id,
        "recommended_action": result.recommended_action,
        "overall_status": result.overall_status,
        "stages": [
            {
                "number": stage.number,
                "stage_id": stage.stage_id,
                "title": stage.title,
                "status": stage.status,
                "missing_inputs": stage.missing_inputs,
                "blocking_reasons": stage.blocking_reasons,
                "engines": stage.engines,
                "next_action": stage.next_action,
            }
            for stage in result.stages
        ],
    }
    target = ROOT / "examples" / "workflow_evaluation.latest.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)
    print(f"overall={result.overall_status}; recommended={result.recommended_stage_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
