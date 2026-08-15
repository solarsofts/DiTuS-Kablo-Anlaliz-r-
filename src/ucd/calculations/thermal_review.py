from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ucd.calculations.nodal_thermal import NodalRegionResult, NodalRouteStudyResult


@dataclass(frozen=True)
class ThermalReviewSummary:
    scenario_id: str
    scenario_name: str
    region_id: str
    region_name: str
    start_m: float
    end_m: float
    installation_type: str
    design_current_per_cable_a: float
    ampacity_per_cable_a: float
    ampacity_margin_a: float
    maximum_conductor_temperature_c: float
    maximum_jacket_temperature_c: float
    temperature_limit_c: float
    critical_cable_id: str
    critical_cable_temperature_c: float
    iec_ampacity_per_cable_a: float
    difference_from_iec_percent: float
    energy_balance_error_percent: float
    maximum_linear_residual: float
    mesh_nx: int
    mesh_ny: int
    mesh_cell_count: int
    status: str
    is_route_critical: bool
    warnings: tuple[str, ...]


def find_nodal_region_result(
    study: NodalRouteStudyResult,
    scenario_id: str,
    region_id: str,
    scope_id: str = "SCENARIO_COMBINED",
) -> NodalRegionResult | None:
    scenario = study.scope_result(scenario_id, scope_id)
    if scenario is None:
        return None
    return next((item for item in scenario.regions if item.region_id == region_id), None)


def build_thermal_review_summaries(study: NodalRouteStudyResult) -> tuple[ThermalReviewSummary, ...]:
    summaries: list[ThermalReviewSummary] = []
    for scenario in study.scenarios:
        for region in scenario.regions:
            critical = max(
                region.cables,
                key=lambda item: item.conductor_temperature_c,
                default=None,
            )
            summaries.append(ThermalReviewSummary(
                scenario.scenario_id,
                scenario.scenario_name,
                region.region_id,
                region.region_name,
                region.start_m,
                region.end_m,
                region.installation_type,
                region.design_current_per_cable_a,
                region.ampacity_per_cable_a,
                region.ampacity_per_cable_a - region.design_current_per_cable_a,
                region.maximum_conductor_temperature_c,
                region.maximum_jacket_temperature_c,
                region.temperature_limit_c,
                critical.cable_id if critical else "—",
                critical.conductor_temperature_c if critical else region.maximum_conductor_temperature_c,
                region.iec_ampacity_per_cable_a,
                region.difference_from_iec_percent,
                region.energy_balance_error_percent,
                region.maximum_linear_residual,
                region.mesh_nx,
                region.mesh_ny,
                region.mesh_cell_count,
                region.status,
                region.region_id == scenario.critical_region_id,
                tuple(region.warnings),
            ))
    return tuple(summaries)


def review_order(study: NodalRouteStudyResult) -> tuple[ThermalReviewSummary, ...]:
    """Return active-scenario results first, with the lowest margin first.

    This ordering is used by the review workspace so the route-limiting section
    remains visible without hiding results from the other load scenarios.
    """
    summaries = build_thermal_review_summaries(study)
    return tuple(sorted(
        summaries,
        key=lambda item: (
            0 if item.scenario_id == study.active_scenario_id else 1,
            item.ampacity_margin_a,
            item.start_m,
            item.region_id,
        ),
    ))


BoundarySegment = tuple[float, float, float, float]


def _shape_ok(
    x_edges: Iterable[float],
    depth_edges: Iterable[float],
    rows: Iterable[Iterable[object]],
) -> tuple[list[float], list[float], list[list[object]]]:
    xs = [float(value) for value in x_edges]
    ys = [float(value) for value in depth_edges]
    matrix = [list(row) for row in rows]
    if len(xs) < 2 or len(ys) < 2:
        return xs, ys, []
    ny = len(ys) - 1
    nx = len(xs) - 1
    if len(matrix) != ny or any(len(row) != nx for row in matrix):
        return xs, ys, []
    return xs, ys, matrix


def extract_material_boundary_segments(
    x_edges: Iterable[float],
    depth_edges: Iterable[float],
    material_ids: Iterable[Iterable[str]],
) -> tuple[BoundarySegment, ...]:
    """Extract internal cell-edge boundaries where material identity changes."""
    xs, ys, matrix = _shape_ok(x_edges, depth_edges, material_ids)
    if not matrix:
        return ()
    ny = len(matrix)
    nx = len(matrix[0])
    segments: list[BoundarySegment] = []
    for iy in range(ny):
        for ix in range(1, nx):
            if matrix[iy][ix - 1] != matrix[iy][ix]:
                segments.append((xs[ix], ys[iy], xs[ix], ys[iy + 1]))
    for iy in range(1, ny):
        for ix in range(nx):
            if matrix[iy - 1][ix] != matrix[iy][ix]:
                segments.append((xs[ix], ys[iy], xs[ix + 1], ys[iy]))
    return tuple(segments)


def extract_quantized_isotherm_segments(
    x_edges: Iterable[float],
    depth_edges: Iterable[float],
    temperature_c: Iterable[Iterable[float]],
    level_count: int = 6,
) -> tuple[BoundarySegment, ...]:
    """Create a stable, inexpensive contour approximation on cell boundaries.

    This is deliberately a display helper, not a replacement for the numerical
    solution. Adjacent cells are assigned to temperature bands; a line is drawn
    where the band changes.
    """
    xs, ys, matrix = _shape_ok(x_edges, depth_edges, temperature_c)
    if not matrix or level_count < 2:
        return ()
    flat = [float(value) for row in matrix for value in row]
    tmin = min(flat)
    tmax = max(flat)
    span = tmax - tmin
    if span <= 1e-12:
        return ()

    def band(value: object) -> int:
        ratio = (float(value) - tmin) / span
        return min(level_count - 1, max(0, int(ratio * level_count)))

    ny = len(matrix)
    nx = len(matrix[0])
    segments: list[BoundarySegment] = []
    for iy in range(ny):
        for ix in range(1, nx):
            if band(matrix[iy][ix - 1]) != band(matrix[iy][ix]):
                segments.append((xs[ix], ys[iy], xs[ix], ys[iy + 1]))
    for iy in range(1, ny):
        for ix in range(nx):
            if band(matrix[iy - 1][ix]) != band(matrix[iy][ix]):
                segments.append((xs[ix], ys[iy], xs[ix + 1], ys[iy]))
    return tuple(segments)
