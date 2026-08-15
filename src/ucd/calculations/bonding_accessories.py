from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ucd.models.project import (
    BONDING_CROSS,
    BondingConnection,
    BondingLinkBox,
    BondingMinorSection,
    BondingNode,
    BondingSystemData,
)

BOUNDARY_MINOR_CROSS = "MINOR_CROSS_BOUNDARY"
BOUNDARY_MAJOR_GROUND = "MAJOR_GROUND_BOUNDARY"
BOUNDARY_ENGINEERING_REVIEW = "ENGINEERING_REVIEW"

LINK_BOX_CROSS = "CROSS_BONDING_LINK_BOX"
LINK_BOX_GROUND = "GROUNDING_LINK_BOX"
LINK_BOX_CUSTOM = "CUSTOM_LINK_BOX"

ACCESSORY_VALID = "VALID"
ACCESSORY_INCOMPLETE = "INCOMPLETE"
ACCESSORY_INVALID = "INVALID"


@dataclass(frozen=True)
class BondingAccessoryItem:
    node_id: str
    link_box_id: str
    position_m: float
    boundary_role: str
    link_box_role: str
    svl_requirement: str
    svl_set_count_per_circuit: int
    svl_pole_count_per_circuit: int
    status: str
    error_codes: tuple[str, ...] = ()
    trace: tuple[str, ...] = ()


@dataclass(frozen=True)
class BondingAccessoryPlan:
    status: str
    items: tuple[BondingAccessoryItem, ...]
    cross_boundary_count: int
    major_ground_boundary_count: int
    cross_link_box_units_per_circuit: int
    grounding_link_box_units_per_circuit: int
    custom_link_box_units_per_circuit: int
    total_link_box_units_per_circuit: int
    svl_set_units_per_circuit: int
    svl_pole_units_per_circuit: int
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class BondingAccessoryInputError(ValueError):
    pass


def _connections_for(
    connections: Iterable[BondingConnection],
    node_id: str,
    link_box_id: str,
) -> list[BondingConnection]:
    return [
        item for item in connections
        if item.node_id == node_id or (link_box_id and item.link_box_id == link_box_id)
    ]


def _cross_graph_valid(connections: list[BondingConnection]) -> bool:
    graph = {
        item.from_sheath.upper(): item.to_sheath.upper()
        for item in connections
        if item.connection_type.strip().upper() == "CROSS"
    }
    if set(graph) != set("ABC") or set(graph.values()) != set("ABC"):
        return False
    return all(graph[phase] != phase for phase in "ABC")


def _solid_ground_graph_valid(connections: list[BondingConnection]) -> bool:
    grounded = {
        item.from_sheath.upper()
        for item in connections
        if item.connection_type.strip().upper() == "SOLID_GROUND"
        and item.to_sheath.strip().upper() in {"G", "GROUND", "EARTH"}
    }
    return grounded == set("ABC")


def resolve_bonding_accessory_plan(bonding: BondingSystemData) -> BondingAccessoryPlan:
    """Resolve link-box and SVL quantities from the electrical bonding graph.

    ``contains_svl`` is treated as a legacy installation/cache flag and is
    checked against the graph-derived requirement; it is never the quantity
    authority.
    """

    minors = list(bonding.minor_sections)
    node_by_id = {item.node_id: item for item in bonding.nodes}
    box_by_joint = {item.joint_node_id: item for item in bonding.link_boxes}
    errors: list[str] = []
    warnings: list[str] = []
    items: list[BondingAccessoryItem] = []

    if bonding.scheme != BONDING_CROSS:
        return BondingAccessoryPlan(
            status=ACCESSORY_INCOMPLETE,
            items=(),
            cross_boundary_count=0,
            major_ground_boundary_count=0,
            cross_link_box_units_per_circuit=0,
            grounding_link_box_units_per_circuit=0,
            custom_link_box_units_per_circuit=0,
            total_link_box_units_per_circuit=0,
            svl_set_units_per_circuit=0,
            svl_pole_units_per_circuit=0,
            warnings=("SVL_PLACEMENT_ENGINEERING_REVIEW",),
        )

    if len(minors) < 2:
        return BondingAccessoryPlan(
            status=ACCESSORY_INCOMPLETE,
            items=(),
            cross_boundary_count=0,
            major_ground_boundary_count=0,
            cross_link_box_units_per_circuit=0,
            grounding_link_box_units_per_circuit=0,
            custom_link_box_units_per_circuit=0,
            total_link_box_units_per_circuit=0,
            svl_set_units_per_circuit=0,
            svl_pole_units_per_circuit=0,
            errors=("LINK_BOX_CONNECTION_GRAPH_INCOMPLETE",),
        )

    for left, right in zip(minors, minors[1:]):
        joint_id = left.end_node_id
        local_errors: list[str] = []
        trace: list[str] = [
            f"{left.section_id}(major={left.major_index}) -> {right.section_id}(major={right.major_index})"
        ]
        if right.start_node_id != joint_id:
            local_errors.append("LINK_BOX_CONNECTION_GRAPH_INCOMPLETE")
        node: BondingNode | None = node_by_id.get(joint_id)
        box: BondingLinkBox | None = box_by_joint.get(joint_id)
        if node is None or box is None:
            local_errors.append("LINK_BOX_CONNECTION_GRAPH_INCOMPLETE")
            role = BOUNDARY_ENGINEERING_REVIEW
            box_role = LINK_BOX_CUSTOM
            svl_required = "ENGINEERING_REVIEW"
            position = float(node.position_m) if node else 0.0
            box_id = box.link_box_id if box else ""
        else:
            position = float(box.position_m)
            box_id = box.link_box_id
            conns = _connections_for(bonding.connections, joint_id, box_id)
            major_boundary = int(left.major_index) != int(right.major_index)
            if major_boundary:
                role = BOUNDARY_MAJOR_GROUND
                box_role = LINK_BOX_GROUND
                svl_required = "NOT_REQUIRED"
                if not _solid_ground_graph_valid(conns) or not bool(node.grounded):
                    local_errors.append("BONDING_MAJOR_BOUNDARY_NOT_GROUNDED")
                if bool(box.contains_svl):
                    local_errors.append("SVL_NOT_REQUIRED_AT_SOLID_GROUND_BOUNDARY")
            else:
                role = BOUNDARY_MINOR_CROSS
                box_role = LINK_BOX_CROSS
                svl_required = "REQUIRED"
                if not _cross_graph_valid(conns):
                    local_errors.append("BONDING_MINOR_BOUNDARY_NOT_CROSS_CONNECTED")
                if not bool(box.contains_svl):
                    local_errors.append("SVL_REQUIRED_BUT_OMITTED")
        status = ACCESSORY_INVALID if local_errors else ACCESSORY_VALID
        errors.extend(f"{joint_id}:{code}" for code in local_errors)
        items.append(BondingAccessoryItem(
            node_id=joint_id,
            link_box_id=box_id,
            position_m=position,
            boundary_role=role,
            link_box_role=box_role,
            svl_requirement=svl_required,
            svl_set_count_per_circuit=1 if svl_required == "REQUIRED" else 0,
            svl_pole_count_per_circuit=3 if svl_required == "REQUIRED" else 0,
            status=status,
            error_codes=tuple(local_errors),
            trace=tuple(trace),
        ))

    cross = sum(item.boundary_role == BOUNDARY_MINOR_CROSS for item in items)
    major = sum(item.boundary_role == BOUNDARY_MAJOR_GROUND for item in items)
    custom = sum(item.link_box_role == LINK_BOX_CUSTOM for item in items)
    status = ACCESSORY_INVALID if errors else (ACCESSORY_INCOMPLETE if warnings else ACCESSORY_VALID)
    return BondingAccessoryPlan(
        status=status,
        items=tuple(items),
        cross_boundary_count=cross,
        major_ground_boundary_count=major,
        cross_link_box_units_per_circuit=cross,
        grounding_link_box_units_per_circuit=major,
        custom_link_box_units_per_circuit=custom,
        total_link_box_units_per_circuit=len(items),
        svl_set_units_per_circuit=sum(item.svl_set_count_per_circuit for item in items),
        svl_pole_units_per_circuit=sum(item.svl_pole_count_per_circuit for item in items),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
