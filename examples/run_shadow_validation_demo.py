from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.shadow_validation import run_shadow_validation  # noqa: E402
from ucd.models.project import ProjectData  # noqa: E402


def main() -> int:
    project = ProjectData(project_name="Fiziksel Motor Shadow Doğrulama Demo")
    result = run_shadow_validation(
        project,
        mesh_scale=3.0,
        maximum_closed_loop_iterations=15,
        maximum_rating_iterations=10,
    )
    payload = result.to_dict()
    payload["engine"] = "DiTuS v0.16.8 Physical Motor Validation / SHADOW_VALIDATION"
    payload["project_schema"] = project.schema_version
    output = Path(__file__).resolve().parent / "shadow_validation_results.latest.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nYazıldı: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
