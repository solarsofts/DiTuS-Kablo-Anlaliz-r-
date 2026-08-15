from __future__ import annotations

from copy import deepcopy

import pytest

from ucd.calculations.nodal_thermal import solve_nodal_route
from ucd.calculations.transient_thermal import (
    TransientThermalInputError,
    solve_transient_route,
)
from ucd.models.project import LoadProfilePoint, ProjectData, TransientLoadProfile


def _quick_project() -> ProjectData:
    project = ProjectData()
    project.thermal_design.regions = project.thermal_design.regions[:1]
    project.thermal_design.route_length_m = project.thermal_design.regions[0].end_m
    project.route_sections = project.route_sections[:1]
    template = project.thermal_design.templates[0]
    template.nodal_base_step_m = 0.35
    template.nodal_refined_step_m = 0.12
    template.nodal_refinement_radius_m = 0.25
    template.nodal_max_cells = 10000
    settings = project.transient_study
    settings.selected_region_ids = ["TR-01"]
    settings.time_step_minutes = 120.0
    settings.transient_mesh_scale = 1.8
    settings.maximum_preconditioning_cycles = 2
    settings.cyclic_convergence_tolerance_c = 0.5
    settings.calculate_cyclic_rating = False
    settings.calculate_emergency_rating = False
    settings.profiles = [
        TransientLoadProfile(
            "TEST",
            "Test çevrimi",
            6.0,
            "STEP",
            [
                LoadProfilePoint(0.0, 0.50, "Düşük"),
                LoadProfilePoint(2.0, 1.00, "Tepe"),
                LoadProfilePoint(4.0, 0.70, "Azalma"),
                LoadProfilePoint(6.0, 0.50, "Son"),
            ],
        )
    ]
    settings.active_profile_id = "TEST"
    return project


@pytest.fixture(scope="module")
def steady_result():
    return solve_nodal_route(_quick_project())


def test_transient_profile_produces_time_series(steady_result) -> None:
    project = _quick_project()
    result = solve_transient_route(project, nodal_result=steady_result)
    region = result.regions[0]
    assert region.points[0].time_h == 0.0
    assert region.points[-1].time_h == pytest.approx(6.0)
    assert len(region.points) == 4
    assert region.maximum_conductor_temperature_c > region.maximum_jacket_temperature_c


def test_higher_load_profile_increases_peak_temperature(steady_result) -> None:
    low = _quick_project()
    high = _quick_project()
    for point in low.transient_study.profiles[0].points:
        point.current_multiplier *= 0.60
    for point in high.transient_study.profiles[0].points:
        point.current_multiplier *= 1.20
    low_result = solve_transient_route(low, nodal_result=steady_result).regions[0]
    high_result = solve_transient_route(high, nodal_result=steady_result).regions[0]
    assert high_result.maximum_conductor_temperature_c > low_result.maximum_conductor_temperature_c


def test_higher_heat_capacity_reduces_short_peak(steady_result) -> None:
    baseline = _quick_project()
    high_capacity = _quick_project()
    high_capacity.transient_study.cable_outer_heat_capacity_mj_m3k = 3.2
    for material in high_capacity.thermal_design.materials:
        material.volumetric_heat_capacity_mj_m3k = 3.0
    base_result = solve_transient_route(baseline, nodal_result=steady_result).regions[0]
    high_result = solve_transient_route(high_capacity, nodal_result=steady_result).regions[0]
    assert high_result.maximum_conductor_temperature_c < base_result.maximum_conductor_temperature_c


def test_cyclic_and_emergency_ratings_are_calculated(steady_result) -> None:
    project = _quick_project()
    project.transient_study.calculate_cyclic_rating = True
    project.transient_study.calculate_emergency_rating = True
    project.transient_study.emergency_duration_h = 2.0
    result = solve_transient_route(project, nodal_result=steady_result).regions[0]
    assert result.cyclic_rating_per_cable_a > 0
    assert result.emergency_rating_per_cable_a > 0
    assert result.cyclic_rating_factor > 0


def test_longer_emergency_duration_reduces_rating(steady_result) -> None:
    short = _quick_project()
    long = _quick_project()
    short.transient_study.calculate_emergency_rating = True
    long.transient_study.calculate_emergency_rating = True
    short.transient_study.emergency_duration_h = 1.0
    long.transient_study.emergency_duration_h = 6.0
    short_result = solve_transient_route(short, nodal_result=steady_result).regions[0]
    long_result = solve_transient_route(long, nodal_result=steady_result).regions[0]
    assert long_result.emergency_rating_per_cable_a < short_result.emergency_rating_per_cable_a


def test_invalid_profile_is_rejected(steady_result) -> None:
    project = _quick_project()
    project.transient_study.profiles[0].points[-1].time_h = 5.0
    with pytest.raises(TransientThermalInputError):
        solve_transient_route(project, nodal_result=steady_result)


def test_v012_migration_adds_transient_defaults() -> None:
    raw = ProjectData().to_dict()
    raw["schema_version"] = "0.12"
    raw.pop("transient_study", None)
    loaded = ProjectData.from_dict(raw)
    assert loaded.schema_version == "0.16.4"
    assert loaded.transient_study.profiles
    assert loaded.transient_study.time_step_minutes > 0
