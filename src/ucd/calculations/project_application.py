from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from math import pi, sqrt
from typing import Any, Iterable

from ucd.calculations.cable_library import apply_catalog_record, create_project_snapshot, validate_cable
from ucd.calculations.first_design import apply_load_calculation
from ucd.models.project import (
    CABLE_SOURCE_CALCULATED,
    CABLE_SOURCE_CATALOG,
    CABLE_SOURCE_MANUFACTURER_DRAWING,
    CABLE_SOURCE_TEST_REPORT,
    CABLE_SOURCE_USER_ASSUMPTION,
    CABLE_VALUE_ASSUMPTION,
    CABLE_VALUE_CATALOG,
    CABLE_VALUE_DERIVED,
    CABLE_VALUE_MANUFACTURER_REQUIRED,
    CABLE_VALUE_MISSING,
    CABLE_VALUE_USER,
    CONFLICT_CREATE_SCENARIOS,
    CONFLICT_UNRESOLVED,
    CONFLICT_USE_SOURCE,
    CONFLICT_USE_USER_VALUE,
    CableApplicationData,
    CableCatalogRecord,
    CableCompletionItem,
    ProjectData,
    RouteCableAssignment,
    SourceConflictDecision,
)

REFERENCE = (
    "DiTuS v0.15.1 project cable application workflow. Catalog values, calculated values, "
    "user inputs and engineering assumptions remain separately traceable. Applying a cable "
    "does not convert a catalog screening result into final project approval."
)


class ProjectCableApplicationError(ValueError):
    pass


@dataclass(frozen=True)
class CableCompletionReport:
    items: tuple[CableCompletionItem, ...]
    blocking_count: int
    manufacturer_confirmation_count: int
    assumption_count: int
    status: str

    @property
    def can_run_preliminary(self) -> bool:
        return self.status in {"PRELIMINARY_READY", "CONDITIONAL"}

    @property
    def can_issue_final(self) -> bool:
        return self.status == "FINAL_DATA_READY"


@dataclass(frozen=True)
class ProjectApplicationResult:
    catalog_record_id: str
    candidate_id: str
    snapshot_id: str
    snapshot_hash: str
    assigned_route_sections: tuple[str, ...]
    completion: CableCompletionReport
    status: str
    trace: tuple[str, ...]


@dataclass(frozen=True)
class ProjectVoltageDropResult:
    current_per_cable_a: float
    resistance_ohm_km: float
    reactance_ohm_km: float
    length_m: float
    voltage_drop_v: float
    voltage_drop_percent: float
    source: str


@dataclass(frozen=True)
class ApplicationIterationGate:
    gate_id: str
    label: str
    status: str
    blocking: bool
    message: str


@dataclass(frozen=True)
class ApplicationIterationSummary:
    status: str
    gates: tuple[ApplicationIterationGate, ...]
    voltage_drop: ProjectVoltageDropResult | None
    trace: tuple[str, ...]


_REQUIRED_FIELDS: tuple[tuple[str, str, str, tuple[str, ...], bool], ...] = (
    ("voltage_class", "Kablo gerilim sınıfı U0/U(Um)", "ELECTRICAL", ("VOLTAGE_DROP", "IEC_60287"), True),
    ("conductor_area", "İletken nominal kesiti", "ELECTRICAL", ("ALL" ,), True),
    ("rdc20", "İletken Rdc @20 °C", "ELECTRICAL", ("VOLTAGE_DROP", "IEC_60287", "FAULT"), True),
    ("capacitance", "Kapasitans", "ELECTRICAL", ("BONDING", "DIELECTRIC_LOSS"), False),
    ("overall_diameter", "Kablo dış çapı", "GEOMETRY", ("IEC_60287", "2D_THERMAL"), True),
    ("conductor_diameter", "Gerçek iletken çapı", "GEOMETRY", ("IEC_60287", "BONDING", "2D_THERMAL"), False),
    ("insulation_outer_diameter", "İzolasyon dış çapı", "GEOMETRY", ("IEC_60287", "BONDING", "2D_THERMAL"), True),
    ("screen_area", "Metalik ekran/kılıf kesiti", "METALLIC_SCREEN", ("BONDING", "FAULT", "SVL"), True),
    ("screen_wire_geometry", "Metalik ekran tel adedi ve tel çapı", "METALLIC_SCREEN", ("BONDING", "FAULT"), False),
    ("thermal_layers", "Katman ısıl özdirençleri", "THERMAL", ("IEC_60287", "2D_THERMAL"), True),
    ("heat_capacity", "Katman hacimsel ısı kapasiteleri", "THERMAL", ("IEC_60853",), False),
    ("bonding_scheme", "Bonding düzeni ve topraklama noktaları", "BONDING", ("BONDING", "SVL", "FAULT"), False),
    ("fault_duration", "Faz ve toprak arızası temizleme süreleri", "FAULT", ("FAULT", "SCREEN_SHORT_CIRCUIT"), False),
)


def _source_for_layer(cable, layer) -> Any | None:
    return next((source for source in cable.parameter_sources if source.source_id == layer.source_id), None)


def _status_from_source(source: Any | None) -> str:
    if source is None:
        return CABLE_VALUE_MISSING
    source_type = str(source.source_type).upper()
    if source_type in {CABLE_SOURCE_CATALOG, CABLE_SOURCE_MANUFACTURER_DRAWING, CABLE_SOURCE_TEST_REPORT}:
        return CABLE_VALUE_CATALOG
    if source_type == CABLE_SOURCE_CALCULATED:
        return CABLE_VALUE_DERIVED
    if source_type == CABLE_SOURCE_USER_ASSUMPTION:
        return CABLE_VALUE_ASSUMPTION
    return CABLE_VALUE_USER


def _first_layer(cable, *types: str):
    wanted = {item.upper() for item in types}
    return next((layer for layer in cable.layers if layer.layer_type.upper() in wanted), None)


def _completion_item(
    item_id: str,
    label: str,
    category: str,
    status: str,
    value: Any,
    unit: str,
    source_reference: str,
    required_for: Iterable[str],
    blocking: bool,
    notes: str = "",
) -> CableCompletionItem:
    return CableCompletionItem(
        item_id=item_id,
        parameter_key=item_id,
        label=label,
        category=category,
        status=status,
        value=value,
        unit=unit,
        source_reference=source_reference,
        required_for=list(required_for),
        blocking=blocking,
        notes=notes,
    )


def assess_cable_completion(project: ProjectData, record: CableCatalogRecord | None = None) -> CableCompletionReport:
    cable = project.cable
    if record is None and cable.catalog_record_id:
        record = next((item for item in project.cable_library.records if item.record_id == cable.catalog_record_id), None)
    catalog_dimensions = record.catalog_dimensions if record else {}
    catalog_electrical = record.catalog_electrical if record else {}

    conductor = _first_layer(cable, "CONDUCTOR")
    insulation = _first_layer(cable, "INSULATION")
    screen = _first_layer(cable, "WIRE_SCREEN", "METALLIC_SCREEN", "METALLIC_SHEATH")

    items: list[CableCompletionItem] = []

    def add_scalar(
        key: str, label: str, category: str, value: Any, unit: str, source_status: str,
        source_ref: str, required_for: tuple[str, ...], blocking: bool, notes: str = ""
    ) -> None:
        status = source_status if value not in {None, "", 0, 0.0} else CABLE_VALUE_MISSING
        items.append(_completion_item(key, label, category, status, value, unit, source_ref, required_for, blocking, notes))

    add_scalar(
        "voltage_class", _REQUIRED_FIELDS[0][1], "ELECTRICAL", cable.voltage_class, "",
        CABLE_VALUE_CATALOG if record else CABLE_VALUE_USER,
        record.source_page if record else "Proje kablo kaydı", ("VOLTAGE_DROP", "IEC_60287"), True,
    )
    add_scalar(
        "conductor_area", _REQUIRED_FIELDS[1][1], "ELECTRICAL", cable.conductor_area_mm2, "mm²",
        _status_from_source(_source_for_layer(cable, conductor)) if conductor else CABLE_VALUE_MISSING,
        conductor.source_id if conductor else "", ("ALL",), True,
    )
    rdc20 = catalog_electrical.get("conductor_rdc20_ohm_km", cable.dc_resistance_20_ohm_km)
    add_scalar(
        "rdc20", _REQUIRED_FIELDS[2][1], "ELECTRICAL", rdc20, "Ω/km",
        CABLE_VALUE_CATALOG if catalog_electrical.get("conductor_rdc20_ohm_km") else CABLE_VALUE_DERIVED,
        record.source_page if record and catalog_electrical.get("conductor_rdc20_ohm_km") else "Kablo modeli",
        ("VOLTAGE_DROP", "IEC_60287", "FAULT"), True,
    )
    capacitance = catalog_electrical.get("capacitance_uf_km", cable.capacitance_uf_km)
    add_scalar(
        "capacitance", _REQUIRED_FIELDS[3][1], "ELECTRICAL", capacitance, "µF/km",
        CABLE_VALUE_CATALOG if catalog_electrical.get("capacitance_uf_km") else CABLE_VALUE_DERIVED,
        record.source_page if record and catalog_electrical.get("capacitance_uf_km") else "Parametrik geometri",
        ("BONDING", "DIELECTRIC_LOSS"), False,
    )
    overall = catalog_dimensions.get("overall_diameter_mm", cable.overall_diameter_mm)
    add_scalar(
        "overall_diameter", _REQUIRED_FIELDS[4][1], "GEOMETRY", overall, "mm",
        CABLE_VALUE_CATALOG if catalog_dimensions.get("overall_diameter_mm") else CABLE_VALUE_DERIVED,
        record.source_page if record and catalog_dimensions.get("overall_diameter_mm") else "Katman geometrisi",
        ("IEC_60287", "2D_THERMAL"), True,
    )

    conductor_status = _status_from_source(_source_for_layer(cable, conductor)) if conductor else CABLE_VALUE_MISSING
    if conductor_status == CABLE_VALUE_DERIVED:
        conductor_note = "Eşdeğer daire çapıdır; gerçek sıkıştırılmış/segmentli iletken çapı üretici çizimiyle teyit edilmelidir."
        conductor_status = CABLE_VALUE_MANUFACTURER_REQUIRED
    else:
        conductor_note = ""
    add_scalar(
        "conductor_diameter", _REQUIRED_FIELDS[5][1], "GEOMETRY",
        conductor.outer_diameter_mm if conductor else cable.conductor_diameter_mm, "mm", conductor_status,
        conductor.source_id if conductor else "", ("IEC_60287", "BONDING", "2D_THERMAL"), False, conductor_note,
    )

    insulation_status = _status_from_source(_source_for_layer(cable, insulation)) if insulation else CABLE_VALUE_MISSING
    if insulation_status == CABLE_VALUE_ASSUMPTION:
        insulation_status = CABLE_VALUE_MANUFACTURER_REQUIRED
    add_scalar(
        "insulation_outer_diameter", _REQUIRED_FIELDS[6][1], "GEOMETRY",
        insulation.outer_diameter_mm if insulation else cable.t1_outer_diameter_mm, "mm", insulation_status,
        insulation.source_id if insulation else "", ("IEC_60287", "BONDING", "2D_THERMAL"), True,
        "Katalog tam katman çapını vermiyorsa üretici konstrüksiyon çizimi gerekir.",
    )

    screen_source = _source_for_layer(cable, screen) if screen else None
    screen_status = _status_from_source(screen_source)
    add_scalar(
        "screen_area", _REQUIRED_FIELDS[7][1], "METALLIC_SCREEN", cable.sheath_cross_section_mm2, "mm²",
        screen_status, screen.source_id if screen else "", ("BONDING", "FAULT", "SVL"), True,
    )
    wire_ok = bool(screen and screen.wire_count > 0 and screen.wire_diameter_mm > 0)
    items.append(_completion_item(
        "screen_wire_geometry", _REQUIRED_FIELDS[8][1], "METALLIC_SCREEN",
        screen_status if wire_ok else CABLE_VALUE_MANUFACTURER_REQUIRED,
        f"{screen.wire_count} × Ø{screen.wire_diameter_mm:g}" if wire_ok else None,
        "mm", screen.source_id if screen else "", ("BONDING", "FAULT"), False,
        "Toplam ekran kesitinden tel adedi/çapı uydurulmaz.",
    ))

    thermal_layers = [
        layer for layer in cable.layers
        if layer.layer_type.upper() not in {
            "CONDUCTOR", "WIRE_SCREEN", "METALLIC_SCREEN", "METALLIC_SHEATH",
            "LAMINATED_METAL_FOIL", "METAL_FOIL", "ARMOUR",
        }
    ]
    thermal_missing = [layer.name for layer in thermal_layers if layer.thermal_resistivity_km_w <= 0]
    thermal_assumed = [layer.name for layer in thermal_layers if _status_from_source(_source_for_layer(cable, layer)) == CABLE_VALUE_ASSUMPTION]
    thermal_status = CABLE_VALUE_CATALOG
    if thermal_missing:
        thermal_status = CABLE_VALUE_MISSING
    elif thermal_assumed:
        thermal_status = CABLE_VALUE_ASSUMPTION
    items.append(_completion_item(
        "thermal_layers", _REQUIRED_FIELDS[9][1], "THERMAL", thermal_status,
        None if thermal_missing else "Katman bazlı", "K·m/W", ", ".join(sorted({layer.source_id for layer in thermal_layers if layer.source_id})),
        ("IEC_60287", "2D_THERMAL"), True,
        ("Eksik: " + ", ".join(thermal_missing)) if thermal_missing else (
            "Geçici mühendislik varsayımı: " + ", ".join(thermal_assumed) if thermal_assumed else ""
        ),
    ))
    items.append(_completion_item(
        "heat_capacity", _REQUIRED_FIELDS[10][1], "THERMAL", CABLE_VALUE_MANUFACTURER_REQUIRED,
        None, "MJ/m³K", "", ("IEC_60853",), False,
        "Kablo katmanlarının hacimsel ısı kapasiteleri mevcut katalog kayıtlarında verilmemiştir.",
    ))

    bonding_ok = bool(project.bonding.scheme and project.bonding.nodes and project.bonding.minor_sections)
    items.append(_completion_item(
        "bonding_scheme", _REQUIRED_FIELDS[11][1], "BONDING",
        CABLE_VALUE_USER if bonding_ok else CABLE_VALUE_MISSING,
        project.bonding.scheme if bonding_ok else None, "", "Proje bonding modeli",
        ("BONDING", "SVL", "FAULT"), False,
        "Link-box ve topraklama dirençleri saha/as-built değerleriyle teyit edilmelidir.",
    ))
    durations = [scenario.duration_s for scenario in project.fault_study.scenarios if scenario.enabled and scenario.duration_s > 0]
    items.append(_completion_item(
        "fault_duration", _REQUIRED_FIELDS[12][1], "FAULT",
        CABLE_VALUE_USER if durations else CABLE_VALUE_MISSING,
        max(durations) if durations else None, "s", "Proje arıza senaryoları",
        ("FAULT", "SCREEN_SHORT_CIRCUIT"), False,
        "Koruma koordinasyon çalışmasından doğrulanmalıdır.",
    ))

    blocking_count = sum(1 for item in items if item.blocking and item.status == CABLE_VALUE_MISSING)
    manufacturer_count = sum(1 for item in items if item.status == CABLE_VALUE_MANUFACTURER_REQUIRED)
    assumption_count = sum(1 for item in items if item.status == CABLE_VALUE_ASSUMPTION)
    if blocking_count:
        status = "BLOCKED"
    elif manufacturer_count == 0 and assumption_count == 0 and all(item.status != CABLE_VALUE_MISSING for item in items):
        status = "FINAL_DATA_READY"
    elif manufacturer_count or assumption_count:
        status = "CONDITIONAL"
    else:
        status = "PRELIMINARY_READY"
    return CableCompletionReport(tuple(items), blocking_count, manufacturer_count, assumption_count, status)


def resolve_source_conflict(
    project: ProjectData,
    conflict_id: str,
    action: str,
    selected_record_ids: Iterable[str] = (),
    resolved_value: Any = None,
    unit: str = "",
    rationale: str = "",
    decided_by: str = "",
) -> SourceConflictDecision:
    allowed = {CONFLICT_USE_SOURCE, CONFLICT_USE_USER_VALUE, CONFLICT_CREATE_SCENARIOS, CONFLICT_UNRESOLVED}
    if action not in allowed:
        raise ProjectCableApplicationError(f"Geçersiz çelişki kararı: {action}")
    conflict = next((item for item in project.source_audit.conflicts if item.conflict_id == conflict_id), None)
    if conflict is None:
        raise ProjectCableApplicationError(f"Kaynak çelişkisi bulunamadı: {conflict_id}")
    selected = list(selected_record_ids)
    valid_ids = {record.record_id for record in project.source_audit.records}
    if action == CONFLICT_USE_SOURCE and (not selected or any(item not in valid_ids for item in selected)):
        raise ProjectCableApplicationError("Kaynak kullanma kararında geçerli en az bir kayıt seçilmelidir.")
    if action == CONFLICT_USE_USER_VALUE and resolved_value in {None, ""}:
        raise ProjectCableApplicationError("Kullanıcı değeri kararında çözümlenmiş değer gereklidir.")
    decision = SourceConflictDecision(
        conflict_id=conflict_id,
        action=action,
        selected_record_ids=selected,
        resolved_value=resolved_value,
        unit=unit,
        rationale=rationale,
        decided_by=decided_by,
        decided_at=datetime.now().isoformat(timespec="seconds"),
    )
    existing = next((i for i, item in enumerate(project.cable_application.conflict_decisions) if item.conflict_id == conflict_id), None)
    if existing is None:
        project.cable_application.conflict_decisions.append(decision)
    else:
        project.cable_application.conflict_decisions[existing] = decision
    conflict.disposition = action
    selected_record = next((record for record in project.source_audit.records if record.record_id in selected), None)
    parameter_key = conflict.parameter_key.lower()
    effective_value = resolved_value if action == CONFLICT_USE_USER_VALUE else (selected_record.value if selected_record else None)
    if effective_value is not None and parameter_key == "power_factor":
        project.design_basis.power_factor = float(effective_value)
    elif effective_value is not None and parameter_key.endswith("route_length_m"):
        value_m = float(effective_value)
        project.design_basis.total_route_length_m = value_m
        project.thermal_design.route_length_m = value_m
        if project.route_sections:
            project.route_sections[0].length_m = value_m
            project.route_sections[0].start_chainage_m = 0.0
            project.route_sections[0].end_chainage_m = value_m
        if len(project.thermal_design.regions) == 1:
            project.thermal_design.regions[0].start_m = 0.0
            project.thermal_design.regions[0].end_m = value_m
    return decision


def _record(project: ProjectData, record_id: str) -> CableCatalogRecord:
    record = next((item for item in project.cable_library.records if item.record_id == record_id), None)
    if record is None:
        raise ProjectCableApplicationError(f"Katalog kaydı bulunamadı: {record_id}")
    if not record.cable_snapshot:
        raise ProjectCableApplicationError(f"Katalog kaydı proje kablosu oluşturmak için konstrüksiyon verisi içermiyor: {record_id}")
    return record


def apply_catalog_candidate_to_project(
    project: ProjectData,
    record_id: str,
    candidate_id: str = "",
    parallel_cables_per_phase: int = 1,
    route_section_names: Iterable[str] | None = None,
) -> ProjectApplicationResult:
    if parallel_cables_per_phase < 1:
        raise ProjectCableApplicationError("Kablo/faz sayısı en az 1 olmalıdır.")
    record = _record(project, record_id)
    load = apply_load_calculation(project.design_basis)
    snapshot = apply_catalog_record(record)
    snapshot.parallel_cables_per_phase = int(parallel_cables_per_phase)
    snapshot.design_current_a = load.design_current_per_circuit_a / parallel_cables_per_phase
    snapshot.voltage_kv = project.design_basis.system_voltage_kv
    snapshot.frequency_hz = project.design_basis.frequency_hz
    snapshot = create_project_snapshot(snapshot, record_id)

    selected_names = set(route_section_names or [section.name for section in project.route_sections])
    available_names = {section.name for section in project.route_sections}
    unknown = sorted(selected_names - available_names)
    if unknown:
        raise ProjectCableApplicationError("Projede bulunmayan güzergâh bölümü: " + ", ".join(unknown))
    if not selected_names:
        raise ProjectCableApplicationError("En az bir güzergâh bölümü seçilmelidir.")

    project.cable = snapshot
    assignments = [
        RouteCableAssignment(
            assignment_id=f"ASSIGN-{index:03d}",
            route_section_name=section.name,
            cable_snapshot_id=snapshot.snapshot_id,
            catalog_record_id=record_id,
            parallel_cables_per_phase=parallel_cables_per_phase,
            active=section.name in selected_names,
            notes="v0.15.1 proje kablo uygulama iş akışı",
        )
        for index, section in enumerate(project.route_sections, 1)
    ]
    completion = assess_cable_completion(project, record)
    application_status = "APPLIED_CONDITIONAL" if completion.status != "FINAL_DATA_READY" else "APPLIED_FINAL_DATA_READY"
    project.cable_application = CableApplicationData(
        selected_candidate_id=candidate_id or f"{record_id}::P{parallel_cables_per_phase}",
        selected_catalog_record_id=record_id,
        applied_snapshot_id=snapshot.snapshot_id,
        applied_snapshot_hash=snapshot.snapshot_hash,
        assignments=assignments,
        completion_items=[deepcopy(item) for item in completion.items],
        conflict_decisions=deepcopy(project.cable_application.conflict_decisions),
        application_status=application_status,
        last_iteration_status="NOT_RUN",
        notes=REFERENCE,
    )
    project.design_progress.cable = "COMPLETE" if completion.status == "FINAL_DATA_READY" else "CONDITIONAL"
    project.design_progress.thermal = "STALE"
    project.design_progress.bonding = "STALE"
    project.design_progress.fault_epr = "STALE"
    project.design_progress.svl = "STALE"
    project.design_progress.final_design = "NOT_READY"
    project.design_progress.missing_data = [
        item.label for item in completion.items
        if item.status in {CABLE_VALUE_MISSING, CABLE_VALUE_MANUFACTURER_REQUIRED, CABLE_VALUE_ASSUMPTION}
    ]
    trace = (
        REFERENCE,
        f"Katalog kaydı {record_id} değişmez proje içine kopyalanarak atandı.",
        f"Projeye atanmış kablo kaydı {snapshot.snapshot_id}; veri imzası SHA-256 {snapshot.snapshot_hash}.",
        f"{len(selected_names)} güzergâh bölümü aktif atandı; {parallel_cables_per_phase} kablo/faz.",
        f"Tasarım akımı {load.design_current_per_circuit_a:.3f} A/devre; kablo başına {snapshot.design_current_a:.3f} A.",
        f"Veri tamamlama durumu: {completion.status}.",
    )
    return ProjectApplicationResult(
        record_id,
        project.cable_application.selected_candidate_id,
        snapshot.snapshot_id,
        snapshot.snapshot_hash,
        tuple(sorted(selected_names)),
        completion,
        application_status,
        trace,
    )


def calculate_project_voltage_drop(project: ProjectData) -> ProjectVoltageDropResult:
    record = _record(project, project.cable_application.selected_catalog_record_id or project.cable.catalog_record_id)
    electrical = record.catalog_electrical
    resistance = float(
        electrical.get("conductor_rac90_ohm_km")
        or electrical.get("conductor_rdc90_ohm_km")
        or electrical.get("conductor_rdc20_ohm_km")
        or project.cable.dc_resistance_20_ohm_km
        or 0.0
    )
    profile = project.design_basis.installation_profile.upper()
    arrangement_inductance = (
        electrical.get("inductance_trefoil_mh_km")
        if "TREFOIL" in profile
        else electrical.get("inductance_flat_mh_km")
    )
    inductance = float(
        arrangement_inductance
        or electrical.get("inductance_mh_km")
        or 0.0
    )
    if resistance <= 0 or inductance <= 0:
        raise ProjectCableApplicationError("Gerilim düşümü için katalog R ve L verileri eksik.")
    active_assignments = {item.route_section_name for item in project.cable_application.assignments if item.active}
    length_m = sum(section.length_m for section in project.route_sections if section.name in active_assignments)
    if length_m <= 0:
        length_m = project.design_basis.total_route_length_m
    load = apply_load_calculation(project.design_basis)
    parallel = max(1, project.cable.parallel_cables_per_phase)
    current_each = load.design_current_per_circuit_a / parallel
    pf = project.design_basis.power_factor if 0 < project.design_basis.power_factor <= 1 else 1.0
    sin_phi = sqrt(max(0.0, 1.0 - pf * pf))
    x = 2.0 * pi * project.design_basis.frequency_hz * inductance / 1000.0
    drop = sqrt(3.0) * current_each * (length_m / 1000.0) * (resistance * pf + x * sin_phi)
    percent = 100.0 * drop / (project.design_basis.system_voltage_kv * 1000.0)
    return ProjectVoltageDropResult(
        current_each, resistance, x, length_m, drop, percent,
        f"{record.manufacturer} {record.model}; {record.source_page or 'catalog source'}",
    )


def evaluate_application_iteration_gates(project: ProjectData) -> ApplicationIterationSummary:
    completion = assess_cable_completion(project)
    decisions = {item.conflict_id: item for item in project.cable_application.conflict_decisions}
    unresolved = []
    for conflict in project.source_audit.conflicts:
        if conflict.severity.upper() not in {"CRITICAL", "HIGH"}:
            continue
        decision = decisions.get(conflict.conflict_id)
        if decision is not None:
            is_unresolved = decision.action == CONFLICT_UNRESOLVED
        else:
            is_unresolved = str(conflict.disposition or CONFLICT_UNRESOLVED).upper() in {"", CONFLICT_UNRESOLVED}
        if is_unresolved:
            unresolved.append(conflict)
    gates: list[ApplicationIterationGate] = []
    gates.append(ApplicationIterationGate(
        "PROJECT_CABLE", "Projeye atanmış sabit kablo kaydı", "PASS" if project.cable.snapshot_id else "BLOCKED", True,
        project.cable.snapshot_id or "Projeye henüz kablo atanmadı.",
    ))
    gates.append(ApplicationIterationGate(
        "DATA_COMPLETION", "Kablo veri tamamlama", completion.status,
        completion.blocking_count > 0,
        f"Bloke eden eksik: {completion.blocking_count}; üretici teyidi: {completion.manufacturer_confirmation_count}; varsayım: {completion.assumption_count}.",
    ))
    gates.append(ApplicationIterationGate(
        "SOURCE_CONFLICTS", "Kaynak çelişkileri", "PASS" if not unresolved else "BLOCKED", True,
        "Kritik/yüksek çelişkiler karara bağlandı." if not unresolved else f"Kararsız kritik/yüksek çelişki: {len(unresolved)}.",
    ))
    assigned = [item for item in project.cable_application.assignments if item.active]
    gates.append(ApplicationIterationGate(
        "ROUTE_ASSIGNMENT", "Güzergâh kablo ataması", "PASS" if assigned else "BLOCKED", True,
        f"Aktif atama: {len(assigned)} bölüm." if assigned else "Aktif güzergâh ataması yok.",
    ))
    voltage_drop = None
    try:
        voltage_drop = calculate_project_voltage_drop(project)
        gates.append(ApplicationIterationGate(
            "VOLTAGE_DROP", "Gerilim düşümü ön hesabı", "PASS", False,
            f"ΔV = {voltage_drop.voltage_drop_v:.3f} V (%{voltage_drop.voltage_drop_percent:.5f}).",
        ))
    except ProjectCableApplicationError as exc:
        gates.append(ApplicationIterationGate("VOLTAGE_DROP", "Gerilim düşümü ön hesabı", "MISSING", False, str(exc)))

    blocked = any(gate.blocking and gate.status == "BLOCKED" for gate in gates)
    status = "BLOCKED" if blocked else ("CONDITIONAL_READY" if completion.status != "FINAL_DATA_READY" else "READY")
    trace = [REFERENCE]
    trace.extend(f"{gate.gate_id}: {gate.status} — {gate.message}" for gate in gates)
    project.cable_application.last_iteration_status = status
    project.cable_application.last_iteration_trace = trace
    return ApplicationIterationSummary(status, tuple(gates), voltage_drop, tuple(trace))
