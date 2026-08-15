from __future__ import annotations

from copy import deepcopy
from math import isclose, sqrt

import pytest

from ucd.calculations.bonding import resolve_major_paths, solve_bonding
from ucd.calculations.bonding_closed_form_validation import (
    CLOSED_FORM_APPLICABLE,
    compare_primitive_network_to_closed_form,
    modified_sectionalized_standing_voltage_factor,
    unequal_minor_cross_bonding_loss_ratio,
)
from ucd.models.project import ProjectData


def _set_minor_ratios(project: ProjectData, ratios: tuple[float, float, float], unit_m: float = 1000.0) -> None:
    lengths = [float(v) * unit_m for v in ratios]
    for minor, length in zip(project.bonding.minor_sections[:3], lengths):
        minor.length_m = length
    positions = (0.0, lengths[0], lengths[0] + lengths[1], sum(lengths))
    for node, position in zip(project.bonding.nodes[:4], positions):
        node.position_m = position
    route = deepcopy(project.route_sections[0])
    route.start_chainage_m = 0.0
    route.end_chainage_m = sum(lengths)
    route.length_m = sum(lengths)
    project.route_sections = [route]


def test_closed_form_standard_fixed_points() -> None:
    assert unequal_minor_cross_bonding_loss_ratio(1.0, 1.0) == pytest.approx(0.0, abs=1e-15)
    assert unequal_minor_cross_bonding_loss_ratio(2.0, 2.0) == pytest.approx(0.04, abs=1e-15)
    assert unequal_minor_cross_bonding_loss_ratio(1.0, 1.2) == pytest.approx(0.00390625, abs=1e-15)


def test_production_primitive_network_matches_2_1_2_closed_form_ratio() -> None:
    project = ProjectData()
    _set_minor_ratios(project, (2.0, 1.0, 2.0))
    check = compare_primitive_network_to_closed_form(project.cable, project.bonding, project.route_sections)
    assert check.applicability == CLOSED_FORM_APPLICABLE
    assert check.expected_ratio == pytest.approx(0.04, abs=1e-15)
    assert check.network_ratio == pytest.approx(0.04, abs=5e-4)


def test_production_primitive_network_matches_1_1_1p2_closed_form_ratio() -> None:
    project = ProjectData()
    _set_minor_ratios(project, (1.0, 1.0, 1.2))
    check = compare_primitive_network_to_closed_form(project.cable, project.bonding, project.route_sections)
    assert check.applicability == CLOSED_FORM_APPLICABLE
    assert check.expected_ratio == pytest.approx(0.00390625, abs=1e-15)
    assert check.network_ratio == pytest.approx(check.expected_ratio, abs=1e-4)


def test_annex_d4_modified_sectionalized_voltage_benchmark() -> None:
    factor = modified_sectionalized_standing_voltage_factor()
    assert factor == pytest.approx(sqrt(3.0) / 2.0, abs=1e-15)
    assert (1.0 - factor) * 100.0 == pytest.approx(13.3974596216, abs=1e-9)


def test_standing_profile_accumulates_complex_minor_emf_and_resets_at_major_ground() -> None:
    project = ProjectData()
    project.bonding.solver_mode = "COUPLED_LOOP_MATRIX"
    _set_minor_ratios(project, (1.0, 1.13, 0.87))
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    group = result.minor_results[:3]
    paths = resolve_major_paths(project.bonding, tuple(project.bonding.minor_sections[:3]))
    phase_index = {phase: index for index, phase in enumerate("ABC")}
    cumulative = [0j, 0j, 0j]
    expected = []
    for i, minor in enumerate(group):
        for path_index, path in enumerate(paths):
            cumulative[path_index] += minor.sheath_voltage_v[phase_index[path[i]]]
        expected.append(max(abs(value) for value in cumulative))
    profile = result.standing_voltage_profile
    for point, target in zip(profile[1:4], expected):
        assert isclose(point.voltage_v, target, rel_tol=1e-12, abs_tol=1e-12)
    assert profile[4].chainage_m == profile[3].chainage_m
    assert isclose(profile[4].voltage_v, 0.0, abs_tol=1e-12)
