from ucd.models.project import (
    EXTERNAL_THERMAL_MANUAL,
    INTERNAL_THERMAL_MANUAL,
    ProjectData,
)


def test_v01_project_migrates_with_defaults_and_preserves_manual_thermal_values() -> None:
    raw = {
        "project_name": "Legacy",
        "cable": {"conductor_area_mm2": 1600.0, "thermal_resistance_t1_km_w": 0.44},
        "route_sections": [{"name": "RS", "length_m": 10.0, "external_thermal_resistance_t4_km_w": 1.11}],
    }
    project = ProjectData.from_dict(raw)
    assert project.project_name == "Legacy"
    assert project.schema_version == "0.16.4"
    assert project.cable.conductor_area_mm2 == 1600.0
    assert project.cable.internal_thermal_mode == INTERNAL_THERMAL_MANUAL
    assert project.cable.thermal_resistance_t1_km_w == 0.44
    assert project.route_sections[0].external_thermal_mode == EXTERNAL_THERMAL_MANUAL
    assert project.route_sections[0].external_thermal_resistance_t4_km_w == 1.11
    assert len(project.bonding.minor_sections) == 3
    assert len(project.bonding.nodes) == 4
    assert len(project.bonding.link_boxes) == 2


def test_v03_project_keeps_automatic_modes() -> None:
    raw = {
        "schema_version": "0.3",
        "cable": {"internal_thermal_mode": "AUTO_GEOMETRY"},
        "route_sections": [{"name": "RS", "length_m": 10.0, "external_thermal_mode": "AUTO_IMAGE"}],
    }
    project = ProjectData.from_dict(raw)
    assert project.cable.internal_thermal_mode == "AUTO_GEOMETRY"
    assert project.route_sections[0].external_thermal_mode == "AUTO_IMAGE"


def test_v03_project_gets_default_bonding_graph_without_changing_thermal_modes() -> None:
    raw = {
        "schema_version": "0.3",
        "cable": {"internal_thermal_mode": "AUTO_GEOMETRY"},
        "route_sections": [{"name": "RS", "length_m": 900.0, "external_thermal_mode": "AUTO_IMAGE"}],
    }
    project = ProjectData.from_dict(raw)
    assert project.schema_version == "0.16.4"
    assert project.cable.internal_thermal_mode == "AUTO_GEOMETRY"
    assert project.route_sections[0].external_thermal_mode == "AUTO_IMAGE"
    assert len(project.bonding.minor_sections) == 3
    assert abs(sum(section.length_m for section in project.bonding.minor_sections) - 900.0) < 1e-9


def test_v04_link_box_nodes_migrate_to_separate_joint_and_link_box_objects() -> None:
    raw = {
        "schema_version": "0.4",
        "route_sections": [{"name": "RS", "length_m": 900.0}],
        "bonding": {
            "nodes": [
                {"node_id": "T1", "name": "T1", "position_m": 0.0, "node_type": "TERMINATION", "earth_resistance_ohm": 0.2},
                {"node_id": "LB1", "name": "Link Box 1", "position_m": 300.0, "node_type": "LINK_BOX", "earth_resistance_ohm": 0.0},
                {"node_id": "LB2", "name": "Link Box 2", "position_m": 600.0, "node_type": "LINK_BOX", "earth_resistance_ohm": 0.0},
                {"node_id": "T2", "name": "T2", "position_m": 900.0, "node_type": "TERMINATION", "earth_resistance_ohm": 0.2},
            ],
            "minor_sections": [
                {"section_id": "MS1", "name": "MS1", "start_node_id": "T1", "end_node_id": "LB1", "length_m": 300.0},
                {"section_id": "MS2", "name": "MS2", "start_node_id": "LB1", "end_node_id": "LB2", "length_m": 300.0},
                {"section_id": "MS3", "name": "MS3", "start_node_id": "LB2", "end_node_id": "T2", "length_m": 300.0},
            ],
            "connections": [
                {"node_id": "LB1", "from_sheath": "A", "to_sheath": "B", "connection_type": "CROSS"},
                {"node_id": "LB1", "from_sheath": "B", "to_sheath": "C", "connection_type": "CROSS"},
                {"node_id": "LB1", "from_sheath": "C", "to_sheath": "A", "connection_type": "CROSS"},
                {"node_id": "LB2", "from_sheath": "A", "to_sheath": "B", "connection_type": "CROSS"},
                {"node_id": "LB2", "from_sheath": "B", "to_sheath": "C", "connection_type": "CROSS"},
                {"node_id": "LB2", "from_sheath": "C", "to_sheath": "A", "connection_type": "CROSS"},
            ],
        },
    }
    project = ProjectData.from_dict(raw)
    assert {node.node_type for node in project.bonding.nodes if node.node_id.startswith("J")} == {"SECTIONALIZING_JOINT"}
    assert {box.link_box_id for box in project.bonding.link_boxes} == {"LB1", "LB2"}
    assert project.bonding.minor_sections[0].end_node_id == "J1"
    assert project.bonding.connections[0].link_box_id == "LB1"


def test_v05_project_gets_default_svl_system() -> None:
    project = ProjectData.from_dict({
        "schema_version": "0.5",
        "project_name": "Legacy v0.5",
        "cable": {},
        "route_sections": [],
    })
    assert project.schema_version == "0.16.4"
    assert project.svl.candidates
    assert project.svl.connection_mode == "STAR_GROUNDED"


def test_v06_project_gets_primitive_solver_defaults() -> None:
    project = ProjectData.from_dict({
        "schema_version": "0.6",
        "project_name": "Legacy v0.6",
        "bonding": {},
    })
    assert project.schema_version == "0.16.4"
    assert project.bonding.solver_mode == "PRIMITIVE_CIM"
    assert project.bonding.sheath_mutual_coupling_enabled is True


def test_v07_project_preserves_explicit_legacy_solver_mode() -> None:
    project = ProjectData.from_dict({
        "schema_version": "0.7",
        "bonding": {"solver_mode": "COUPLED_LOOP_MATRIX"},
    })
    assert project.schema_version == "0.16.4"
    assert project.bonding.solver_mode == "COUPLED_LOOP_MATRIX"


def test_v08_primitive_fields_round_trip() -> None:
    project = ProjectData()
    project.bonding.solver_mode = "NODE_VOLTAGE"
    project.bonding.earth_resistivity_ohm_m = 250.0
    project.bonding.gcc_enabled = True
    project.bonding.gcc_area_mm2 = 300.0
    loaded = ProjectData.from_dict(project.to_dict())
    assert loaded.schema_version == "0.16.4"
    assert loaded.bonding.solver_mode == "NODE_VOLTAGE"
    assert loaded.bonding.earth_resistivity_ohm_m == 250.0
    assert loaded.bonding.gcc_enabled
    assert loaded.bonding.gcc_area_mm2 == 300.0


def test_v08_project_gets_default_fault_study_and_v09_round_trip() -> None:
    legacy = ProjectData.from_dict({"schema_version": "0.8", "project_name": "Legacy v0.8"})
    assert legacy.schema_version == "0.16.4"
    assert len(legacy.fault_study.scenarios) == 3
    legacy.fault_study.solver_mode = "NODE_VOLTAGE"
    legacy.fault_study.scenarios[0].fault_current_a = 40000.0
    loaded = ProjectData.from_dict(legacy.to_dict())
    assert loaded.fault_study.solver_mode == "NODE_VOLTAGE"
    assert loaded.fault_study.scenarios[0].fault_current_a == 40000.0
