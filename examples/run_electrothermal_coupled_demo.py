from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.electrothermal_coupled import (  # noqa: E402
    solve_electrothermal_ampacity,
    solve_electrothermal_coupled,
)
from ucd.calculations.installation import generate_standard_cross_section  # noqa: E402
from ucd.models.project import (  # noqa: E402
    InstallationDesignData,
    ProjectData,
    RouteSection,
    ThermalRegion,
    default_bonding_system,
)


def main() -> int:
    section = generate_standard_cross_section(
        cross_section_id="ICS-ET-DEMO",
        name="2 devre / 2 paralel / elektro-termal kapalı çevrim",
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
        region_ids=["TR-ET-DEMO"],
    )
    section.physical_cables[-1].x_m += 0.17
    section.physical_cables[-1].depth_m += 0.09

    project = ProjectData(project_name="Elektro-Termal Kapalı Çevrim Demo")
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    project.route_sections = [RouteSection("R-ET-DEMO", 300.0, thermal_region_id="TR-ET-DEMO")]
    project.thermal_design.route_length_m = 300.0
    project.thermal_design.regions = [
        ThermalRegion(
            "TR-ET-DEMO",
            "Elektro-termal demo bölgesi",
            0.0,
            300.0,
            project.thermal_design.templates[0].template_id,
        )
    ]
    project.bonding = default_bonding_system(300.0)
    project.bonding.gcc_enabled = True

    result = solve_electrothermal_coupled(
        project,
        mesh_scale=2.5,
        maximum_iterations=20,
        temperature_tolerance_c=0.08,
        current_tolerance_percent=0.10,
        loss_tolerance_percent=0.10,
        relaxation_factor=0.60,
    )
    ampacity = solve_electrothermal_ampacity(
        project,
        mesh_scale=3.0,
        maximum_closed_loop_iterations=18,
        maximum_rating_iterations=12,
        temperature_tolerance_c=0.25,
        current_tolerance_a=5.0,
    )
    payload = {
        "engine": "DiTuS v0.16.7 Closed-Loop Electro-Thermal SHADOW_COMPARE",
        "project_schema": project.schema_version,
        "mode": result.mode,
        "coupling_mode": result.coupling_mode,
        "converged": result.converged,
        "iteration_count": result.iteration_count,
        "maximum_iterations": result.maximum_iterations,
        "temperature_tolerance_c": result.temperature_tolerance_c,
        "current_tolerance_percent": result.current_tolerance_percent,
        "loss_tolerance_percent": result.loss_tolerance_percent,
        "final_maximum_conductor_temperature_c": result.final_thermal.maximum_nodal_conductor_temperature_c,
        "final_lambda1": result.final_global_em.lambda1,
        "final_core_loss_w": result.final_global_em.total_core_metal_loss_w,
        "final_sheath_loss_w": result.final_global_em.total_sheath_metal_loss_w,
        "maximum_core_current_imbalance_percent": result.final_global_em.maximum_core_current_imbalance_percent,
        "ampacity_shadow": {
            "converged": ampacity.converged,
            "rating_factor": ampacity.rating_factor,
            "circuit_rating_currents_a": ampacity.circuit_rating_currents_a,
            "temperature_limit_c": ampacity.temperature_limit_c,
            "critical_region_id": ampacity.critical_region_id,
            "critical_cable_id": ampacity.critical_cable_id,
            "evaluation_count": len(ampacity.evaluations),
        },
        "iterations": [
            {
                "iteration": item.iteration,
                "maximum_temperature_residual_c": item.maximum_temperature_residual_c,
                "maximum_core_current_change_percent": item.maximum_core_current_change_percent,
                "maximum_sheath_current_change_percent": item.maximum_sheath_current_change_percent,
                "active_loss_change_percent": item.active_loss_change_percent,
                "maximum_conductor_temperature_c": item.maximum_conductor_temperature_c,
                "maximum_sheath_temperature_c": item.maximum_sheath_temperature_c,
                "total_core_loss_w": item.total_core_loss_w,
                "total_sheath_loss_w": item.total_sheath_loss_w,
                "lambda1": item.lambda1,
                "em_methods_agree": item.em_methods_agree,
                "thermal_regions_converged": item.thermal_regions_converged,
            }
            for item in result.iterations
        ],
        "regions": [
            {
                "region_id": region.region_id,
                "cross_section_id": region.cross_section_id,
                "maximum_nodal_conductor_temperature_c": region.maximum_nodal_conductor_temperature_c,
                "nodal_energy_balance_error_percent": region.nodal_energy_balance_error_percent,
                "cables": [
                    {
                        "physical_cable_id": cable.physical_cable_id,
                        "key": cable.key,
                        "current_a": abs(cable.current_a),
                        "conductor_loss_w_m": cable.conductor_loss_w_m,
                        "sheath_loss_w_m": cable.sheath_loss_w_m,
                        "nodal_jacket_temperature_c": cable.nodal_jacket_temperature_c,
                        "nodal_conductor_temperature_c": cable.nodal_conductor_temperature_c,
                    }
                    for cable in region.cables
                ],
            }
            for region in result.final_thermal.regions
        ],
        "issues": [
            {"severity": item.severity, "code": item.code, "message": item.message}
            for item in result.issues
        ],
    }
    output = Path(__file__).resolve().parent / "electrothermal_coupled_results.latest.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nYazıldı: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
