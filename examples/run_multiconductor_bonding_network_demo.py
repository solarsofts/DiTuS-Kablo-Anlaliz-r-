from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.installation import generate_standard_cross_section  # noqa: E402
from ucd.calculations.multiconductor_bonding_network import (  # noqa: E402
    solve_multiconductor_bonding_network,
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
        cross_section_id="ICS-NET-DEMO",
        name="2 devre / 2 paralel / genel N-kılıf bonding ağı",
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
        region_ids=["TR-NET-DEMO"],
    )
    section.physical_cables[-1].x_m += 0.17
    section.physical_cables[-1].depth_m += 0.09

    project = ProjectData(project_name="N-İletken Bonding Ağı Demo")
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    project.route_sections = [
        RouteSection("R-NET-DEMO", 300.0, thermal_region_id="TR-NET-DEMO"),
    ]
    project.bonding = default_bonding_system(300.0)
    project.bonding.gcc_enabled = True

    result = solve_multiconductor_bonding_network(project)
    payload = {
        "engine": "DiTuS v0.16.5.2 General N-Conductor Bonding Network SHADOW_COMPARE",
        "project_schema": project.schema_version,
        "methods_agree": result.methods_agree,
        "sheath_count": len(result.sheath_order),
        "minor_section_count": len(result.section_results),
        "node_count": result.node_count,
        "branch_current_count": result.branch_current_count,
        "maximum_method_voltage_difference_v": result.maximum_method_voltage_difference_v,
        "maximum_method_current_difference_a": result.maximum_method_current_difference_a,
        "maximum_sheath_current_a": result.maximum_sheath_current_a,
        "maximum_sheath_to_earth_voltage_v": result.maximum_sheath_to_earth_voltage_v,
        "maximum_sheath_to_sheath_voltage_v": result.maximum_sheath_to_sheath_voltage_v,
        "maximum_gcc_current_a": result.maximum_gcc_current_a,
        "total_core_metal_loss_w": result.total_core_metal_loss_w,
        "total_sheath_metal_loss_w": result.total_sheath_metal_loss_w,
        "total_gcc_metal_loss_w": result.total_gcc_metal_loss_w,
        "total_earth_return_equivalent_loss_w": result.total_earth_return_equivalent_loss_w,
        "total_accessory_loss_w": result.total_accessory_loss_w,
        "lambda1_shadow": result.lambda1,
        "sections": [
            {
                "section_id": item.section_id,
                "major_index": item.major_index,
                "start_m": item.start_m,
                "end_m": item.end_m,
                "cross_sections": list(item.route_cross_sections),
                "maximum_sheath_current_a": item.maximum_sheath_current_a,
                "maximum_sheath_to_earth_voltage_v": item.maximum_sheath_to_earth_voltage_v,
                "maximum_sheath_to_sheath_voltage_v": item.maximum_sheath_to_sheath_voltage_v,
                "core_metal_loss_w": item.core_metal_loss_w,
                "sheath_metal_loss_w": item.sheath_metal_loss_w,
                "gcc_current": _complex(item.gcc_current_a),
                "sheaths": [
                    {
                        "key": row.key,
                        "physical_cable_id": row.physical_cable_id,
                        "current": _complex(row.sheath_current_a),
                        "start_voltage_to_earth": _complex(row.start_voltage_to_earth_v),
                        "end_voltage_to_earth": _complex(row.end_voltage_to_earth_v),
                        "integrated_open_emf": _complex(row.integrated_open_emf_v),
                        "sheath_metal_loss_w": row.sheath_metal_loss_w,
                    }
                    for row in item.sheath_results
                ],
            }
            for item in result.section_results
        ],
        "cross_links": [
            {
                "branch_id": item.branch_id,
                "current": _complex(item.current_a),
                "active_loss_w": item.active_loss_w,
            }
            for item in result.accessory_branches
            if item.branch_type == "CROSS_LINK"
        ],
    }
    output = Path(__file__).resolve().parent / "multiconductor_bonding_network_results.latest.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nYazıldı: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
