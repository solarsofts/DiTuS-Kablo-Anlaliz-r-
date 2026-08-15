from __future__ import annotations

import math

from ucd.calculations.bonding import (
    optimize_cross_bonding,
    physical_sheath_impedance_matrix_ohm_km,
    resolve_major_paths,
    solve_bonding,
)
from ucd.models.project import (
    BONDING_SINGLE_POINT,
    BONDING_SOLID_BOTH_END,
    ProjectData,
    RouteSection,
)


def test_equal_cross_bonded_minor_sections_cancel_major_section_emf() -> None:
    project = ProjectData()
    project.bonding.solver_mode = "COUPLED_LOOP_MATRIX"
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert result.lambda1 < 1e-12
    assert max(loop.residual_emf_magnitude_v for loop in result.loop_results) < 1e-9
    assert result.max_standing_voltage_v > 0
    assert {loop.sheath_path for loop in result.loop_results} == {
        ("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B")
    }


def test_unequal_minor_sections_create_residual_emf_and_sheath_loss() -> None:
    project = ProjectData()
    project.bonding.nodes[2].position_m *= 1.10
    project.bonding.minor_sections[1].length_m = (
        project.bonding.nodes[2].position_m - project.bonding.nodes[1].position_m
    )
    project.bonding.minor_sections[2].length_m = (
        project.bonding.nodes[3].position_m - project.bonding.nodes[2].position_m
    )
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert result.lambda1 > 0
    assert result.total_sheath_loss_w > 0
    assert all(loop.current_magnitude_a > 0 for loop in result.loop_results)


def test_single_point_has_zero_circulating_current_but_nonzero_standing_voltage() -> None:
    project = ProjectData()
    project.bonding.scheme = BONDING_SINGLE_POINT
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert math.isclose(result.lambda1, 0.0, abs_tol=1e-15)
    assert result.max_standing_voltage_v > 0
    assert all(math.isclose(loop.current_magnitude_a, 0.0, abs_tol=1e-15) for loop in result.loop_results)


def test_solid_both_end_has_higher_loss_than_balanced_cross_bonding() -> None:
    project = ProjectData()
    cross = solve_bonding(project.cable, project.bonding, project.route_sections)
    project.bonding.scheme = BONDING_SOLID_BOTH_END
    solid = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert solid.lambda1 > cross.lambda1
    assert solid.total_sheath_loss_w > cross.total_sheath_loss_w


def test_sheath_resistance_falls_when_screen_area_increases() -> None:
    from ucd.calculations.cable_library import synchronize_cable_from_layers

    project = ProjectData()
    base = solve_bonding(project.cable, project.bonding, project.route_sections)
    screen = next(
        layer for layer in project.cable.layers
        if layer.layer_type in {"METALLIC_SCREEN", "WIRE_SCREEN", "METALLIC_SHEATH"}
    )
    screen.conductor_area_mm2 *= 2
    synchronize_cable_from_layers(project.cable)
    larger = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert larger.sheath_resistance_operating_ohm_km < base.sheath_resistance_operating_ohm_km


def test_explicit_cross_connection_graph_controls_sheath_paths() -> None:
    project = ProjectData()
    # Reverse the second link-box mapping while keeping a valid permutation.
    for connection in project.bonding.connections:
        if connection.link_box_id == "LB2":
            connection.to_sheath = {"A": "C", "B": "A", "C": "B"}[connection.from_sheath]
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    paths = {loop.sheath_path for loop in result.loop_results}
    assert paths == {("A", "B", "A"), ("B", "C", "B"), ("C", "A", "C")}


def test_joint_and_link_box_are_separate_objects() -> None:
    project = ProjectData()
    assert {node.node_id for node in project.bonding.nodes} >= {"J1", "J2"}
    assert {box.link_box_id for box in project.bonding.link_boxes} == {"LB1", "LB2"}
    assert {box.joint_node_id for box in project.bonding.link_boxes} == {"J1", "J2"}


def test_automatic_design_uses_multiple_major_sections_when_voltage_limit_is_low() -> None:
    project = ProjectData()
    project.route_sections = [
        RouteSection("RS-A", 500.0, phase_spacing_m=0.15),
        RouteSection("RS-B", 500.0, phase_spacing_m=0.50),
    ]
    design = optimize_cross_bonding(
        project.cable, project.route_sections, project.bonding, voltage_limit_v=30.0
    )
    assert design.minor_section_count % 3 == 0
    assert design.major_section_count >= 2
    assert design.calculation.max_standing_voltage_v <= 30.0 + 1e-6
    assert len(design.bonding.link_boxes) == design.minor_section_count - 1


def test_route_spacing_changes_are_integrated_in_minor_voltage() -> None:
    project = ProjectData()
    uniform = solve_bonding(project.cable, project.bonding, project.route_sections)
    project.route_sections[1].phase_spacing_m = 0.50
    project.route_sections[2].phase_spacing_m = 0.50
    changed = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert changed.max_standing_voltage_v != uniform.max_standing_voltage_v


def test_visual_loop_states_are_abc_bca_cab_from_connection_graph() -> None:
    project = ProjectData()
    paths = resolve_major_paths(project.bonding, tuple(project.bonding.minor_sections[:3]))
    assert paths == (("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B"))
    # Per-minor physical occupancy of continuous Loop A/B/C. This is exactly
    # what the v0.7 diagram renders on the A/B/C physical sheath lanes.
    occupancy = tuple(tuple(path[i] for path in paths) for i in range(3))
    assert occupancy == (("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B"))


def test_flat_formation_has_symmetric_nonzero_mutual_loop_coupling() -> None:
    project = ProjectData()
    project.cable.arrangement = "Flat"
    matrix = physical_sheath_impedance_matrix_ohm_km(
        project.cable, project.bonding, project.bonding.phase_spacing_m
    )
    assert matrix.shape == (3, 3)
    assert abs(matrix[0, 1]) > 0
    assert abs(matrix[0, 2]) > 0
    assert abs(matrix[0, 1] - matrix[1, 0]) < 1e-12
    assert abs(matrix[0, 2] - matrix[2, 0]) < 1e-12


def test_coupled_complex_matrix_changes_unequal_flat_loop_currents() -> None:
    project = ProjectData()
    project.cable.arrangement = "Flat"
    project.bonding.nodes[2].position_m *= 1.10
    project.bonding.minor_sections[1].length_m = (
        project.bonding.nodes[2].position_m - project.bonding.nodes[1].position_m
    )
    project.bonding.minor_sections[2].length_m = (
        project.bonding.nodes[3].position_m - project.bonding.nodes[2].position_m
    )
    project.bonding.solver_mode = "COUPLED_LOOP_MATRIX"
    coupled = solve_bonding(project.cable, project.bonding, project.route_sections)
    project.bonding.solver_mode = "INDEPENDENT_LOOP_PREVIEW"
    independent = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert coupled.major_matrix_results
    assert coupled.maximum_matrix_condition_number >= 1.0
    differences = [
        abs(a.current_magnitude_a - b.current_magnitude_a)
        for a, b in zip(coupled.loop_results, independent.loop_results)
    ]
    assert max(differences) > 0.1


def test_ideal_cancellation_is_flagged_as_model_condition_not_real_zero_claim() -> None:
    project = ProjectData()
    project.bonding.solver_mode = "COUPLED_LOOP_MATRIX"
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    assert result.ideal_cancellation
    assert result.solver_mode == "COUPLED_LOOP_MATRIX"
    assert any("gerçek akımın sıfır" in note for note in result.notes)


def test_mutual_coupling_toggle_removes_off_diagonal_terms() -> None:
    project = ProjectData()
    project.cable.arrangement = "Flat"
    project.bonding.sheath_mutual_coupling_enabled = False
    matrix = physical_sheath_impedance_matrix_ohm_km(
        project.cable, project.bonding, project.bonding.phase_spacing_m
    )
    assert all(abs(matrix[i, j]) < 1e-15 for i in range(3) for j in range(3) if i != j)


def test_cross_bond_standing_profile_accumulates_complex_emf_along_resolved_paths() -> None:
    project = ProjectData()
    project.bonding.solver_mode = "COUPLED_LOOP_MATRIX"
    # Deliberately unbalance the middle minor so vector accumulation cannot be
    # mistaken for plotting each minor's own |E|.
    project.bonding.nodes[2].position_m *= 1.13
    project.bonding.minor_sections[1].length_m = (
        project.bonding.nodes[2].position_m - project.bonding.nodes[1].position_m
    )
    project.bonding.minor_sections[2].length_m = (
        project.bonding.nodes[3].position_m - project.bonding.nodes[2].position_m
    )
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

    # start, three cumulative joint/end points, then grounded reset at same end chainage
    profile = result.standing_voltage_profile
    assert len(profile) >= 5
    assert math.isclose(profile[0].voltage_v, 0.0, abs_tol=1e-12)
    for point, target in zip(profile[1:4], expected):
        assert math.isclose(point.voltage_v, target, rel_tol=1e-12, abs_tol=1e-12)
    assert profile[4].chainage_m == profile[3].chainage_m
    assert math.isclose(profile[4].voltage_v, 0.0, abs_tol=1e-12)
    assert math.isclose(result.max_standing_voltage_v, max(expected), rel_tol=1e-12)


def test_primitive_bonding_profile_uses_solved_sheath_to_earth_node_voltages() -> None:
    project = ProjectData()
    project.bonding.solver_mode = "PRIMITIVE_CIM"
    result = solve_bonding(project.cable, project.bonding, project.route_sections)
    primitive = result.primitive_network_result
    assert primitive is not None
    profile = result.standing_voltage_profile
    assert profile
    assert all("solved network" in point.label for point in profile)
    expected_max = max(
        max(
            *(abs(value) for value in section.start_sheath_voltages_v),
            *(abs(value) for value in section.end_sheath_voltages_v),
        )
        for section in primitive.section_results
    )
    assert math.isclose(max(point.voltage_v for point in profile), expected_max, rel_tol=1e-12)
    assert math.isclose(result.max_standing_voltage_v, expected_max, rel_tol=1e-12)
