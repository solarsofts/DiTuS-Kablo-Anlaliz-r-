from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.installation import generate_standard_cross_section  # noqa: E402
from ucd.calculations.multiconductor_em import (  # noqa: E402
    SHEATH_OPEN,
    SHEATH_SOLID_BOTH_END,
    solve_multiconductor_em,
)
from ucd.models.project import InstallationDesignData, ProjectData  # noqa: E402


def _complex(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag), "magnitude": float(abs(value))}


def main() -> int:
    section = generate_standard_cross_section(
        cross_section_id="ICS-DEMO-N24",
        name="2 devre / faz başına 2 paralel / ABC-CBA",
        arrangement="FLAT",
        circuit_count=2,
        parallel_cables_per_phase=2,
        phase_orders=["ABC", "CBA"],
        circuit_load_currents_a=[900.0, 600.0],
        phase_spacing_m=0.25,
        circuit_spacing_m=1.60,
        parallel_group_spacing_m=0.80,
        burial_depth_m=1.25,
        outer_diameter_m=0.105,
    )
    section.physical_cables[-1].x_m += 0.17
    section.physical_cables[-1].depth_m += 0.09
    project = ProjectData(project_name="N-İletken EM Demo")
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )

    payload: dict[str, object] = {
        "engine": "DiTuS v0.16.5.2 General N-Conductor EM SHADOW_COMPARE",
        "project_schema": project.schema_version,
        "cross_section_id": section.cross_section_id,
        "results": {},
    }
    for mode in (SHEATH_OPEN, SHEATH_SOLID_BOTH_END):
        result = solve_multiconductor_em(project, sheath_mode=mode)
        payload["results"][mode] = {
            "conductor_count": len(result.conductor_order),
            "core_count": result.core_count,
            "group_count": len(result.group_results),
            "methods_agree": result.methods_agree,
            "maximum_method_current_difference_a": result.maximum_method_current_difference_a,
            "maximum_method_voltage_difference_v_km": result.maximum_method_voltage_difference_v_km,
            "lambda1_shadow": result.lambda1,
            "maximum_current_imbalance_percent": result.maximum_current_imbalance_percent,
            "groups": [
                {
                    "group_id": item.group_id,
                    "target": _complex(item.target_current_a),
                    "solved": _complex(item.solved_current_a),
                    "current_sum_residual_a": item.current_sum_residual_a,
                    "imbalance_percent": item.imbalance_percent,
                }
                for item in result.group_results
            ],
            "cables": [
                {
                    "physical_cable_id": item.physical_cable_id,
                    "core_current": _complex(item.core_current_a),
                    "sheath_current": _complex(item.sheath_current_a),
                    "current_share_percent": item.current_share_percent,
                    "core_loss_w_km": item.core_loss_w_km,
                    "sheath_loss_w_km": item.sheath_loss_w_km,
                }
                for item in result.cable_results
            ],
        }

    output = Path(__file__).resolve().parent / "multiconductor_em_results.latest.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nYazıldı: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
