from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Iterable

from ucd.models.project import (
    CableChannelGeometryData,
    DuctSlotData,
    ExternalHeatSourceData,
    InstallationCircuitData,
    InstallationCrossSectionData,
    InstallationDesignData,
    PhysicalCableData,
    ThermalMaterialRegionData,
    ProjectData,
    THERMAL_INSTALL_DIRECT_BURIED,
    THERMAL_INSTALL_DUCT_BANK,
    THERMAL_INSTALL_HDD,
    THERMAL_INSTALL_CONCRETE_TROUGH,
    THERMAL_INSTALL_TUNNEL,
)


INSTALLATION_REFERENCE = (
    "IEC 60287-1-2:2023 double-circuit sheath-loss geometry; "
    "IEC 60287-1-3:2023 parallel single-core cable current sharing; "
    "IEEE 575-2014 sheath bonding; CIGRE TB 797 sheath bonding systems; "
    "IEC 60287-2-1:2023 trench/duct/trough thermal geometry; IEEE 442-2017 material testing"
)


class InstallationInputError(ValueError):
    pass


def physical_cable_contact_tolerance_m(cable_outer_diameter_m: float) -> float:
    """Numerical tolerance for a jacket-to-jacket cable contact.

    Kablo-Kanal coordinate tables are human-editable and historically display
    metre coordinates to five decimals.  Re-reading an exact equilateral
    TREFOIL through that table can shorten a 60--105 mm centre distance by a
    few micrometres even though the engineering geometry is still touching,
    not overlapping.  This tolerance accepts only that sub-millimetric
    representation error; material penetration beyond it remains invalid.
    """

    diameter = max(0.0, float(cable_outer_diameter_m))
    return max(2.0e-5, diameter * 5.0e-4)


@dataclass(frozen=True)
class InstallationValidationIssue:
    severity: str
    code: str
    message: str
    cross_section_id: str = ""
    object_id: str = ""


@dataclass(frozen=True)
class SectionClearanceRecord:
    category: str
    object_a: str
    object_b: str
    actual_clearance_m: float
    required_clearance_m: float
    status: str
    message: str


@dataclass(frozen=True)
class ResolvedPhysicalCable:
    physical_cable_id: str
    circuit_id: str
    phase: str
    parallel_index: int
    x_m: float
    depth_m: float
    current_a: float
    current_angle_deg: float
    cable_snapshot_id: str
    duct_slot_id: str
    active: bool


@dataclass(frozen=True)
class DirectBuriedEnvelope:
    """Construction envelope of the active physical cable group.

    Depths are measured positive downwards from finished grade.  The bedding
    envelope includes the real cable outside diameter plus the specified sand
    covers below, above and at both sides of the cable group.
    """

    cable_left_m: float
    cable_right_m: float
    cable_top_m: float
    cable_bottom_m: float
    bedding_left_m: float
    bedding_right_m: float
    bedding_top_m: float
    bedding_bottom_m: float
    bedding_height_m: float
    required_bottom_width_m: float


def direct_buried_envelope(
    section: InstallationCrossSectionData,
    cable_outer_diameter_m: float,
) -> DirectBuriedEnvelope:
    cables = [item for item in section.physical_cables if item.active]
    if not cables:
        raise InstallationInputError("Doğrudan gömülü kesitte etkin fiziksel kablo bulunmuyor.")
    diameter = max(float(cable_outer_diameter_m), 0.001)
    radius = diameter / 2.0
    g = section.channel_geometry
    cable_left = min(float(item.x_m) - radius for item in cables)
    cable_right = max(float(item.x_m) + radius for item in cables)
    cable_top = min(float(item.depth_m) - radius for item in cables)
    cable_bottom = max(float(item.depth_m) + radius for item in cables)
    side = max(0.0, float(g.bedding_side_clearance_m))
    top_cover = max(0.0, float(g.bedding_top_cover_m))
    bottom_cover = max(0.0, float(g.bedding_bottom_cover_m))
    bedding_top = max(0.0, cable_top - top_cover)
    bedding_bottom = cable_bottom + bottom_cover
    return DirectBuriedEnvelope(
        cable_left_m=cable_left,
        cable_right_m=cable_right,
        cable_top_m=cable_top,
        cable_bottom_m=cable_bottom,
        bedding_left_m=cable_left - side,
        bedding_right_m=cable_right + side,
        bedding_top_m=bedding_top,
        bedding_bottom_m=bedding_bottom,
        bedding_height_m=max(0.0, bedding_bottom - bedding_top),
        required_bottom_width_m=max(0.20, cable_right - cable_left + 2.0 * side),
    )


def synchronise_direct_buried_geometry(
    section: InstallationCrossSectionData,
    cable_outer_diameter_m: float,
    *,
    anchor_to_trench_bottom: bool | None = None,
    expand_trench_width: bool = True,
) -> DirectBuriedEnvelope:
    """Keep the real cable group inside its sand bedding envelope.

    The function is intentionally limited to the Kablo-Kanal editor model.  It
    does not run or replace any locked IEC/bonding/thermal solver.  When the
    bottom lock is active, all cable depths are shifted together so the
    deepest cable has the requested bottom sand cover.  The solver-facing
    ``bedding_thickness_m`` is then derived from the actual cable envelope.
    """

    if str(section.installation_type).upper() != THERMAL_INSTALL_DIRECT_BURIED:
        return direct_buried_envelope(section, cable_outer_diameter_m)
    active = [item for item in section.physical_cables if item.active]
    if not active:
        raise InstallationInputError("Doğrudan gömülü kesitte etkin fiziksel kablo bulunmuyor.")
    g = section.channel_geometry
    diameter = max(float(cable_outer_diameter_m), 0.001)
    radius = diameter / 2.0
    locked = bool(g.cable_group_bottom_locked) if anchor_to_trench_bottom is None else bool(anchor_to_trench_bottom)
    if locked:
        deepest_centre = max(float(item.depth_m) for item in active)
        target_deepest_centre = max(
            radius,
            float(g.trench_depth_m) - max(0.0, float(g.bedding_bottom_cover_m)) - radius,
        )
        shift = target_deepest_centre - deepest_centre
        for item in active:
            item.depth_m = max(radius, float(item.depth_m) + shift)
    envelope = direct_buried_envelope(section, diameter)
    # Keep the excavation deep enough when the user supplied a free cable
    # depth, otherwise the cable group would visually leave the channel.
    if envelope.bedding_bottom_m > float(g.trench_depth_m):
        g.trench_depth_m = envelope.bedding_bottom_m
        envelope = direct_buried_envelope(section, diameter)
    g.bedding_thickness_m = max(0.0, float(g.trench_depth_m) - envelope.bedding_top_m)
    if expand_trench_width:
        g.trench_width_m = max(float(g.trench_width_m), envelope.required_bottom_width_m)
    return direct_buried_envelope(section, diameter)


def direct_buried_warning_depths(
    section: InstallationCrossSectionData,
    cable_outer_diameter_m: float,
) -> tuple[float | None, float | None]:
    """Return warning-mesh and warning-tape depths above the sand envelope."""

    envelope = direct_buried_envelope(section, cable_outer_diameter_m)
    g = section.channel_geometry
    mesh = None
    tape = None
    if bool(g.warning_mesh_enabled):
        mesh = max(0.02, envelope.bedding_top_m - max(0.0, float(g.warning_mesh_offset_above_bedding_m)))
    if bool(g.warning_tape_enabled):
        tape = max(0.02, envelope.bedding_top_m - max(0.0, float(g.warning_tape_offset_above_bedding_m)))
    return mesh, tape


def phase_angle_deg(phase: str) -> float:
    phase = str(phase).strip().upper()
    if phase == "A":
        return 0.0
    if phase == "B":
        return -120.0
    if phase == "C":
        return 120.0
    raise InstallationInputError(f"Geçersiz faz: {phase!r}; A, B veya C bekleniyor.")


def active_cross_section(project_or_design: ProjectData | InstallationDesignData) -> InstallationCrossSectionData:
    design = (
        project_or_design.installation_design
        if isinstance(project_or_design, ProjectData)
        else project_or_design
    )
    if not design.cross_sections:
        raise InstallationInputError("Kurulum modelinde fiziksel kesit bulunmuyor.")
    for section in design.cross_sections:
        if section.cross_section_id == design.active_cross_section_id:
            return section
    return design.cross_sections[0]


def cross_section_for_region(
    project: ProjectData,
    region_id: str,
) -> InstallationCrossSectionData:
    for section in project.installation_design.cross_sections:
        if region_id in section.region_ids:
            return section
    return active_cross_section(project)


def _phase_position_map(
    arrangement: str,
    burial_depth_m: float,
    phase_spacing_m: float,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    depth = float(burial_depth_m)
    spacing = float(phase_spacing_m)
    if depth <= 0 or spacing <= 0:
        raise InstallationInputError("Gömülme derinliği ve faz aralığı sıfırdan büyük olmalıdır.")
    normalized = str(arrangement).strip().upper()
    if normalized in {"FLAT", "HORIZONTAL", "DÜZ", "DUZ"}:
        return ((-spacing, depth), (0.0, depth), (spacing, depth))
    if normalized in {"VERTICAL", "DÜŞEY", "DUSEY"}:
        return ((0.0, max(0.01, depth - spacing)), (0.0, depth), (0.0, depth + spacing))
    if normalized in {"TREFOIL", "ÜÇGEN", "UCGEN"}:
        lower = depth + sqrt(3.0) * spacing / 2.0
        return ((0.0, depth), (-spacing / 2.0, lower), (spacing / 2.0, lower))
    raise InstallationInputError(f"Desteklenmeyen hazır yerleşim: {arrangement}")


def _normalise_phase_order(order: str) -> str:
    value = "".join(ch for ch in str(order).upper() if ch in "ABC")
    if len(value) != 3 or set(value) != {"A", "B", "C"}:
        raise InstallationInputError(f"Faz sırası ABC'nin bir permütasyonu olmalıdır: {order!r}")
    return value


def channel_geometry_defaults(
    installation_type: str,
    *,
    burial_depth_m: float = 1.20,
    cable_span_m: float = 0.45,
) -> CableChannelGeometryData:
    """Return a conservative editable geometry for the selected installation type.

    These values only seed the drawing.  They are not certified construction
    dimensions and do not silently overwrite cable coordinates.
    """

    kind = str(installation_type or THERMAL_INSTALL_DIRECT_BURIED).upper()
    depth = max(float(burial_depth_m), 0.20)
    width = max(0.80, float(cable_span_m) + 0.40)
    base = CableChannelGeometryData(
        trench_width_m=width,
        trench_depth_m=max(depth + 0.35, 1.20),
        thermal_backfill_height_m=max(0.45, min(0.80, depth * 0.55)),
        cover_slab_depth_m=max(0.25, depth - 0.45),
        source_reference="INSTALLATION_TYPE_DEFAULT",
    )
    if kind == THERMAL_INSTALL_DUCT_BANK:
        base.geometry_mode = "PARAMETRIC_DUCT_BANK"
        base.trench_width_m = max(width, 1.00)
        base.trench_depth_m = max(depth + 0.55, 1.50)
        base.duct_bank_width_m = max(0.75, width - 0.20)
        base.duct_bank_height_m = 0.55
        base.thermal_backfill_height_m = 0.0
    elif kind == THERMAL_INSTALL_CONCRETE_TROUGH:
        base.geometry_mode = "PARAMETRIC_CONCRETE_TROUGH"
        base.trench_width_m = max(width, 1.10)
        base.trench_depth_m = max(depth + 0.40, 1.25)
        base.trough_inner_width_m = max(0.70, width - 0.30)
        base.trough_inner_height_m = 0.70
        base.thermal_backfill_height_m = 0.0
    elif kind == THERMAL_INSTALL_HDD:
        base.geometry_mode = "PARAMETRIC_HDD"
        base.trench_width_m = max(width, 0.80)
        base.trench_depth_m = max(depth + 0.50, 2.00)
        base.hdd_bore_diameter_m = max(0.35, float(cable_span_m) + 0.20)
        base.cover_slab_enabled = False
        base.thermal_backfill_height_m = 0.0
    elif kind == THERMAL_INSTALL_TUNNEL:
        base.geometry_mode = "PARAMETRIC_TUNNEL"
        base.trench_width_m = 2.40
        base.trench_depth_m = max(depth + 1.50, 3.00)
        base.tunnel_width_m = 2.00
        base.tunnel_height_m = 2.00
        base.cover_slab_enabled = False
        base.thermal_backfill_height_m = 0.0
    else:
        base.geometry_mode = "PARAMETRIC_TRENCH"
    return base


def update_channel_geometry_for_installation(
    section: InstallationCrossSectionData,
    installation_type: str,
    *,
    reset_dimensions: bool = False,
) -> None:
    """Switch visible structure while preserving user dimensions by default."""

    section.installation_type = str(installation_type).upper()
    depths = [float(item.depth_m) for item in section.physical_cables if item.active]
    xs = [float(item.x_m) for item in section.physical_cables if item.active]
    burial = min(depths, default=1.20)
    span = max(xs, default=0.2) - min(xs, default=-0.2)
    defaults = channel_geometry_defaults(section.installation_type, burial_depth_m=burial, cable_span_m=span)
    if reset_dimensions:
        section.channel_geometry = defaults
        return
    geometry = section.channel_geometry
    geometry.geometry_mode = defaults.geometry_mode
    if not geometry.source_reference or geometry.source_reference.startswith(("LEGACY_", "MIGRATED_")):
        geometry.source_reference = "USER_INSTALLATION_TYPE_CHANGE"
    if section.installation_type == THERMAL_INSTALL_DUCT_BANK:
        geometry.duct_bank_width_m = max(geometry.duct_bank_width_m, span + 0.20)
    elif section.installation_type == THERMAL_INSTALL_HDD:
        geometry.hdd_bore_diameter_m = max(geometry.hdd_bore_diameter_m, span + 0.15)


def channel_half_width_at_depth(section: InstallationCrossSectionData, depth_m: float) -> float:
    """Return trench half-width at a depth below surface.

    ``trench_width_m`` is the bottom width. ``side_slope_h_to_v`` expands
    each wall toward the surface. A zero slope preserves the legacy
    rectangular trench exactly.
    """

    g = section.channel_geometry
    bottom = max(float(g.trench_depth_m), 0.01)
    depth = min(max(float(depth_m), 0.0), bottom)
    bottom_half = max(float(g.trench_width_m), 0.01) / 2.0
    slope = max(0.0, float(g.side_slope_h_to_v))
    return bottom_half + slope * (bottom - depth)


def channel_polygon_vertices(section: InstallationCrossSectionData) -> tuple[tuple[float, float], ...]:
    g = section.channel_geometry
    bottom = max(float(g.trench_depth_m), 0.01)
    centre = float(g.center_x_m)
    bottom_half = max(float(g.trench_width_m), 0.01) / 2.0
    top_half = channel_half_width_at_depth(section, 0.0)
    return (
        (centre - top_half, 0.0),
        (centre + top_half, 0.0),
        (centre + bottom_half, bottom),
        (centre - bottom_half, bottom),
    )


def channel_geometry_bounds(section: InstallationCrossSectionData) -> tuple[float, float, float]:
    vertices = channel_polygon_vertices(section)
    return min(x for x, _ in vertices), max(x for x, _ in vertices), max(y for _, y in vertices)


def point_inside_channel(section: InstallationCrossSectionData, x_m: float, depth_m: float) -> bool:
    g = section.channel_geometry
    bottom = max(float(g.trench_depth_m), 0.01)
    depth = float(depth_m)
    if depth < 0.0 or depth > bottom:
        return False
    return abs(float(x_m) - float(g.center_x_m)) <= channel_half_width_at_depth(section, depth) + 1e-12


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(
    a: tuple[float, float], b: tuple[float, float],
    c: tuple[float, float], d: tuple[float, float],
    *, tolerance: float = 1e-12,
) -> bool:
    o1, o2 = _orientation(a, b, c), _orientation(a, b, d)
    o3, o4 = _orientation(c, d, a), _orientation(c, d, b)
    return (o1 * o2 < -tolerance) and (o3 * o4 < -tolerance)


def polygon_self_intersects(vertices: Iterable[Iterable[float]]) -> bool:
    points = [(float(item[0]), float(item[1])) for item in vertices]
    count = len(points)
    if count < 4:
        return False
    for i in range(count):
        a, b = points[i], points[(i + 1) % count]
        for j in range(i + 1, count):
            if j in {i, (i + 1) % count} or (j + 1) % count in {i, (i + 1) % count}:
                continue
            if i == 0 and j == count - 1:
                continue
            c, d = points[j], points[(j + 1) % count]
            if _segments_intersect(a, b, c, d):
                return True
    return False


def _channel_envelope_clearance_m(
    section: InstallationCrossSectionData, x_m: float, depth_m: float, radius_m: float,
) -> float:
    g = section.channel_geometry
    bottom = max(float(g.trench_depth_m), 0.01)
    depth = float(depth_m)
    side = channel_half_width_at_depth(section, depth) - abs(float(x_m) - float(g.center_x_m))
    return min(depth, bottom - depth, side) - max(float(radius_m), 0.0)


def section_clearance_records(
    section: InstallationCrossSectionData,
    *,
    cable_outer_diameter_m: float,
) -> tuple[SectionClearanceRecord, ...]:
    """Return geometry-only fit/clearance records for engineering review.

    Required clearances are zero-fit limits, not construction-code spacing
    recommendations. Project-specific installation minimums remain designer
    inputs and must not be invented by the application.
    """

    records: list[SectionClearanceRecord] = []
    cable_radius = max(float(cable_outer_diameter_m), 0.0) / 2.0
    active_cables = [item for item in section.physical_cables if item.active]
    channel_envelope_types = {
        THERMAL_INSTALL_DIRECT_BURIED, THERMAL_INSTALL_DUCT_BANK, THERMAL_INSTALL_CONCRETE_TROUGH
    }
    if section.installation_type in channel_envelope_types:
        for cable in active_cables:
            clearance = _channel_envelope_clearance_m(section, cable.x_m, cable.depth_m, cable_radius)
            records.append(SectionClearanceRecord(
                "CABLE_CHANNEL", cable.physical_cable_id, section.cross_section_id, clearance, 0.0,
                "FAIL" if clearance < -1e-9 else "LOW" if clearance < 0.01 else "PASS",
                f"Kablo dış zarfının kanal/hendek sınırına en küçük açıklığı {clearance:.4f} m.",
            ))
    for index, first in enumerate(active_cables):
        for second in active_cables[index + 1:]:
            centre = sqrt((first.x_m - second.x_m) ** 2 + (first.depth_m - second.depth_m) ** 2)
            clearance = centre - 2.0 * cable_radius
            records.append(SectionClearanceRecord(
                "CABLE_CABLE", first.physical_cable_id, second.physical_cable_id, clearance, 0.0,
                "FAIL" if clearance < -1e-9 else "LOW" if clearance < 0.01 else "PASS",
                f"Kablo dış zarfları arası net açıklık {clearance:.4f} m.",
            ))
    active_slots = [item for item in section.duct_slots if item.active]
    if section.installation_type in channel_envelope_types:
        for slot in active_slots:
            radius = max(float(slot.outer_diameter_m), 0.0) / 2.0
            clearance = _channel_envelope_clearance_m(section, slot.x_m, slot.depth_m, radius)
            records.append(SectionClearanceRecord(
                "DUCT_CHANNEL", slot.slot_id, section.cross_section_id, clearance, 0.0,
                "FAIL" if clearance < -1e-9 else "LOW" if clearance < 0.01 else "PASS",
                f"Duct dış zarfının kanal/hendek sınırına en küçük açıklığı {clearance:.4f} m.",
            ))
    for index, first in enumerate(active_slots):
        for second in active_slots[index + 1:]:
            centre = sqrt((first.x_m - second.x_m) ** 2 + (first.depth_m - second.depth_m) ** 2)
            clearance = centre - (first.outer_diameter_m + second.outer_diameter_m) / 2.0
            records.append(SectionClearanceRecord(
                "DUCT_DUCT", first.slot_id, second.slot_id, clearance, 0.0,
                "FAIL" if clearance < -1e-9 else "LOW" if clearance < 0.01 else "PASS",
                f"Duct dış zarfları arası net açıklık {clearance:.4f} m.",
            ))
    slots = {item.slot_id: item for item in active_slots}
    for cable in active_cables:
        slot = slots.get(cable.duct_slot_id)
        if slot is None:
            continue
        clearance = (float(slot.inner_diameter_m) - float(cable_outer_diameter_m)) / 2.0
        records.append(SectionClearanceRecord(
            "CABLE_DUCT_ANNULUS", cable.physical_cable_id, slot.slot_id, clearance, 0.0,
            "FAIL" if clearance < -1e-9 else "LOW" if clearance < 0.005 else "PASS",
            f"Kablo ile duct iç cidarı arasındaki radyal açıklık {clearance:.4f} m.",
        ))
    return tuple(records)


def polygon_area_m2(vertices: Iterable[Iterable[float]]) -> float:
    points = [(float(item[0]), float(item[1])) for item in vertices]
    if len(points) < 3:
        return 0.0
    return abs(sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )) / 2.0


def generate_standard_cross_section(
    *,
    cross_section_id: str,
    name: str,
    arrangement: str = "TREFOIL",
    installation_type: str = THERMAL_INSTALL_DIRECT_BURIED,
    circuit_count: int = 1,
    parallel_cables_per_phase: int = 1,
    phase_spacing_m: float = 0.15,
    circuit_spacing_m: float = 0.80,
    parallel_group_spacing_m: float = 0.25,
    burial_depth_m: float = 1.20,
    outer_diameter_m: float = 0.105,
    phase_orders: Iterable[str] | None = None,
    circuit_load_currents_a: Iterable[float] | None = None,
    region_ids: Iterable[str] | None = None,
    duct_rows: int = 2,
    duct_columns: int = 3,
    duct_inner_diameter_m: float = 0.13,
    duct_outer_diameter_m: float = 0.16,
) -> InstallationCrossSectionData:
    circuit_count = max(1, int(circuit_count))
    parallel_count = max(1, int(parallel_cables_per_phase))
    if outer_diameter_m <= 0:
        raise InstallationInputError("Kablo dış çapı sıfırdan büyük olmalıdır.")
    orders = list(phase_orders or [])
    loads = [float(v) for v in (circuit_load_currents_a or [])]
    while len(orders) < circuit_count:
        orders.append("ABC")
    while len(loads) < circuit_count:
        loads.append(0.0)
    orders = [_normalise_phase_order(v) for v in orders[:circuit_count]]

    circuits = [
        InstallationCircuitData(
            f"C{index}",
            f"Devre {index}",
            orders[index - 1],
            loads[index - 1],
            1.0,
            True,
        )
        for index in range(1, circuit_count + 1)
    ]
    physical: list[PhysicalCableData] = []
    slots: list[DuctSlotData] = []

    normalized_install = str(installation_type).upper()
    normalized_arrangement = str(arrangement).upper()
    legacy_duct_arrangement = normalized_arrangement == "DUCT_BANK"
    if normalized_install == THERMAL_INSTALL_DUCT_BANK or legacy_duct_arrangement:
        required = circuit_count * parallel_count * 3
        rows = max(1, int(duct_rows))
        columns = max(1, int(duct_columns))
        if rows * columns < required:
            rows = max(rows, int((required + columns - 1) / columns))
        slot_spacing = max(float(phase_spacing_m), float(duct_outer_diameter_m) * 1.20)
        x0 = -(columns - 1) * slot_spacing / 2.0
        for row in range(rows):
            for col in range(columns):
                index = row * columns + col + 1
                slots.append(DuctSlotData(
                    f"DS-{index:02d}",
                    x0 + col * slot_spacing,
                    burial_depth_m + row * slot_spacing,
                    duct_inner_diameter_m,
                    duct_outer_diameter_m,
                    row + 1,
                    col + 1,
                ))
        slot_index = 0
        for circuit in circuits:
            for parallel_index in range(1, parallel_count + 1):
                for phase in circuit.phase_order:
                    slot = slots[slot_index]
                    slot_index += 1
                    physical.append(PhysicalCableData(
                        f"{circuit.circuit_id}-{phase}-{parallel_index}",
                        circuit.circuit_id,
                        phase,
                        parallel_index,
                        slot.x_m,
                        slot.depth_m,
                        duct_slot_id=slot.slot_id,
                    ))
        arrangement_label = "CUSTOM"
    else:
        effective_phase_spacing_m = (
            float(outer_diameter_m)
            if normalized_arrangement == "TREFOIL"
            else float(phase_spacing_m)
        )
        base_positions = _phase_position_map(
            normalized_arrangement, burial_depth_m, effective_phase_spacing_m
        )
        group_span = max(float(parallel_group_spacing_m), outer_diameter_m * 1.10)
        circuit_span = max(
            float(circuit_spacing_m),
            group_span * parallel_count + effective_phase_spacing_m * 2.0,
        )
        for circuit_index, circuit in enumerate(circuits, start=1):
            circuit_offset = (circuit_index - (circuit_count + 1) / 2.0) * circuit_span
            for parallel_index in range(1, parallel_count + 1):
                parallel_offset = (parallel_index - (parallel_count + 1) / 2.0) * group_span
                for position_index, phase in enumerate(circuit.phase_order):
                    x0, depth0 = base_positions[position_index]
                    physical.append(PhysicalCableData(
                        f"{circuit.circuit_id}-{phase}-{parallel_index}",
                        circuit.circuit_id,
                        phase,
                        parallel_index,
                        x0 + circuit_offset + parallel_offset,
                        depth0,
                    ))
        arrangement_label = normalized_arrangement

    return InstallationCrossSectionData(
        cross_section_id=cross_section_id,
        name=name,
        installation_type=(
            THERMAL_INSTALL_DUCT_BANK
            if normalized_install == THERMAL_INSTALL_DUCT_BANK or legacy_duct_arrangement
            else normalized_install
        ),
        arrangement_label=arrangement_label,
        region_ids=list(region_ids or []),
        circuits=circuits,
        physical_cables=physical,
        duct_slots=slots,
        external_heat_sources=[],
        channel_geometry=channel_geometry_defaults(
            THERMAL_INSTALL_DUCT_BANK
            if normalized_install == THERMAL_INSTALL_DUCT_BANK or legacy_duct_arrangement
            else normalized_install,
            burial_depth_m=burial_depth_m,
            cable_span_m=(
                max((item.x_m for item in physical), default=0.20)
                - min((item.x_m for item in physical), default=-0.20)
            ),
        ),
        source_reference="USER_GENERATED_PRESET",
        notes="Hazır formasyondan üretildi; her fiziksel kablonun x-y konumu ayrıca düzenlenebilir.",
    )


def resolved_physical_cables(
    section: InstallationCrossSectionData,
    *,
    include_inactive: bool = False,
) -> tuple[ResolvedPhysicalCable, ...]:
    circuits = {item.circuit_id: item for item in section.circuits}
    active_cables = [
        item for item in section.physical_cables
        if include_inactive or (item.active and circuits.get(item.circuit_id, InstallationCircuitData("", "", active=False)).active)
    ]
    by_phase: dict[tuple[str, str], list[PhysicalCableData]] = {}
    for cable in active_cables:
        by_phase.setdefault((cable.circuit_id, cable.phase.upper()), []).append(cable)

    resolved: list[ResolvedPhysicalCable] = []
    for cable in active_cables:
        circuit = circuits.get(cable.circuit_id)
        if circuit is None:
            raise InstallationInputError(
                f"{cable.physical_cable_id}: bağlı devre bulunamadı: {cable.circuit_id}"
            )
        peers = by_phase.get((cable.circuit_id, cable.phase.upper()), [])
        total = max(0.0, float(circuit.load_current_a))
        explicit_sum = sum(max(0.0, float(item.current_override_a)) for item in peers if item.current_override_a > 0)
        automatic = [item for item in peers if item.current_override_a <= 0]
        if cable.current_override_a > 0:
            current = float(cable.current_override_a)
        else:
            remaining = max(0.0, total - explicit_sum)
            current = remaining / max(1, len(automatic))
        angle = (
            float(cable.current_angle_override_deg)
            if cable.current_angle_override_deg is not None
            else phase_angle_deg(cable.phase)
        )
        resolved.append(ResolvedPhysicalCable(
            cable.physical_cable_id,
            cable.circuit_id,
            cable.phase.upper(),
            int(cable.parallel_index),
            float(cable.x_m),
            float(cable.depth_m),
            current,
            angle,
            cable.cable_snapshot_id,
            cable.duct_slot_id,
            cable.active and circuit.active,
        ))
    return tuple(resolved)


def validate_installation_design(
    project_or_design: ProjectData | InstallationDesignData,
    *,
    cable_outer_diameter_m: float | None = None,
) -> tuple[InstallationValidationIssue, ...]:
    material_ids: set[str] = set()
    if isinstance(project_or_design, ProjectData):
        design = project_or_design.installation_design
        material_ids = {item.material_id for item in project_or_design.thermal_design.materials}
        if cable_outer_diameter_m is None:
            cable_outer_diameter_m = project_or_design.cable.overall_diameter_mm / 1000.0
    else:
        design = project_or_design
    diameter = max(float(cable_outer_diameter_m or 0.0), 0.0)
    issues: list[InstallationValidationIssue] = []
    if not design.cross_sections:
        return (InstallationValidationIssue("ERROR", "NO_CROSS_SECTION", "Fiziksel kurulum kesiti bulunmuyor."),)

    section_ids: set[str] = set()
    for section in design.cross_sections:
        sid = section.cross_section_id
        if not sid:
            issues.append(InstallationValidationIssue("ERROR", "EMPTY_SECTION_ID", "Kesit ID boş olamaz."))
        elif sid in section_ids:
            issues.append(InstallationValidationIssue("ERROR", "DUPLICATE_SECTION_ID", f"Mükerrer kesit ID: {sid}", sid))
        section_ids.add(sid)
        if section.coordinate_system != "X_HORIZONTAL_DEPTH_POSITIVE_DOWN_M":
            issues.append(InstallationValidationIssue(
                "WARNING", "COORDINATE_SYSTEM", "Koordinat sistemi beklenen x/yüzeyden derinlik metre tanımıyla uyuşmuyor.", sid
            ))

        geometry = section.channel_geometry
        if geometry.trench_width_m <= 0 or geometry.trench_depth_m <= 0:
            issues.append(InstallationValidationIssue(
                "ERROR", "CHANNEL_GEOMETRY", "Kanal/hendek genişliği ve derinliği sıfırdan büyük olmalıdır.", sid
            ))
        if not isfinite(float(geometry.side_slope_h_to_v)) or float(geometry.side_slope_h_to_v) < 0:
            issues.append(InstallationValidationIssue(
                "ERROR", "CHANNEL_SIDE_SLOPE", "Hendek yan eğimi H:V sıfır veya pozitif olmalıdır.", sid
            ))
        layer_sum = (
            max(0.0, float(geometry.bedding_thickness_m))
            + max(0.0, float(geometry.thermal_backfill_height_m))
            + max(0.0, float(geometry.selected_fill_thickness_m))
            + max(0.0, float(geometry.surface_layer_thickness_m))
        )
        if layer_sum > float(geometry.trench_depth_m) + 1e-9:
            issues.append(InstallationValidationIssue(
                "ERROR", "CHANNEL_LAYER_STACK",
                f"Katman kalınlıkları hendek derinliğini aşıyor: {layer_sum:.3f} > {geometry.trench_depth_m:.3f} m.", sid
            ))
        if str(section.installation_type).upper() == THERMAL_INSTALL_DIRECT_BURIED and diameter > 0.0:
            try:
                envelope = direct_buried_envelope(section, diameter)
            except InstallationInputError:
                envelope = None
            if envelope is not None:
                if envelope.bedding_bottom_m > float(geometry.trench_depth_m) + 1e-9:
                    issues.append(InstallationValidationIssue(
                        "WARNING", "CABLE_BEDDING_BELOW_TRENCH",
                        "Kablo grubu ve alt yatak kumu hendek tabanının altına taşıyor.", sid
                    ))
                expected_bedding = max(0.0, float(geometry.trench_depth_m) - envelope.bedding_top_m)
                if abs(expected_bedding - float(geometry.bedding_thickness_m)) > 1e-5:
                    issues.append(InstallationValidationIssue(
                        "WARNING", "BEDDING_ENVELOPE_NOT_SYNCHRONISED",
                        "Yatak kumu zarfı gerçek kablo dış çapı ve alt/üst örtülerle senkron değil.", sid
                    ))
                if float(geometry.bedding_bottom_cover_m) < 0.10 - 1e-9:
                    issues.append(InstallationValidationIssue(
                        "WARNING", "BEDDING_BOTTOM_COVER_BELOW_PROJECT_RULE",
                        "Kablo altı yatak kumu 0,10 m proje başlangıç kuralının altında.", sid
                    ))
                if float(geometry.bedding_top_cover_m) < 0.10 - 1e-9:
                    issues.append(InstallationValidationIssue(
                        "WARNING", "BEDDING_TOP_COVER_BELOW_PROJECT_RULE",
                        "En üst kablo üzerindeki kum örtüsü 0,10 m proje başlangıç kuralının altında.", sid
                    ))
                if float(geometry.trench_width_m) + 1e-9 < envelope.required_bottom_width_m:
                    issues.append(InstallationValidationIssue(
                        "WARNING", "TRENCH_TOO_NARROW_FOR_BEDDING",
                        f"Hendek taban genişliği kablo grubu ve yan kum payı için yetersiz: "
                        f"{geometry.trench_width_m:.3f} < {envelope.required_bottom_width_m:.3f} m.", sid
                    ))
        if geometry.cover_slab_enabled and (
            geometry.cover_slab_width_m <= 0 or geometry.cover_slab_thickness_m <= 0
            or geometry.cover_slab_depth_m <= 0 or geometry.cover_slab_depth_m >= geometry.trench_depth_m
        ):
            issues.append(InstallationValidationIssue(
                "ERROR", "COVER_SLAB_GEOMETRY", "Koruma plakası genişlik/kalınlık/derinlik değerleri geçersiz.", sid
            ))
        left, right, bottom = channel_geometry_bounds(section)

        if material_ids:
            referenced_materials = {
                geometry.native_soil_material_id, geometry.bedding_material_id,
                geometry.thermal_backfill_material_id, geometry.selected_fill_material_id,
                geometry.general_fill_material_id, geometry.surface_material_id,
                geometry.cover_slab_material_id, geometry.duct_bank_material_id,
                geometry.trough_material_id, geometry.hdd_grout_material_id,
            } - {""}
            for material_id in sorted(referenced_materials - material_ids):
                issues.append(InstallationValidationIssue(
                    "ERROR", "UNKNOWN_THERMAL_MATERIAL",
                    f"Kablo-kanal geometrisi bilinmeyen termal malzemeye bağlı: {material_id}", sid, material_id
                ))

        region_object_ids: set[str] = set()
        for material_region in section.material_regions:
            rid = str(material_region.region_id).strip()
            if not rid or rid in region_object_ids:
                issues.append(InstallationValidationIssue(
                    "ERROR", "DUPLICATE_MATERIAL_REGION",
                    f"Boş veya mükerrer malzeme bölgesi ID: {material_region.region_id!r}", sid, rid
                ))
            region_object_ids.add(rid)
            vertices = list(material_region.vertices_m or [])
            valid_vertices = (
                len(vertices) >= 3
                and all(
                    isinstance(point, (list, tuple)) and len(point) >= 2
                    and isfinite(float(point[0])) and isfinite(float(point[1]))
                    and float(point[1]) >= 0.0
                    for point in vertices
                )
            )
            if not valid_vertices:
                issues.append(InstallationValidationIssue(
                    "ERROR", "MATERIAL_REGION_GEOMETRY",
                    "Termal malzeme bölgesi en az üç geçerli noktalı olmalıdır.", sid, rid
                ))
            elif polygon_self_intersects(vertices):
                issues.append(InstallationValidationIssue(
                    "ERROR", "MATERIAL_REGION_SELF_INTERSECTION",
                    "Termal malzeme polygonu kendi kendini kesiyor; köşe sırası düzeltilmelidir.", sid, rid
                ))
            elif polygon_area_m2(vertices) <= 1e-8:
                issues.append(InstallationValidationIssue(
                    "ERROR", "MATERIAL_REGION_GEOMETRY",
                    "Termal malzeme bölgesi sıfırdan büyük alana sahip olmalıdır.", sid, rid
                ))
            if material_ids and str(material_region.material_id) not in material_ids:
                issues.append(InstallationValidationIssue(
                    "ERROR", "UNKNOWN_THERMAL_MATERIAL",
                    f"Malzeme bölgesi bilinmeyen termal malzemeye bağlı: {material_region.material_id}", sid, rid
                ))

        active_priorities: dict[int, list[str]] = {}
        for material_region in section.material_regions:
            if material_region.active:
                active_priorities.setdefault(int(material_region.priority), []).append(str(material_region.region_id))
        for priority, region_ids in sorted(active_priorities.items()):
            if len(region_ids) > 1:
                issues.append(InstallationValidationIssue(
                    "WARNING", "MATERIAL_REGION_PRIORITY_TIE",
                    f"Aynı öncelikte birden fazla aktif malzeme bölgesi var ({priority}): {', '.join(region_ids)}. "
                    "Çakışan hücrelerde liste sırası sonucu etkileyebilir.", sid, region_ids[0]
                ))

        circuit_ids: set[str] = set()
        circuits: dict[str, InstallationCircuitData] = {}
        for circuit in section.circuits:
            if not circuit.circuit_id or circuit.circuit_id in circuit_ids:
                issues.append(InstallationValidationIssue(
                    "ERROR", "DUPLICATE_CIRCUIT_ID", f"Boş veya mükerrer devre ID: {circuit.circuit_id!r}", sid, circuit.circuit_id
                ))
            circuit_ids.add(circuit.circuit_id)
            circuits[circuit.circuit_id] = circuit
            try:
                _normalise_phase_order(circuit.phase_order)
            except InstallationInputError as exc:
                issues.append(InstallationValidationIssue("ERROR", "PHASE_ORDER", str(exc), sid, circuit.circuit_id))
            if circuit.load_current_a < 0:
                issues.append(InstallationValidationIssue(
                    "ERROR", "NEGATIVE_CIRCUIT_LOAD", "Devre akımı negatif olamaz.", sid, circuit.circuit_id
                ))
            if abs(float(circuit.load_factor) - 1.0) > 1e-12:
                issues.append(InstallationValidationIssue(
                    "WARNING", "LEGACY_CIRCUIT_LOAD_FACTOR_IGNORED",
                    "Legacy devre yük faktörü kararlı durum akımına uygulanmaz; IEC 60853 kayıp-yük faktörü aktif yük profilinden türetilir.",
                    sid, circuit.circuit_id
                ))

        slot_ids: set[str] = set()
        slots: dict[str, DuctSlotData] = {}
        for slot in section.duct_slots:
            if not slot.slot_id or slot.slot_id in slot_ids:
                issues.append(InstallationValidationIssue(
                    "ERROR", "DUPLICATE_DUCT_SLOT", f"Boş veya mükerrer duct slot ID: {slot.slot_id!r}", sid, slot.slot_id
                ))
            slot_ids.add(slot.slot_id)
            slots[slot.slot_id] = slot
            if slot.depth_m <= 0 or slot.inner_diameter_m <= 0 or slot.outer_diameter_m <= slot.inner_diameter_m:
                issues.append(InstallationValidationIssue(
                    "ERROR", "DUCT_GEOMETRY", "Duct slot derinliği/çapları geçersiz.", sid, slot.slot_id
                ))

        cable_ids: set[str] = set()
        occupied_slots: dict[str, str] = {}
        active = [item for item in section.physical_cables if item.active]
        for cable in section.physical_cables:
            cid = cable.physical_cable_id
            if not cid or cid in cable_ids:
                issues.append(InstallationValidationIssue(
                    "ERROR", "DUPLICATE_PHYSICAL_CABLE", f"Boş veya mükerrer fiziksel kablo ID: {cid!r}", sid, cid
                ))
            cable_ids.add(cid)
            if cable.circuit_id not in circuits:
                issues.append(InstallationValidationIssue(
                    "ERROR", "UNKNOWN_CIRCUIT", f"Fiziksel kablo bilinmeyen devreye bağlı: {cable.circuit_id}", sid, cid
                ))
            if cable.phase.upper() not in {"A", "B", "C"}:
                issues.append(InstallationValidationIssue("ERROR", "INVALID_PHASE", f"Geçersiz faz: {cable.phase}", sid, cid))
            if int(cable.parallel_index) < 1:
                issues.append(InstallationValidationIssue("ERROR", "PARALLEL_INDEX", "Paralel kablo numarası en az 1 olmalıdır.", sid, cid))
            if not all(isfinite(float(v)) for v in (cable.x_m, cable.depth_m)) or cable.depth_m <= 0:
                issues.append(InstallationValidationIssue("ERROR", "CABLE_COORDINATE", "Kablo x/derinlik koordinatı geçersiz.", sid, cid))
            elif section.installation_type in {
                THERMAL_INSTALL_DIRECT_BURIED, THERMAL_INSTALL_DUCT_BANK, THERMAL_INSTALL_CONCRETE_TROUGH
            } and not point_inside_channel(section, float(cable.x_m), float(cable.depth_m)):
                issues.append(InstallationValidationIssue(
                    "WARNING", "CABLE_OUTSIDE_CHANNEL",
                    "Kablo merkezi tanımlı kanal/hendek geometrisinin dışında kalıyor.", sid, cid
                ))
            if cable.current_override_a < 0:
                issues.append(InstallationValidationIssue("ERROR", "NEGATIVE_CABLE_LOAD", "Kablo akım override değeri negatif olamaz.", sid, cid))
            if abs(float(cable.load_factor) - 1.0) > 1e-12:
                issues.append(InstallationValidationIssue(
                    "WARNING", "LEGACY_PHYSICAL_CABLE_LOAD_FACTOR_IGNORED",
                    "Fiziksel kablo legacy yük faktörü hesapta kullanılmaz; akım override değeri doğrudan RMS çalışma akımıdır.", sid, cid
                ))
            if cable.duct_slot_id:
                if cable.duct_slot_id not in slots:
                    issues.append(InstallationValidationIssue("ERROR", "UNKNOWN_DUCT_SLOT", f"Duct slot bulunamadı: {cable.duct_slot_id}", sid, cid))
                elif cable.duct_slot_id in occupied_slots:
                    issues.append(InstallationValidationIssue(
                        "ERROR", "DUCT_SLOT_OCCUPIED",
                        f"Duct slot birden fazla kabloya atanmış: {cable.duct_slot_id}", sid, cid,
                    ))
                else:
                    occupied_slots[cable.duct_slot_id] = cid
                    slot = slots[cable.duct_slot_id]
                    if abs(cable.x_m - slot.x_m) > 1e-6 or abs(cable.depth_m - slot.depth_m) > 1e-6:
                        issues.append(InstallationValidationIssue(
                            "WARNING", "DUCT_COORDINATE_MISMATCH",
                            "Kablo koordinatı atanmış duct slot merkezinden farklı; slota hizalama önerilir.", sid, cid,
                        ))

        for circuit in section.circuits:
            if not circuit.active:
                continue
            counts = {
                phase: len([c for c in active if c.circuit_id == circuit.circuit_id and c.phase.upper() == phase])
                for phase in "ABC"
            }
            if 0 in counts.values():
                issues.append(InstallationValidationIssue(
                    "ERROR", "MISSING_PHASE", f"{circuit.circuit_id} aktif devresinde eksik faz var: {counts}", sid, circuit.circuit_id
                ))
            elif len(set(counts.values())) != 1:
                issues.append(InstallationValidationIssue(
                    "WARNING", "UNEQUAL_PARALLEL_COUNT", f"{circuit.circuit_id} faz başına kablo sayıları eşit değil: {counts}", sid, circuit.circuit_id
                ))

        if diameter > 0:
            for index, first in enumerate(active):
                for second in active[index + 1:]:
                    distance = sqrt((first.x_m - second.x_m) ** 2 + (first.depth_m - second.depth_m) ** 2)
                    if distance < diameter - physical_cable_contact_tolerance_m(diameter):
                        issues.append(InstallationValidationIssue(
                            "ERROR", "CABLE_OVERLAP",
                            f"Kablolar çakışıyor: {first.physical_cable_id}/{second.physical_cable_id}; "
                            f"eksen mesafesi={distance:.4f} m, dış çap={diameter:.4f} m.",
                            sid, first.physical_cable_id,
                        ))

        for record in section_clearance_records(section, cable_outer_diameter_m=diameter):
            if record.category == "CABLE_CHANNEL" and record.status == "FAIL":
                issues.append(InstallationValidationIssue(
                    "WARNING", "CABLE_ENVELOPE_OUTSIDE_CHANNEL", record.message, sid, record.object_a
                ))
            elif record.category == "CABLE_CHANNEL" and record.status == "LOW":
                issues.append(InstallationValidationIssue(
                    "WARNING", "CABLE_CHANNEL_LOW_CLEARANCE", record.message, sid, record.object_a
                ))
            elif record.category == "DUCT_CHANNEL" and record.status == "FAIL":
                issues.append(InstallationValidationIssue(
                    "WARNING", "DUCT_ENVELOPE_OUTSIDE_CHANNEL", record.message, sid, record.object_a
                ))
            elif record.category == "DUCT_DUCT" and record.status == "FAIL":
                issues.append(InstallationValidationIssue(
                    "ERROR", "DUCT_OVERLAP", record.message, sid, record.object_a
                ))
            elif record.category == "CABLE_DUCT_ANNULUS" and record.status == "FAIL":
                issues.append(InstallationValidationIssue(
                    "ERROR", "CABLE_DOES_NOT_FIT_DUCT", record.message, sid, record.object_a
                ))
            elif record.category == "CABLE_DUCT_ANNULUS" and record.status == "LOW":
                issues.append(InstallationValidationIssue(
                    "WARNING", "CABLE_DUCT_LOW_ANNULAR_CLEARANCE", record.message, sid, record.object_a
                ))

        if geometry.cover_slab_enabled:
            slab_left = float(geometry.center_x_m) - float(geometry.cover_slab_width_m) / 2.0
            slab_right = float(geometry.center_x_m) + float(geometry.cover_slab_width_m) / 2.0
            slab_top = float(geometry.cover_slab_depth_m) - float(geometry.cover_slab_thickness_m) / 2.0
            slab_bottom = float(geometry.cover_slab_depth_m) + float(geometry.cover_slab_thickness_m) / 2.0
            for cable in active:
                nearest_x = min(max(float(cable.x_m), slab_left), slab_right)
                nearest_y = min(max(float(cable.depth_m), slab_top), slab_bottom)
                distance = sqrt((float(cable.x_m) - nearest_x) ** 2 + (float(cable.depth_m) - nearest_y) ** 2)
                if distance < diameter / 2.0 - 1e-9:
                    issues.append(InstallationValidationIssue(
                        "ERROR", "CABLE_COVER_SLAB_COLLISION",
                        "Kablo dış zarfı koruma plakasıyla çakışıyor.", sid, cable.physical_cable_id
                    ))

        for source in section.external_heat_sources:
            if source.heat_w_m < 0 or source.effective_radius_m <= 0 or source.depth_m <= 0:
                issues.append(InstallationValidationIssue(
                    "ERROR", "EXTERNAL_HEAT_SOURCE", "Harici ısı kaynağı değeri/yarıçapı/derinliği geçersiz.", sid, source.source_id
                ))

    if design.active_cross_section_id not in section_ids:
        issues.append(InstallationValidationIssue(
            "WARNING", "ACTIVE_SECTION_MISSING",
            "Aktif kesit ID listede bulunamadı; ilk kesit kullanılacaktır.",
            design.active_cross_section_id,
        ))
    return tuple(issues)



def insert_material_region_vertex(
    vertices_m: Iterable[Iterable[float]],
    edge_index: int | None = None,
) -> tuple[list[list[float]], int]:
    """Insert a vertex at an edge midpoint without changing polygon topology.

    When ``edge_index`` is omitted the longest edge is selected.  The helper is
    UI-independent so geometry editing can be regression-tested without Qt.
    """

    vertices = [[float(point[0]), float(point[1])] for point in vertices_m]
    if len(vertices) < 3:
        raise InstallationInputError("Malzeme polygonu köşe eklemek için en az üç köşeli olmalıdır.")
    count = len(vertices)
    if edge_index is None:
        lengths = []
        for index in range(count):
            first = vertices[index]
            second = vertices[(index + 1) % count]
            lengths.append((second[0] - first[0]) ** 2 + (second[1] - first[1]) ** 2)
        edge_index = max(range(count), key=lambda index: lengths[index])
    edge_index = int(edge_index) % count
    first = vertices[edge_index]
    second = vertices[(edge_index + 1) % count]
    midpoint = [(first[0] + second[0]) / 2.0, (first[1] + second[1]) / 2.0]
    inserted_index = edge_index + 1
    vertices.insert(inserted_index, midpoint)
    return vertices, inserted_index


def remove_material_region_vertex(
    vertices_m: Iterable[Iterable[float]],
    vertex_index: int,
) -> list[list[float]]:
    """Remove one polygon vertex while preserving the three-vertex minimum."""

    vertices = [[float(point[0]), float(point[1])] for point in vertices_m]
    if len(vertices) <= 3:
        raise InstallationInputError("Malzeme polygonunda en az üç köşe kalmalıdır.")
    index = int(vertex_index)
    if index < 0 or index >= len(vertices):
        raise InstallationInputError("Silinecek polygon köşe indeksi geçersiz.")
    vertices.pop(index)
    return vertices

def installation_summary(project: ProjectData) -> tuple[str, ...]:
    issues = validate_installation_design(project)
    errors = sum(1 for item in issues if item.severity == "ERROR")
    warnings = sum(1 for item in issues if item.severity == "WARNING")
    sections = project.installation_design.cross_sections
    cable_count = sum(len(item.physical_cables) for item in sections)
    circuit_count = sum(len(item.circuits) for item in sections)
    return (
        f"Kesit sayısı = {len(sections)}",
        f"Devre kaydı = {circuit_count}",
        f"Fiziksel kablo = {cable_count}",
        f"Doğrulama = {errors} hata / {warnings} uyarı",
        f"Solver bağı = {project.installation_design.solver_coupling_mode}",
        f"Referans kapsam = {INSTALLATION_REFERENCE}",
    )
