from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.installation import generate_standard_cross_section  # noqa: E402
from ucd.calculations.multiconductor_global_network import (  # noqa: E402
    solve_global_multiconductor_network,
)
from ucd.models.project import (  # noqa: E402
    InstallationDesignData,
    ProjectData,
    RouteSection,
    default_bonding_system,
)


def _complex(value: complex) -> dict[str, float]:
    return {
        "real": float(value.real),
        "imag": float(value.imag),
        "magnitude": float(abs(value)),
    }


def main() -> int:
    section = generate_standard_cross_section(
        cross_section_id="ICS-GLOBAL-DEMO",
        name="2 devre / 2 paralel / global core + bonding",
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
        region_ids=["TR-GLOBAL-DEMO"],
    )
    # Deliberate asymmetry: equal sharing must not be imposed.
    section.physical_cables[-1].x_m += 0.17
    section.physical_cables[-1].depth_m += 0.09

    project = ProjectData(project_name="Global N-Core + N-Kılıf Demo")
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    project.route_sections = [
        RouteSection("R-GLOBAL-DEMO", 300.0, thermal_region_id="TR-GLOBAL-DEMO"),
    ]
    project.bonding = default_bonding_system(300.0)
    project.bonding.gcc_enabled = True

    result = solve_global_multiconductor_network(project)
    payload = {
        "engine": "DiTuS v0.16.5.2 Global N-Core + N-Sheath SHADOW_COMPARE",
        "project_schema": project.schema_version,
        "methods_agree": result.methods_agree,
        "core_sharing_mode": result.core_sharing_mode,
        "core_count": len(result.core_order),
        "sheath_count": len(result.sheath_order),
        "group_count": len(result.group_order),
        "minor_section_count": len(result.section_results),
        "maximum_method_core_current_difference_a": result.maximum_method_core_current_difference_a,
        "maximum_method_sheath_current_difference_a": result.maximum_method_sheath_current_difference_a,
        "maximum_method_voltage_difference_v": result.maximum_method_voltage_difference_v,
        "maximum_core_current_imbalance_percent": result.maximum_core_current_imbalance_percent,
        "maximum_sheath_current_a": result.maximum_sheath_current_a,
        "maximum_sheath_to_earth_voltage_v": result.maximum_sheath_to_earth_voltage_v,
        "total_core_metal_loss_w": result.total_core_metal_loss_w,
        "total_sheath_metal_loss_w": result.total_sheath_metal_loss_w,
        "lambda1_shadow": result.lambda1,
        "groups": [
            {
                "group_id": item.group_id,
                "parallel_count": item.parallel_count,
                "target": _complex(item.target_current_a),
                "solved": _complex(item.solved_current_a),
                "route_voltage_drop": _complex(item.route_voltage_drop_v),
                "imbalance_percent": item.imbalance_percent,
                "current_sum_residual_a": item.current_sum_residual_a,
            }
            for item in result.group_results
        ],
        "cores": [
            {
                "key": item.key,
                "physical_cable_id": item.physical_cable_id,
                "current": _complex(item.core_current_a),
                "equal_share": _complex(item.equal_share_current_a),
                "current_share_percent": item.current_share_percent,
                "difference_from_equal_share_a": item.current_difference_from_equal_share_a,
                "route_voltage_drop": _complex(item.route_voltage_drop_v),
                "core_metal_loss_w": item.core_metal_loss_w,
            }
            for item in result.core_results
        ],
        "sections": [
            {
                "section_id": item.section_id,
                "major_index": item.major_index,
                "cross_sections": list(item.route_cross_sections),
                "maximum_sheath_current_a": item.maximum_sheath_current_a,
                "maximum_sheath_to_earth_voltage_v": item.maximum_sheath_to_earth_voltage_v,
                "core_metal_loss_w": item.core_metal_loss_w,
                "sheath_metal_loss_w": item.sheath_metal_loss_w,
            }
            for item in result.section_results
        ],
    }
    output = Path(__file__).resolve().parent / "multiconductor_global_network_results.latest.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nYazıldı: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
