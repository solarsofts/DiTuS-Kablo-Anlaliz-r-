from __future__ import annotations

from copy import deepcopy

from ucd.calculations.multiconductor_thermal import solve_multiconductor_thermal
from ucd.calculations.nodal_thermal import solve_nodal_route
from ucd.models.project import ProjectData


def test_channel_geometry_is_active_in_shadow_and_production_nodal() -> None:
    baseline = ProjectData()
    edited = deepcopy(baseline)
    for section in edited.installation_design.cross_sections:
        section.channel_geometry.source_reference = "USER_INTERACTIVE_GEOMETRY"
        section.channel_geometry.trench_width_m = 2.40
        section.channel_geometry.thermal_backfill_height_m = 0.75
        section.channel_geometry.bedding_thickness_m = 0.35

    shadow_base = solve_multiconductor_thermal(
        baseline, mesh_scale=3.0, max_iterations=15, tolerance_c=0.08
    )
    shadow_edited = solve_multiconductor_thermal(
        edited, mesh_scale=3.0, max_iterations=15, tolerance_c=0.08
    )
    assert abs(
        shadow_edited.maximum_nodal_conductor_temperature_c
        - shadow_base.maximum_nodal_conductor_temperature_c
    ) > 0.5
    assert any(
        issue.code == "INSTALLATION_CHANNEL_GEOMETRY_ACTIVE"
        for issue in shadow_edited.issues
    )

    production_base = solve_nodal_route(baseline)
    production_edited = solve_nodal_route(edited)
    assert abs(
        production_edited.active.maximum_conductor_temperature_c
        - production_base.active.maximum_conductor_temperature_c
    ) > 0.05
    assert abs(
        production_edited.active.route_ampacity_per_cable_a
        - production_base.active.route_ampacity_per_cable_a
    ) > 0.05
    assert any(
        "Kablo-Kanal gerçek x-y" in line
        for region in production_edited.active.regions
        for line in region.trace
    )
