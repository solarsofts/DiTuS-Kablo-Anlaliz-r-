from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.installation import generate_standard_cross_section  # noqa: E402
from ucd.calculations.multiconductor_thermal import solve_multiconductor_thermal  # noqa: E402
from ucd.models.project import (  # noqa: E402
    ExternalHeatSourceData,
    InstallationDesignData,
    ProjectData,
    RouteSection,
    ThermalRegion,
    default_bonding_system,
)


def main() -> int:
    section = generate_standard_cross_section(
        cross_section_id="ICS-THERMAL-DEMO",
        name="2 devre / 2 paralel / gerçek x-y termal",
        arrangement="FLAT",
        circuit_count=2,
        parallel_cables_per_phase=2,
        phase_orders=["ABC", "CBA"],
        circuit_load_currents_a=[900.0, 600.0],
        phase_spacing_m=0.25,
        circuit_spacing_m=2.50,
        parallel_group_spacing_m=0.75,
        burial_depth_m=1.25,
        outer_diameter_m=0.105,
        region_ids=["TR-THERMAL-DEMO"],
    )
    section.physical_cables[-1].x_m += 0.17
    section.physical_cables[-1].depth_m += 0.09
    section.external_heat_sources = [
        ExternalHeatSourceData("HS-DEMO", "Harici sıcak boru", 0.0, 1.10, 20.0, 0.08, True)
    ]

    project = ProjectData(project_name="Gerçek x-y N-Kablo Termal Demo")
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    project.route_sections = [
        RouteSection("R-THERMAL-DEMO", 300.0, thermal_region_id="TR-THERMAL-DEMO"),
    ]
    project.thermal_design.route_length_m = 300.0
    project.thermal_design.regions = [
        ThermalRegion(
            "TR-THERMAL-DEMO",
            "Gerçek x-y demo bölgesi",
            0.0,
            300.0,
            project.thermal_design.templates[0].template_id,
        )
    ]
    project.bonding = default_bonding_system(300.0)
    project.bonding.gcc_enabled = True

    result = solve_multiconductor_thermal(project, mesh_scale=2.0, tolerance_c=0.05)
    payload = {
        "engine": "DiTuS v0.16.6 Real-x/y Multiconductor Thermal SHADOW_COMPARE",
        "project_schema": project.schema_version,
        "mode": result.mode,
        "coupling_mode": result.coupling_mode,
        "region_count": len(result.regions),
        "critical_analytical_region_id": result.critical_analytical_region_id,
        "critical_nodal_region_id": result.critical_nodal_region_id,
        "maximum_analytical_conductor_temperature_c": result.maximum_analytical_conductor_temperature_c,
        "maximum_nodal_conductor_temperature_c": result.maximum_nodal_conductor_temperature_c,
        "maximum_method_temperature_difference_c": result.maximum_method_temperature_difference_c,
        "regions": [
            {
                "region_id": region.region_id,
                "cross_section_id": region.cross_section_id,
                "installation_type": region.installation_type,
                "cable_count": len(region.cables),
                "analytical_matrix_size": len(region.analytical_matrix_km_w),
                "nodal_mesh": [region.nodal_mesh_nx, region.nodal_mesh_ny],
                "nodal_converged": region.nodal_converged,
                "nodal_energy_balance_error_percent": region.nodal_energy_balance_error_percent,
                "maximum_analytical_conductor_temperature_c": region.maximum_analytical_conductor_temperature_c,
                "maximum_nodal_conductor_temperature_c": region.maximum_nodal_conductor_temperature_c,
                "maximum_method_temperature_difference_c": region.maximum_method_temperature_difference_c,
                "cables": [
                    {
                        "physical_cable_id": item.physical_cable_id,
                        "key": item.key,
                        "current_a": abs(item.current_a),
                        "conductor_loss_w_m": item.conductor_loss_w_m,
                        "sheath_loss_w_m": item.sheath_loss_w_m,
                        "dielectric_loss_w_m": item.dielectric_loss_w_m,
                        "armour_loss_w_m": item.armour_loss_w_m,
                        "total_loss_w_m": item.total_loss_w_m,
                        "analytical_conductor_temperature_c": item.analytical_conductor_temperature_c,
                        "nodal_conductor_temperature_c": item.nodal_conductor_temperature_c,
                    }
                    for item in region.cables
                ],
            }
            for region in result.regions
        ],
        "issues": [
            {"severity": item.severity, "code": item.code, "message": item.message, "object_id": item.object_id}
            for item in result.issues
        ],
    }
    output = Path(__file__).resolve().parent / "multiconductor_thermal_results.latest.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nYazıldı: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
