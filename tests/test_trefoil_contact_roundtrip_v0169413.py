from __future__ import annotations

from math import hypot

import pytest

from ucd.calculations.cable_channel_templates import lock_trefoil_centres_to_outer_diameter
from ucd.calculations.installation import validate_installation_design
from ucd.calculations.thermal_resistance import ThermalInputError, direct_buried_thermal_matrix_km_w
from ucd.models.project import ProjectData


def _pair_distances(points: dict[str, tuple[float, float]]) -> tuple[float, float, float]:
    return tuple(
        hypot(points[first][0] - points[second][0], points[first][1] - points[second][1])
        for first, second in (("A", "B"), ("B", "C"), ("C", "A"))
    )


def test_five_decimal_sixty_mm_trefoil_is_contact_not_overlap() -> None:
    diameter = 0.060
    # Exact lower offset is 0.051961524... m.  The Kablo-Kanal table used to
    # write 0.05196 m, shortening two sides by about 1.3 micrometres.
    positions = ((0.0, 1.20000), (-0.03000, 1.25196), (0.03000, 1.25196))
    matrix = direct_buried_thermal_matrix_km_w(positions, diameter * 1000.0, 1.0)
    assert len(matrix) == 3


def test_material_penetration_beyond_contact_tolerance_is_still_rejected() -> None:
    diameter = 0.060
    positions = ((0.0, 1.20), (-0.0290, 1.25023), (0.0290, 1.25023))
    with pytest.raises(ThermalInputError):
        direct_buried_thermal_matrix_km_w(positions, diameter * 1000.0, 1.0)


def test_current_project_load_repairs_rounded_trefoil_to_exact_outer_diameter() -> None:
    project = ProjectData()
    diameter = project.cable.overall_diameter_mm / 1000.0
    raw = project.to_dict()
    raw["installation_design"]["model_revision"] = "0.16.9.4.12"
    section = raw["installation_design"]["cross_sections"][0]
    for cable in section["physical_cables"]:
        if cable["circuit_id"] == "C1":
            cable["x_m"] = round(float(cable["x_m"]), 5)
            cable["depth_m"] = round(float(cable["depth_m"]), 5)

    loaded = ProjectData.from_dict(raw)
    loaded_section = loaded.installation_design.cross_sections[0]
    points = {
        item.phase: (item.x_m, item.depth_m)
        for item in loaded_section.physical_cables
        if item.circuit_id == "C1" and int(item.parallel_index) == 1
    }
    assert all(abs(value - diameter) < 1e-12 for value in _pair_distances(points))
    assert loaded.installation_design.model_revision == "0.16.9.4.34"
    assert "CABLE_OVERLAP" not in {item.code for item in validate_installation_design(loaded)}


def test_explicit_trefoil_lock_preserves_group_centroid_and_sets_exact_pitch() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    diameter = project.cable.overall_diameter_mm / 1000.0
    group = [
        item for item in section.physical_cables
        if item.circuit_id == "C1" and int(item.parallel_index) == 1
    ]
    for item in group:
        item.x_m = round(item.x_m + 0.12345678, 5)
        item.depth_m = round(item.depth_m + 0.23456789, 5)
    before = (
        sum(item.x_m for item in group) / 3.0,
        sum(item.depth_m for item in group) / 3.0,
    )

    moved = lock_trefoil_centres_to_outer_diameter(section, diameter, ["C1"])
    after = (
        sum(item.x_m for item in group) / 3.0,
        sum(item.depth_m for item in group) / 3.0,
    )
    points = {item.phase: (item.x_m, item.depth_m) for item in group}

    assert moved >= 3
    assert after == pytest.approx(before, abs=1e-14)
    assert all(abs(value - diameter) < 1e-12 for value in _pair_distances(points))
