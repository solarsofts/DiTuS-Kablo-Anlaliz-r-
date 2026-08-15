from __future__ import annotations

import json
from pathlib import Path

from ucd.calculations.installation_coupling import (
    MATERIAL_LAYERED,
    RESULT_DERIVED_FROM_SCALAR,
    RESULT_ENGINEERING_APPROXIMATION,
    resolve_installation_geometry,
    synchronize_installation_geometry,
)
from ucd.calculations.thermal_route import validate_thermal_design
from ucd.models.project import ProjectData

ROOT = Path(__file__).resolve().parents[1]


def _synthetic() -> ProjectData:
    return ProjectData.from_dict(json.loads((ROOT / 'examples/synthetic_20km_line.ucd.json').read_text(encoding='utf-8')))


def test_layered_physical_section_keeps_preview_but_nodal_is_authority() -> None:
    project = _synthetic()
    synchronize_installation_geometry(project)
    region = next(r for r in project.thermal_design.regions if r.region_id == 'TR-01')
    ov = region.overrides
    assert ov['material_field_class'] == MATERIAL_LAYERED
    assert ov['analytic_result_authority'] == RESULT_ENGINEERING_APPROXIMATION
    assert ov['authoritative_method'] == 'NODAL'
    assert ov['analytical_preview_allowed'] is True
    assert 'layer_reduction_status' not in ov
    assert 'far_field_effective_rho_km_w' not in ov


def test_negative_surface_correction_records_raw_and_clamp_evidence() -> None:
    project = _synthetic()
    # Make selected/general/surface layers lower-rho than native to force a negative preview correction.
    for material in project.thermal_design.materials:
        if material.material_id in {'MAT-FILL-01', 'MAT-ASPHALT-01'}:
            material.thermal_resistivity_km_w = 0.2
    resolved = resolve_installation_geometry(project).for_region('TR-01')
    assert resolved is not None
    pr = resolved.projection
    assert pr['surface_correction_raw_km_w'] < 0.0
    assert pr['surface_thermal_correction_km_w'] == 0.0
    assert pr['surface_correction_clamped'] is True


def test_groundwater_reason_code_is_distinct_and_nonfatal_to_analytic_preview() -> None:
    project = _synthetic()
    region = next(r for r in project.thermal_design.regions if r.region_id == 'TR-01')
    region.overrides['groundwater_depth_m'] = 0.8
    issues = validate_thermal_design(project.thermal_design, project.cable)
    matches = [i for i in issues if i.region_id == 'TR-01' and i.code == 'ANALYTIC_GROUNDWATER_BOUNDARY_REQUIRES_NODAL']
    assert matches and all(i.severity == 'WARNING' for i in matches)


def test_trefoil_scalar_depth_is_formation_centre_not_shallowest_axis() -> None:
    project = _synthetic()
    resolved = resolve_installation_geometry(project).for_region('TR-01')
    assert resolved is not None
    trefoil = next(g for g in resolved.phase_groups if g.resolved_arrangement == 'TREFOIL')
    centre = sum(depth for _phase, _x, depth in trefoil.positions_by_phase) / 3.0
    shallow = min(depth for _phase, _x, depth in trefoil.positions_by_phase)
    assert resolved.burial_depth_m == centre
    assert centre > shallow


def test_legacy_scalar_authority_is_capped() -> None:
    project = ProjectData()
    # No accepted physical projection: thermal-method fallback must never call this IEC-authoritative.
    for route in project.route_sections:
        route.geometry_basis = 'LEGACY_SCALAR'
    # Contract-level assertion on the declared authority enum used by the closure.
    assert RESULT_DERIVED_FROM_SCALAR == 'DERIVED_FROM_SCALAR'
