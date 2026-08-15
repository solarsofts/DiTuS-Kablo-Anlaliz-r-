from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import isclose
from typing import Any

from ucd.calculations.cable_physical_parameters import (
    MaterialAlphaResolution,
    PhysicalParameterInputError,
    resolve_material_alpha_20_per_c,
)

from ucd.models.project import (
    CALC_METHOD_CERTIFIED_INPUT,
    CALC_METHOD_LEGACY_COEFFICIENT,
    CALC_METHOD_MANUAL_OVERRIDE,
    CALC_METHOD_PHYSICAL_AUTO,
    CALC_STATUS_CALCULATED,
    CALC_STATUS_PRELIMINARY_ONLY,
    CALC_STATUS_REQUIRES_CONFIRMATION,
    CALC_STATUS_VERIFIED,
    CalculationPolicyData,
    ParameterProvenanceRecord,
    ProjectData,
)

REFERENCE = "DiTuS v0.16.4 calculation policy and parameter provenance layer"


@dataclass(frozen=True)
class ParameterSpecification:
    parameter_path: str
    label: str
    unit: str
    category: str
    preferred_method: str
    standard_reference: str = ""
    validity_scope: str = ""
    legacy_default: bool = False


@dataclass
class CalculationPolicyIssue:
    severity: str
    parameter_path: str
    code: str
    message: str


@dataclass
class CalculationPolicyAudit:
    records: list[ParameterProvenanceRecord] = field(default_factory=list)
    issues: list[CalculationPolicyIssue] = field(default_factory=list)
    method_counts: dict[str, int] = field(default_factory=dict)
    status_counts: dict[str, int] = field(default_factory=dict)
    final_design_blocked: bool = False
    audited_at: str = ""

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "WARNING")


PARAMETER_SPECIFICATIONS: tuple[ParameterSpecification, ...] = (
    ParameterSpecification(
        "cable.conductor_area_mm2", "İletken nominal kesiti", "mm²", "CONDUCTOR",
        CALC_METHOD_CERTIFIED_INPUT, "IEC 60228 / üretici kablo verisi",
        "Seçilen fiziksel kablo snapshot'ı",
    ),
    ParameterSpecification(
        "cable.dc_resistance_20_ohm_km", "İletken DC direnci (20 °C)", "Ω/km", "CONDUCTOR",
        CALC_METHOD_CERTIFIED_INPUT, "IEC 60228 / üretici test veya katalog verisi",
        "İletken malzemesi, yapısı ve kesiti",
    ),
    ParameterSpecification(
        "cable.temperature_coefficient_20_per_c", "İletken sıcaklık katsayısı α20", "1/°C", "CONDUCTOR",
        CALC_METHOD_CERTIFIED_INPUT, "IEC 60287-1-1 malzeme parametresi",
        "İletken malzemesi",
    ),
    ParameterSpecification(
        "cable.sheath_temperature_coefficient_20_per_c", "Metalik kılıf sıcaklık katsayısı α20", "1/°C", "METALLIC_SHEATH",
        CALC_METHOD_CERTIFIED_INPUT, "IEC 60287-1-1 malzeme parametresi",
        "Metalik kılıf/ekran malzemesi",
    ),
    ParameterSpecification(
        "cable.conductor_shape", "İletken şekli", "-", "CONDUCTOR_CONSTRUCTION",
        CALC_METHOD_CERTIFIED_INPUT, "IEC 60287-1-1 yapı sınıflandırması / üretici kesit çizimi",
        "Fiziksel skin/proximity katsayı çözüm kapsamı",
    ),
    ParameterSpecification(
        "cable.conductor_stranding_type", "İletken tel/segment yapısı", "-", "CONDUCTOR_CONSTRUCTION",
        CALC_METHOD_CERTIFIED_INPUT, "IEC 60287-1-1 ks/kp yapı tablosu / üretici kesit çizimi",
        "Solid, stranded, Milliken veya özel yapı",
    ),
    ParameterSpecification(
        "cable.conductor_insulation_system", "İzolasyon sistemi sınıfı", "-", "CONDUCTOR_CONSTRUCTION",
        CALC_METHOD_CERTIFIED_INPUT, "IEC 60287-1-1 ks/kp yapı tablosu",
        "Extruded/mineral veya fluid/paper/PPL sınıfı",
    ),
    ParameterSpecification(
        "cable.milliken_wire_profile", "Cu Milliken tel profili", "-", "CONDUCTOR_CONSTRUCTION",
        CALC_METHOD_CERTIFIED_INPUT, "IEC 60287-1-1 ks/kp yapı tablosu / üretici çizimi",
        "Insulated, bare uni-directional veya bare bi-directional",
    ),
    ParameterSpecification(
        "cable.skin_effect_coefficient_ks", "Skin yapı katsayısı ks", "-", "AC_RESISTANCE",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-1-1",
        "0 ise iletken yapı tablosundan çözülür; pozitif değer izlenebilir açık girdidir",
    ),
    ParameterSpecification(
        "cable.proximity_effect_coefficient_kp", "Proximity yapı katsayısı kp", "-", "AC_RESISTANCE",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-1-1",
        "0 ise iletken yapı tablosundan çözülür; pozitif değer izlenebilir açık girdidir",
    ),
    ParameterSpecification(
        "cable.skin_effect_factor", "Skin effect faktörü ys", "-", "AC_RESISTANCE",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-1-1",
        "Tek damarlı kablo, 50/60 Hz; iletken yapısı doğrulanmalıdır", True,
    ),
    ParameterSpecification(
        "cable.proximity_effect_factor", "Proximity effect faktörü yp", "-", "AC_RESISTANCE",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-1-1",
        "Gerçek kablo formasyonu ve faz yerleşimi", True,
    ),
    ParameterSpecification(
        "cable.capacitance_uf_km", "Kapasitans", "µF/km", "DIELECTRIC",
        CALC_METHOD_CERTIFIED_INPUT, "Üretici test/katalog verisi veya katman geometrisi kontrolü",
        "Kablo katman geometrisi ve dielektrik özellikleri", True,
    ),
    ParameterSpecification(
        "cable.dielectric_loss_tan_delta", "Dielektrik kayıp faktörü tanδ", "-", "DIELECTRIC",
        CALC_METHOD_CERTIFIED_INPUT, "Üretici test/malzeme verisi",
        "İzolasyon malzemesi, sıcaklık ve frekans", True,
    ),
    ParameterSpecification(
        "cable.sheath_cross_section_mm2", "Metalik kılıf/screen kesiti", "mm²", "SHEATH",
        CALC_METHOD_CERTIFIED_INPUT, "Üretici kablo kesit çizimi",
        "Seçilen kablo yapısı",
    ),
    ParameterSpecification(
        "cable.sheath_dc_resistance_20_ohm_km", "Metalik kılıf DC direnci (20 °C)", "Ω/km", "SHEATH",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287 / IEEE 575 bonding girdisi",
        "Kılıf malzemesi ve gerçek metal kesiti",
    ),
    ParameterSpecification(
        "cable.sheath_loss_factor", "Metalik kılıf kayıp oranı λ1", "-", "SHEATH_LOSS",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-1-1/-1-3; IEEE 575; CIGRE TB 797",
        "Bonding şeması, gerçek geometri ve işletme akımları", True,
    ),
    ParameterSpecification(
        "cable.armour_loss_factor", "Zırh kayıp oranı λ2", "-", "ARMOUR_LOSS",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-1-1",
        "Zırh tipi ve manyetik özellikleri doğrulanmalıdır", True,
    ),
    ParameterSpecification(
        "cable.thermal_resistance_t1_km_w", "İç termal direnç T1", "K·m/W", "THERMAL_INTERNAL",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-2-1",
        "Kablo iç katman geometrisi ve ısıl özdirençleri",
    ),
    ParameterSpecification(
        "cable.thermal_resistance_t2_km_w", "İç termal direnç T2", "K·m/W", "THERMAL_INTERNAL",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-2-1",
        "Kablo iç katman geometrisi ve ısıl özdirençleri",
    ),
    ParameterSpecification(
        "cable.thermal_resistance_t3_km_w", "İç termal direnç T3", "K·m/W", "THERMAL_INTERNAL",
        CALC_METHOD_PHYSICAL_AUTO, "IEC 60287-2-1",
        "Kablo dış katman geometrisi ve ısıl özdirençleri",
    ),
    ParameterSpecification(
        "design_basis.soil_thermal_resistivity_km_w", "Zemin ısıl özdirenci", "K·m/W", "THERMAL_EXTERNAL",
        CALC_METHOD_CERTIFIED_INPUT, "Saha/laboratuvar ölçümü; IEC 60287-2-1 proje girdisi",
        "Güzergâh bölgesi, nem ve mevsim koşulları", True,
    ),
    ParameterSpecification(
        "design_basis.burial_depth_m", "Gömülme derinliği", "m", "INSTALLATION",
        CALC_METHOD_CERTIFIED_INPUT, "As-built / tasarım kesiti",
        "Güzergâh bölgesi",
    ),
    ParameterSpecification(
        "design_basis.phase_spacing_m", "Fazlar arası merkez mesafesi", "m", "INSTALLATION",
        CALC_METHOD_CERTIFIED_INPUT, "As-built / tasarım kesiti",
        "Legacy Trefoil/Flat ön model; fiziksel x-y kesit ana modele geçecektir",
    ),
    ParameterSpecification(
        "design_basis.circuit_spacing_m", "Devreler arası merkez mesafesi", "m", "INSTALLATION",
        CALC_METHOD_CERTIFIED_INPUT, "As-built / tasarım kesiti",
        "Legacy çoklu devre ön modeli; fiziksel x-y kesit ana modele geçecektir",
    ),
)


def _read_path(project: ProjectData, parameter_path: str) -> Any:
    current: Any = project
    for token in parameter_path.split("."):
        current = getattr(current, token)
    return current


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _record_id(parameter_path: str) -> str:
    return "PAR-" + parameter_path.replace(".", "-").replace("_", "-").upper()


def _has_verified_cable_source(project: ProjectData) -> bool:
    return any(bool(source.verified) for source in project.cable.parameter_sources)


def _catalog_identity(project: ProjectData) -> str:
    cable = project.cable
    bits = [cable.manufacturer, cable.series, cable.model]
    return " / ".join(bit.strip() for bit in bits if str(bit).strip())


AUTO_ALPHA_MIGRATION_SOURCE_TYPES = frozenset({
    "PROJECT_CABLE_SNAPSHOT",
    "GENERIC_TEMPLATE",
})
ALPHA_PARAMETER_PATHS = {
    "cable.temperature_coefficient_20_per_c": ("conductor_material", "temperature_coefficient_20_per_c"),
    "cable.sheath_temperature_coefficient_20_per_c": ("sheath_material", "sheath_temperature_coefficient_20_per_c"),
}


def _alpha_material_and_value(project: ProjectData, path: str) -> tuple[str, float]:
    material_field, value_field = ALPHA_PARAMETER_PATHS[path]
    return str(getattr(project.cable, material_field)), float(getattr(project.cable, value_field))


def _record_is_explicit_alpha_override(record: ParameterProvenanceRecord | None) -> bool:
    if record is None:
        return False
    if record.method == CALC_METHOD_MANUAL_OVERRIDE:
        return True
    return str(record.source_type or "").upper() not in (
        AUTO_ALPHA_MIGRATION_SOURCE_TYPES | {"MATERIAL_DEFAULT"}
    )


def _classify_alpha_value(
    project: ProjectData, path: str, record: ParameterProvenanceRecord | None = None
) -> MaterialAlphaResolution:
    material, value = _alpha_material_and_value(project, path)
    return resolve_material_alpha_20_per_c(
        material, value, explicit_override=_record_is_explicit_alpha_override(record)
    )


def _migrate_alpha_defaults(project: ProjectData) -> bool:
    """Migrate only historical automatic alpha records; preserve manual/field sources."""
    records = {item.parameter_path: item for item in project.calculation_policy.parameter_records}
    changed = False
    for path, (_material_field, value_field) in ALPHA_PARAMETER_PATHS.items():
        record = records.get(path)
        if record is not None and _record_is_explicit_alpha_override(record):
            continue
        try:
            resolution = _classify_alpha_value(project, path, record)
        except PhysicalParameterInputError:
            continue
        old_value = float(getattr(project.cable, value_field))
        if not isclose(old_value, resolution.value_per_c, rel_tol=1e-6, abs_tol=1e-9):
            setattr(project.cable, value_field, resolution.value_per_c)
            changed = True
        if record is None:
            continue
        # The irreversible migration surface is deliberately limited to the two
        # historical automatic source types named in AUTO_ALPHA_MIGRATION_SOURCE_TYPES.
        if str(record.source_type or "").upper() not in AUTO_ALPHA_MIGRATION_SOURCE_TYPES:
            continue
        record.value_snapshot = resolution.value_per_c
        if resolution.source_type == "MATERIAL_DEFAULT":
            record.method = CALC_METHOD_PHYSICAL_AUTO
            record.status = CALC_STATUS_CALCULATED
            record.source_type = "MATERIAL_DEFAULT"
            record.source_reference = resolution.source_reference
            record.confidence = "HIGH"
            record.notes = (
                "Malzeme profilinden türetildi; tarihsel 0.00393 şema varsayılanı "
                "Cu dışındaki tanınan malzemelerde korunmaz."
            )
        else:
            record.method = CALC_METHOD_CERTIFIED_INPUT
            record.status = CALC_STATUS_REQUIRES_CONFIRMATION
            record.source_type = "EXPLICIT_COEFFICIENT"
            record.source_reference = "Malzeme varsayılanından farklı legacy snapshot değeri"
            record.confidence = "MEDIUM"
            record.notes = "Alan bazlı kaynak doğrulanana kadar açık katsayı girdisi kabul edilir."
        record.updated_at = _now()
        changed = True
    return changed


def resolve_project_alpha_20_per_c(
    project: ProjectData, parameter_path: str
) -> MaterialAlphaResolution:
    if parameter_path not in ALPHA_PARAMETER_PATHS:
        raise KeyError(parameter_path)
    bootstrap_calculation_policy(project)
    record = next((
        item for item in project.calculation_policy.parameter_records
        if item.parameter_path == parameter_path
    ), None)
    return _classify_alpha_value(project, parameter_path, record)


def _initial_method_and_status(
    project: ProjectData,
    specification: ParameterSpecification,
    value: Any,
) -> tuple[str, str, str, str, str]:
    path = specification.parameter_path
    verified_source = _has_verified_cable_source(project)
    catalog_identity = _catalog_identity(project)
    snapshot_present = bool(project.cable.snapshot_id or project.cable.catalog_record_id)

    if path in ALPHA_PARAMETER_PATHS:
        try:
            resolution = _classify_alpha_value(project, path)
        except PhysicalParameterInputError as exc:
            return (
                CALC_METHOD_CERTIFIED_INPUT,
                CALC_STATUS_REQUIRES_CONFIRMATION,
                "EXPLICIT_COEFFICIENT",
                "Çözülemeyen malzeme/katsayı girdisi",
                str(exc),
            )
        if resolution.source_type == "MATERIAL_DEFAULT":
            return (
                CALC_METHOD_PHYSICAL_AUTO,
                CALC_STATUS_CALCULATED,
                "MATERIAL_DEFAULT",
                resolution.source_reference,
                "Malzeme profilinden çözülen α20; alan bazlı açık kaynak bunu geçersiz kılabilir.",
            )
        return (
            CALC_METHOD_CERTIFIED_INPUT,
            CALC_STATUS_REQUIRES_CONFIRMATION,
            "EXPLICIT_COEFFICIENT",
            resolution.source_reference,
            "Malzeme varsayılanından farklı değer; alan bazlı kaynak doğrulanmalıdır.",
        )

    if path in {
        "cable.skin_effect_coefficient_ks",
        "cable.proximity_effect_coefficient_kp",
    }:
        numeric = float(value or 0.0)
        if numeric <= 0.0:
            return (
                CALC_METHOD_PHYSICAL_AUTO,
                CALC_STATUS_CALCULATED,
                "IEC_CONSTRUCTION_RESOLVER",
                "v0.16.4 iletken yapı tablosu çözümü",
                "Sonuç, iletken şekli/tel yapısı/izolasyon sınıfı doğrulanmışsa geçerlidir.",
            )
        return (
            CALC_METHOD_CERTIFIED_INPUT,
            CALC_STATUS_REQUIRES_CONFIRMATION,
            "EXPLICIT_COEFFICIENT",
            "Açık ks/kp girdisi",
            "Kaynak belgesi ve katsayı çiftinin birlikte girildiği doğrulanmalıdır.",
        )

    if path in {
        "cable.skin_effect_factor",
        "cable.proximity_effect_factor",
        "cable.sheath_loss_factor",
        "cable.armour_loss_factor",
    }:
        return (
            CALC_METHOD_LEGACY_COEFFICIENT,
            CALC_STATUS_PRELIMINARY_ONLY,
            "LEGACY_SCALAR",
            "v0.16.3 kilitli skaler kablo girdisi",
            "Fiziksel parametre/bonding motoru devreye girene kadar yalnız ön tasarım.",
        )

    if path == "cable.dc_resistance_20_ohm_km" and float(value or 0.0) <= 0.0:
        return (
            CALC_METHOD_PHYSICAL_AUTO,
            CALC_STATUS_CALCULATED,
            "GEOMETRY_DERIVED",
            "Nominal kesit ve malzeme özdirencinden mevcut IEC çekirdeğinde türetilir",
            "Üretici/test Rdc değeri girildiğinde karşılaştırılmalıdır.",
        )

    if path == "cable.sheath_dc_resistance_20_ohm_km" and float(value or 0.0) <= 0.0:
        return (
            CALC_METHOD_PHYSICAL_AUTO,
            CALC_STATUS_CALCULATED,
            "GEOMETRY_DERIVED",
            "Kılıf metal kesiti ve özdirencinden bonding çekirdeğinde türetilir",
            "Üretici/test kılıf direnci girildiğinde karşılaştırılmalıdır.",
        )

    if path.startswith("cable.thermal_resistance_t"):
        if str(project.cable.internal_thermal_mode).upper() == "AUTO_GEOMETRY":
            return (
                CALC_METHOD_PHYSICAL_AUTO,
                CALC_STATUS_CALCULATED,
                "GEOMETRY_DERIVED",
                "Kablo katman geometrisi ve ısıl özdirençlerinden",
                "Mevcut fiziksel iç termal katman hesabı.",
            )
        return (
            CALC_METHOD_MANUAL_OVERRIDE,
            CALC_STATUS_REQUIRES_CONFIRMATION,
            "PROJECT_INPUT",
            "Manuel T1/T2/T3 girdisi",
            "Kaynak ve geçerlilik kapsamı doğrulanmalıdır.",
        )

    if path == "design_basis.soil_thermal_resistivity_km_w":
        source = str(project.design_basis.soil_thermal_value_source or "").upper()
        if any(token in source for token in ("TEST", "MEASURE", "SAHA", "LAB", "VERIFIED")):
            return (
                CALC_METHOD_CERTIFIED_INPUT,
                CALC_STATUS_VERIFIED,
                "SITE_TEST",
                project.design_basis.soil_thermal_value_source,
                "Saha/laboratuvar ölçüm kaydı proje dosyasına bağlanmalıdır.",
            )
        return (
            CALC_METHOD_LEGACY_COEFFICIENT,
            CALC_STATUS_PRELIMINARY_ONLY,
            "PROJECT_ASSUMPTION",
            project.design_basis.soil_thermal_value_source or "PRELIMINARY_ASSUMPTION",
            "Nihai tasarım için güzergâh bölgesi bazında ölçüm/teyit gerekir.",
        )

    if snapshot_present and (verified_source or project.cable.data_status == "VERIFIED"):
        return (
            CALC_METHOD_CERTIFIED_INPUT,
            CALC_STATUS_VERIFIED,
            "PROJECT_CABLE_SNAPSHOT",
            catalog_identity or project.cable.snapshot_id,
            "Projeye kopyalanmış ve izlenebilir kablo snapshot'ı.",
        )

    if snapshot_present:
        return (
            CALC_METHOD_CERTIFIED_INPUT,
            CALC_STATUS_REQUIRES_CONFIRMATION,
            "PROJECT_CABLE_SNAPSHOT",
            catalog_identity or project.cable.snapshot_id,
            "Snapshot mevcut; kaynak doğrulama durumu tamamlanmamış.",
        )

    if specification.legacy_default:
        return (
            CALC_METHOD_LEGACY_COEFFICIENT,
            CALC_STATUS_PRELIMINARY_ONLY,
            "GENERIC_TEMPLATE",
            "DiTuS jenerik kablo şablonu",
            "Üretici/test verisi veya fiziksel hesap ile değiştirilmelidir.",
        )

    return (
        specification.preferred_method,
        CALC_STATUS_REQUIRES_CONFIRMATION,
        "PROJECT_INPUT",
        "Proje skaler girdisi",
        "Kaynak belgesi eklenmemiş veya doğrulanmamış.",
    )


def bootstrap_calculation_policy(project: ProjectData) -> CalculationPolicyData:
    """Create missing provenance records without changing any solver input value."""

    policy = project.calculation_policy
    changed = _migrate_alpha_defaults(project)
    existing = {record.parameter_path: record for record in policy.parameter_records}
    for specification in PARAMETER_SPECIFICATIONS:
        if specification.parameter_path in existing:
            continue
        value = _read_path(project, specification.parameter_path)
        method, status, source_type, source_reference, notes = _initial_method_and_status(
            project, specification, value
        )
        policy.parameter_records.append(ParameterProvenanceRecord(
            record_id=_record_id(specification.parameter_path),
            parameter_path=specification.parameter_path,
            label=specification.label,
            value_snapshot=value,
            unit=specification.unit,
            category=specification.category,
            method=method,
            status=status,
            source_type=source_type,
            source_reference=source_reference,
            standard_reference=specification.standard_reference,
            validity_scope=specification.validity_scope,
            confidence="HIGH" if status == CALC_STATUS_VERIFIED else "MEDIUM",
            notes=notes,
            updated_at=_now(),
        ))
        changed = True
    if changed or not policy.policy_revision:
        policy.policy_revision = "0.16.4"
    return policy


def find_parameter_record(
    project: ProjectData, parameter_path: str
) -> ParameterProvenanceRecord | None:
    bootstrap_calculation_policy(project)
    return next(
        (record for record in project.calculation_policy.parameter_records
         if record.parameter_path == parameter_path),
        None,
    )


def register_parameter_provenance(
    project: ProjectData,
    parameter_path: str,
    *,
    method: str,
    status: str,
    source_type: str,
    source_reference: str,
    standard_reference: str = "",
    source_page: str = "",
    validity_scope: str = "",
    confidence: str = "HIGH",
    override_reason: str = "",
    notes: str = "",
) -> ParameterProvenanceRecord:
    """Update provenance metadata for a value already written by the caller.

    The function deliberately does not write the engineering value itself. This
    keeps v0.16.4 shadow-mode numerically neutral and prevents metadata edits from silently
    changing a solver input.
    """

    record = find_parameter_record(project, parameter_path)
    if record is None:
        raise KeyError(f"Bilinmeyen hesap parametresi: {parameter_path}")
    record.value_snapshot = _read_path(project, parameter_path)
    record.method = method
    record.status = status
    record.source_type = source_type
    record.source_reference = source_reference
    record.standard_reference = standard_reference or record.standard_reference
    record.source_page = source_page
    record.validity_scope = validity_scope or record.validity_scope
    record.confidence = confidence
    record.override_reason = override_reason
    record.notes = notes
    record.updated_at = _now()
    return record


def register_physical_calculation(
    project: ProjectData,
    parameter_path: str,
    *,
    source_reference: str,
    standard_reference: str,
    validity_scope: str = "",
    notes: str = "",
) -> ParameterProvenanceRecord:
    return register_parameter_provenance(
        project,
        parameter_path,
        method=CALC_METHOD_PHYSICAL_AUTO,
        status=CALC_STATUS_CALCULATED,
        source_type="CALCULATION_ENGINE",
        source_reference=source_reference,
        standard_reference=standard_reference,
        validity_scope=validity_scope,
        confidence="HIGH",
        notes=notes,
    )


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-12)
    return left == right


def audit_calculation_policy(project: ProjectData) -> CalculationPolicyAudit:
    policy = bootstrap_calculation_policy(project)
    issues: list[CalculationPolicyIssue] = []
    method_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}

    for record in policy.parameter_records:
        method_counts[record.method] = method_counts.get(record.method, 0) + 1
        status_counts[record.status] = status_counts.get(record.status, 0) + 1
        try:
            current_value = _read_path(project, record.parameter_path)
        except AttributeError:
            issues.append(CalculationPolicyIssue(
                "ERROR", record.parameter_path, "PARAMETER_PATH_INVALID",
                "Parametre yolu proje veri modelinde bulunamadı.",
            ))
            continue

        if not _values_equal(current_value, record.value_snapshot):
            issues.append(CalculationPolicyIssue(
                "WARNING", record.parameter_path, "VALUE_CHANGED_WITHOUT_PROVENANCE",
                f"Güncel değer {current_value!r}; kayıtlı kaynak anındaki değer {record.value_snapshot!r}. "
                "Değişikliğin kaynak/yöntem kaydı yenilenmelidir.",
            ))

        if record.method == CALC_METHOD_MANUAL_OVERRIDE and not record.override_reason.strip():
            issues.append(CalculationPolicyIssue(
                "WARNING", record.parameter_path, "OVERRIDE_REASON_MISSING",
                "Manuel override için gerekçe girilmemiş.",
            ))

        if record.method == CALC_METHOD_LEGACY_COEFFICIENT:
            severity = "ERROR" if policy.block_final_with_legacy_coefficients else "WARNING"
            issues.append(CalculationPolicyIssue(
                severity, record.parameter_path, "LEGACY_COEFFICIENT_ACTIVE",
                "Legacy/varsayılan katsayı etkin. Yalnız ön tasarımda kullanılmalıdır.",
            ))

        if record.status in {CALC_STATUS_PRELIMINARY_ONLY, CALC_STATUS_REQUIRES_CONFIRMATION}:
            issues.append(CalculationPolicyIssue(
                "WARNING", record.parameter_path, "PARAMETER_NOT_FINAL",
                f"Parametre statüsü nihai tasarıma hazır değil: {record.status}.",
            ))

        if not record.source_reference.strip():
            issues.append(CalculationPolicyIssue(
                "WARNING", record.parameter_path, "SOURCE_REFERENCE_MISSING",
                "Kaynak referansı boş.",
            ))

    final_blocked = any(issue.severity == "ERROR" for issue in issues)
    audited_at = _now()
    policy.last_audited_at = audited_at
    return CalculationPolicyAudit(
        records=list(policy.parameter_records),
        issues=issues,
        method_counts=method_counts,
        status_counts=status_counts,
        final_design_blocked=final_blocked,
        audited_at=audited_at,
    )


def render_calculation_policy_audit(project: ProjectData) -> str:
    audit = audit_calculation_policy(project)
    lines = [
        "HESAP PARAMETRELERİ VE KAYNAK DENETİMİ",
        "=" * 78,
        f"Denetim zamanı: {audit.audited_at}",
        f"Kayıt sayısı: {len(audit.records)}",
        f"Uyarı: {audit.warning_count} | Hata: {audit.error_count}",
        f"Nihai tasarım kapısı: {'BLOKE' if audit.final_design_blocked else 'AÇIK'}",
        "",
        "PARAMETRE KAYITLARI",
        "-" * 78,
    ]
    for record in audit.records:
        try:
            current_value = _read_path(project, record.parameter_path)
        except AttributeError:
            current_value = "<bulunamadı>"
        lines.append(
            f"{record.label}: {current_value} {record.unit} | {record.method} | {record.status} | "
            f"{record.source_reference or '-'}"
        )
    if audit.issues:
        lines.extend(["", "BULGULAR", "-" * 78])
        lines.extend(
            f"[{issue.severity}] {issue.parameter_path} / {issue.code}: {issue.message}"
            for issue in audit.issues
        )
    return "\n".join(lines)
