from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from ucd.calculations.bonding import solve_bonding
from ucd.calculations.iec60287 import SUITABILITY_INDETERMINATE
from ucd.calculations.installation_coupling import (
    MATERIAL_LAYERED,
    RESULT_ENGINEERING_APPROXIMATION,
    attach_resolved_geometry_to_route_sections,
    resolve_installation_geometry,
    synchronize_installation_geometry,
)
from ucd.calculations.project_geometry_runtime import (
    materialize_project_route_sections,
    solve_project_bonding,
)
from ucd.calculations.thermal_resistance import solve_section_thermal
from ucd.calculations.thermal_route import solve_thermal_route
from ucd.models.project import EXTERNAL_THERMAL_AUTO, ProjectData


ROOT = Path(__file__).resolve().parents[1]


def _synthetic() -> ProjectData:
    return ProjectData.from_dict(json.loads((ROOT / "examples" / "synthetic_20km_line.ucd.json").read_text()))


def test_reference_three_material_trench_keeps_analytic_preview_but_nodal_authority() -> None:
    project = _synthetic()
    sections, result = materialize_project_route_sections(project, strict=True)
    assert not result.classification.all_errors
    assert len(sections) == 4
    for region_id in ("TR-01", "TR-02"):
        region = next(item for item in project.thermal_design.regions if item.region_id == region_id)
        assert region.overrides["material_field_class"] == MATERIAL_LAYERED
        assert region.overrides["analytic_result_authority"] == RESULT_ENGINEERING_APPROXIMATION
        assert region.overrides["authoritative_method"] == "NODAL"
        assert region.overrides["analytical_preview_allowed"] is True
        assert region.overrides["surface_thermal_correction_km_w"] > 0.0
        assert region.overrides["backfill_effective_radius_m"] > 0.0
        assert "far_field_effective_rho_km_w" not in region.overrides
        assert "layer_reduction_status" not in region.overrides


def test_auto_image_depends_on_axis_depth_not_trench_bottom() -> None:
    project = _synthetic()
    region = project.thermal_design.regions[0]
    region.overrides["external_thermal_mode"] = EXTERNAL_THERMAL_AUTO
    sections, _ = materialize_project_route_sections(project, strict=True)
    first = sections[0]
    positions = tuple((value[0], value[1]) for _phase, value in sorted(first.phase_positions_m.items()))
    base = solve_section_thermal(project.cable, first, positions).external.effective_t4_km_w

    project.installation_design.cross_sections[0].channel_geometry.trench_depth_m += 0.75
    sections, _ = materialize_project_route_sections(project, strict=True)
    changed = sections[0]
    positions2 = tuple((value[0], value[1]) for _phase, value in sorted(changed.phase_positions_m.items()))
    altered = solve_section_thermal(project.cable, changed, positions2).external.effective_t4_km_w
    assert altered == pytest.approx(base, rel=0.0, abs=1e-12)


def test_per_group_geometry_is_not_collapsed_into_bonding_scalar() -> None:
    project = _synthetic()
    section = project.installation_design.cross_sections[0]
    # Open only circuit 2 while preserving circuit 1 touching trefoil.
    for cable in section.physical_cables:
        if cable.circuit_id == "C2" and cable.phase == "B":
            cable.x_m -= 0.06
        if cable.circuit_id == "C2" and cable.phase == "C":
            cable.x_m += 0.06
    old_fallback = project.bonding.phase_spacing_m
    synchronize_installation_geometry(project)
    resolved = resolve_installation_geometry(project).for_region("TR-01")
    assert resolved is not None
    groups = {(g.circuit_id, g.parallel_index): g for g in resolved.phase_groups}
    assert groups[("C1", 1)].canonical_spacing_m != pytest.approx(groups[("C2", 1)].canonical_spacing_m)
    assert project.bonding.phase_spacing_m == old_fallback


def test_bonding_target_circuit_selects_explicit_xy() -> None:
    project = _synthetic()
    section = project.installation_design.cross_sections[0]
    for cable in section.physical_cables:
        if cable.circuit_id == "C2":
            cable.x_m *= 1.8
    project.bonding.target_circuit_id = "C2"
    sections, _ = materialize_project_route_sections(project, strict=True)
    tr1 = sections[0]
    assert tr1.bonding_circuit_id == "C2"
    result_c2 = solve_bonding(project.cable, project.bonding, sections)

    project2 = _synthetic()
    project2.bonding.target_circuit_id = "C1"
    result_c1 = solve_project_bonding(project2)
    assert result_c2.sheath_loop_reactance_ohm_km != pytest.approx(result_c1.sheath_loop_reactance_ohm_km)


def test_custom_explicit_xy_is_supported_by_bonding_and_primitive() -> None:
    project = _synthetic()
    section = project.installation_design.cross_sections[0]
    section.arrangement_label = "CUSTOM"
    for cable in section.physical_cables:
        if cable.circuit_id == "C1" and cable.phase == "A":
            cable.x_m -= 0.03
        if cable.circuit_id == "C1" and cable.phase == "C":
            cable.depth_m += 0.04
    result = solve_project_bonding(project)
    contribution = result.minor_results[0].route_contributions[0]
    assert contribution.phase_positions_m
    assert contribution.geometry_fingerprint
    assert result.primitive_network_result is not None


def test_geometry_fingerprint_changes_with_physical_coordinate() -> None:
    project = _synthetic()
    first = resolve_installation_geometry(project).for_region("TR-01")
    assert first is not None
    project.installation_design.cross_sections[0].physical_cables[0].x_m += 0.001
    second = resolve_installation_geometry(project).for_region("TR-01")
    assert second is not None
    assert first.geometry_fingerprint != second.geometry_fingerprint


def test_nonreducible_slab_is_model_scope_not_physical_rejection() -> None:
    project = _synthetic()
    project.installation_design.cross_sections[0].channel_geometry.cover_slab_enabled = True
    result = solve_thermal_route(project)
    scenario = result.active
    tr1 = next(item for item in scenario.region_outcomes if item.region_id == "TR-01")
    assert tr1.success
    assert tr1.error_code == ""
    assert tr1.physical_rejection is False
    issues = [item for item in result.validation_issues if item.region_id == "TR-01"]
    assert any(item.code == "ANALYTIC_COMPLEX_REGIONS_REQUIRES_NODAL" and item.severity == "WARNING" for item in issues)


def test_legacy_route_without_explicit_xy_still_uses_scalar_fallback() -> None:
    project = ProjectData()
    legacy_routes = deepcopy(project.route_sections)
    for route in legacy_routes:
        route.phase_positions_m = {}
        route.geometry_basis = "LEGACY_SCALAR"
    result = solve_bonding(project.cable, project.bonding, legacy_routes)
    assert result.total_length_m > 0
    assert not result.minor_results[0].route_contributions[0].phase_positions_m
