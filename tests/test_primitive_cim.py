from __future__ import annotations

import numpy as np

from ucd.calculations.bonding import solve_bonding
from ucd.calculations.primitive_cim import (
    PrimitiveConductor,
    primitive_impedance_matrix_ohm_km,
    solve_primitive_network,
)
from ucd.models.project import ProjectData, RouteSection


def test_primitive_matrix_is_complex_symmetric_and_contains_earth_return() -> None:
    conductors = (
        PrimitiveConductor("CA", "CORE", "A", 0.0, 1.2, 0.015, 0.02),
        PrimitiveConductor("SA", "SHEATH", "A", 0.0, 1.2, 0.041, 0.20),
        PrimitiveConductor("SB", "SHEATH", "B", 0.3, 1.2, 0.041, 0.20),
    )
    z, de = primitive_impedance_matrix_ohm_km(conductors, 50.0, 100.0, 0.041)
    assert z.shape == (3, 3)
    assert np.allclose(z, z.T)
    assert de > 100.0
    assert z[0, 0].real > conductors[0].resistance_ohm_km
    assert abs(z[0, 1]) > 0


def test_cim_and_node_voltage_agree_on_same_primitive_network() -> None:
    project = ProjectData()
    result = solve_primitive_network(project.cable, project.bonding, project.route_sections)
    assert result.methods_agree
    assert result.maximum_method_voltage_difference_v < 1e-6
    assert result.maximum_method_current_difference_a < 1e-6
    assert result.cim.equation_residual < 1e-10
    assert result.nv.equation_residual < 1e-10


def test_primitive_cross_bonding_has_small_but_nonzero_charging_sheath_current() -> None:
    project = ProjectData()
    project.bonding.solver_mode = "PRIMITIVE_CIM"
    project.bonding.include_dielectric_charging = True
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert result.primitive_network_result is not None
    assert 0.01 < result.primitive_network_result.maximum_sheath_current_a < 10.0
    assert result.lambda1 > 0
    assert not result.ideal_cancellation


def test_disabling_dielectric_charging_reduces_ideal_system_current() -> None:
    project = ProjectData()
    project.bonding.include_dielectric_charging = True
    charged = solve_primitive_network(project.cable, project.bonding, project.route_sections)
    project.bonding.include_dielectric_charging = False
    uncharged = solve_primitive_network(project.cable, project.bonding, project.route_sections)
    assert uncharged.maximum_sheath_current_a < charged.maximum_sheath_current_a


def test_earth_resistivity_changes_primitive_matrix_even_when_balanced_common_mode_cancels() -> None:
    conductors = (
        PrimitiveConductor("CA", "CORE", "A", 0.0, 1.2, 0.015, 0.02),
        PrimitiveConductor("SA", "SHEATH", "A", 0.0, 1.2, 0.041, 0.20),
        PrimitiveConductor("SB", "SHEATH", "B", 0.3, 1.2, 0.041, 0.20),
    )
    low, _ = primitive_impedance_matrix_ohm_km(conductors, 50.0, 20.0, 0.041)
    high, _ = primitive_impedance_matrix_ohm_km(conductors, 50.0, 1000.0, 0.041)
    assert abs(high[0, 0] - low[0, 0]) > 1e-3
    assert abs(high[0, 2] - low[0, 2]) > 1e-3


def test_optional_gcc_is_part_of_primitive_network_and_carries_current() -> None:
    project = ProjectData()
    project.bonding.gcc_enabled = True
    project.bonding.gcc_ground_at_major_boundaries = True
    result = solve_primitive_network(project.cable, project.bonding, project.route_sections)
    assert result.conductor_order == ("A", "B", "C", "GCC")
    assert result.maximum_gcc_current_a > 0
    assert result.total_gcc_metal_loss_w >= 0


def test_route_geometry_changes_primitive_solution() -> None:
    project = ProjectData()
    base = solve_primitive_network(project.cable, project.bonding, project.route_sections)
    project.route_sections[1].phase_spacing_m = 0.50
    changed = solve_primitive_network(project.cable, project.bonding, project.route_sections)
    assert abs(changed.maximum_sheath_current_a - base.maximum_sheath_current_a) > 1e-4


def test_node_voltage_can_be_selected_as_operational_result() -> None:
    project = ProjectData()
    project.bonding.solver_mode = "NODE_VOLTAGE"
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert result.solver_mode == "NODE_VOLTAGE"
    assert result.primitive_network_result.selected_method == "NODE_VOLTAGE"
    assert result.primitive_network_result.methods_agree


def test_long_multi_major_network_solves_sparsely() -> None:
    project = ProjectData()
    project.route_sections = [RouteSection("Long", 9000.0, phase_spacing_m=0.20)]
    from ucd.calculations.bonding import build_cross_bonding_system
    project.bonding = build_cross_bonding_system([i * 1000.0 for i in range(10)], project.bonding)
    project.bonding.solver_mode = "PRIMITIVE_CIM"
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    primitive = result.primitive_network_result
    assert primitive.node_count > 40
    assert primitive.methods_agree
    assert np.isfinite(primitive.maximum_sheath_current_a)
