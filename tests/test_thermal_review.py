from __future__ import annotations

from ucd.calculations.nodal_thermal import solve_nodal_route
from ucd.calculations.thermal_review import (
    build_thermal_review_summaries,
    extract_material_boundary_segments,
    extract_quantized_isotherm_segments,
    find_nodal_region_result,
    review_order,
)
from ucd.models.project import ProjectData


def test_review_summaries_include_all_scenarios_and_regions() -> None:
    study = solve_nodal_route(ProjectData())
    summaries = build_thermal_review_summaries(study)
    assert len(summaries) == sum(len(item.regions) for item in study.scenarios)
    assert any(item.is_route_critical for item in summaries)
    assert all(item.ampacity_margin_a == item.ampacity_per_cable_a - item.design_current_per_cable_a for item in summaries)


def test_review_order_puts_active_scenario_and_lowest_margin_first() -> None:
    study = solve_nodal_route(ProjectData())
    ordered = review_order(study)
    active = [item for item in ordered if item.scenario_id == study.active_scenario_id]
    assert ordered[0].scenario_id == study.active_scenario_id
    assert [item.ampacity_margin_a for item in active] == sorted(item.ampacity_margin_a for item in active)


def test_find_region_result_returns_exact_scenario_region_pair() -> None:
    study = solve_nodal_route(ProjectData())
    target = study.active.regions[-1]
    found = find_nodal_region_result(study, study.active_scenario_id, target.region_id)
    assert found is target
    assert find_nodal_region_result(study, "missing", target.region_id) is None


def test_material_boundaries_are_extracted_only_at_material_changes() -> None:
    segments = extract_material_boundary_segments(
        (0.0, 1.0, 2.0),
        (0.0, 1.0, 2.0),
        (("SOIL", "SOIL"), ("SOIL", "GROUT")),
    )
    assert set(segments) == {(1.0, 1.0, 1.0, 2.0), (1.0, 1.0, 2.0, 1.0)}


def test_quantized_isotherms_are_empty_for_uniform_field() -> None:
    assert extract_quantized_isotherm_segments(
        (0.0, 1.0, 2.0),
        (0.0, 1.0, 2.0),
        ((25.0, 25.0), (25.0, 25.0)),
    ) == ()


def test_quantized_isotherms_detect_temperature_band_change() -> None:
    segments = extract_quantized_isotherm_segments(
        (0.0, 1.0, 2.0),
        (0.0, 1.0, 2.0),
        ((25.0, 25.0), (25.0, 75.0)),
        level_count=4,
    )
    assert segments
