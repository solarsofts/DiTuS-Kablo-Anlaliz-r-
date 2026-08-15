from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from math import isfinite, log, pi, sqrt
from typing import Any

from ucd.calculations.thermal_resistance import (
    ThermalInputError,
    resolve_internal_thermal_resistance,
)
from ucd.models.project import CableData, ProjectData, RouteSection


REFERENCE = "IEC 60287-1-1:2023 cable-loss parameter layer; CIGRE TB 880/TB 894 verification targets"
EPSILON_0_F_M = 8.8541878128e-12


class PhysicalParameterInputError(ValueError):
    pass


@dataclass(frozen=True)
class PhysicalParameterIssue:
    severity: str
    code: str
    parameter: str
    message: str


@dataclass(frozen=True)
class ConstructionCoefficientResult:
    supported: bool
    ks: float
    kp: float
    source: str
    scope: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AcResistanceResolution:
    rdc20_ohm_km: float
    rdc_temperature_ohm_km: float
    ac_resistance_ohm_km: float
    alpha20_per_c: float
    alpha_source: str
    ks: float
    kp: float
    xs: float
    xp: float
    ys: float
    yp: float
    coefficient_source: str
    coefficient_scope: str
    phase_spacing_m: float | None
    used_legacy_fallback: bool
    trace: tuple[str, ...] = ()


@dataclass
class PhysicalCableParameterResult:
    cable_id: str
    cable_name: str
    route_section_name: str
    mode: str
    target_temperature_c: float
    supported_for_ac_resistance: bool
    final_design_ready: bool

    rdc20_input_ohm_km: float
    rdc20_geometry_ohm_km: float
    rdc20_basis_ohm_km: float
    rdc20_basis_source: str
    material_alpha_reference_per_c: float
    alpha_used_per_c: float
    rdc_temperature_ohm_km: float

    ks: float
    kp: float
    coefficient_source: str
    xs: float
    xp: float
    skin_effect_factor_ys: float
    proximity_effect_factor_yp: float
    physical_ac_resistance_ohm_km: float

    legacy_skin_effect_factor_ys: float
    legacy_proximity_effect_factor_yp: float
    legacy_ac_resistance_ohm_km: float
    ac_resistance_difference_percent: float

    capacitance_input_uf_km: float
    capacitance_geometry_uf_km: float
    capacitance_difference_percent: float
    dielectric_loss_input_w_m: float
    dielectric_loss_geometry_w_m: float

    sheath_resistance_input_ohm_km: float
    sheath_resistance_geometry_ohm_km: float
    sheath_resistance_basis_ohm_km: float
    sheath_resistance_basis_source: str

    conductor_equivalent_radius_mm: float
    conductor_gmr_mm: float
    sheath_gmr_mm: float
    t1_km_w: float
    t2_km_w: float
    t3_km_w: float

    issues: list[PhysicalParameterIssue] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    calculated_at: str = ""
    reference: str = REFERENCE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "WARNING")


def _normalized(value: str) -> str:
    return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")


def _positive(name: str, value: float, *, allow_zero: bool = False) -> float:
    value = float(value)
    if (allow_zero and value < 0.0) or (not allow_zero and value <= 0.0):
        relation = "negatif olamaz" if allow_zero else "sıfırdan büyük olmalı"
        raise PhysicalParameterInputError(f"{name} {relation}: {value}")
    return value


def _percent_difference(candidate: float, reference: float) -> float:
    if abs(reference) <= 1e-15:
        return 0.0 if abs(candidate) <= 1e-15 else float("inf")
    return 100.0 * (candidate - reference) / reference


def material_resistivity_20_ohm_m(material: str) -> float:
    key = _normalized(material)
    values = {
        "CU": 1.7241e-8,
        "COPPER": 1.7241e-8,
        "BAKIR": 1.7241e-8,
        "AL": 2.8264e-8,
        "ALUMINIUM": 2.8264e-8,
        "ALUMINUM": 2.8264e-8,
        "ALÜMINYUM": 2.8264e-8,
        "ALUMINYUM": 2.8264e-8,
        "PB": 21.4e-8,
        "LEAD": 21.4e-8,
        "KURŞUN": 21.4e-8,
        "KURSUN": 21.4e-8,
        "BRONZE": 3.5e-8,
        "BRONZ": 3.5e-8,
    }
    if key not in values:
        raise PhysicalParameterInputError(
            f"20 °C özdirenci tanımlı olmayan malzeme: {material}. Sertifikalı direnç girilmelidir."
        )
    return values[key]


def material_alpha_20_per_c(material: str) -> float:
    key = _normalized(material)
    if key in {"CU", "COPPER", "BAKIR"}:
        return 0.00393
    if key in {"AL", "ALUMINIUM", "ALUMINUM", "ALÜMINYUM", "ALUMINYUM"}:
        return 0.00403
    if key in {"PB", "LEAD", "KURŞUN", "KURSUN"}:
        return 0.00400
    if key in {"BRONZE", "BRONZ"}:
        return 0.00300
    raise PhysicalParameterInputError(f"Sıcaklık katsayısı tanımlı olmayan malzeme: {material}")




# Historical CableData schema default through project schema 0.16.4.
# This heuristic can be retired once parameter_sources carries an explicit
# field-level binding for temperature_coefficient_20_per_c and
# sheath_temperature_coefficient_20_per_c.
LEGACY_SCHEMA_ALPHA_DEFAULT = 0.00393


@dataclass(frozen=True)
class MaterialAlphaResolution:
    value_per_c: float
    source_type: str
    source_reference: str
    migrated_legacy_default: bool = False
    explicit_override: bool = False


def resolve_material_alpha_20_per_c(
    material: str,
    stored_value: float,
    *,
    explicit_override: bool = False,
    absolute_tolerance: float = 1e-9,
    relative_tolerance: float = 1e-6,
) -> MaterialAlphaResolution:
    """Resolve an effective alpha20 without preserving the historical Cu default on Al.

    A caller may mark the scalar as an explicit field-level override. Otherwise
    the material default wins when the scalar equals either that default or the
    historical schema-wide 0.00393 default. A genuinely different positive
    value is retained as an explicit, confirmation-requiring coefficient.
    """
    from math import isclose, isfinite

    value = float(stored_value)
    if not isfinite(value) or value < 0.0:
        raise PhysicalParameterInputError(f"Sıcaklık katsayısı geçersiz: {stored_value}")
    material_default = material_alpha_20_per_c(material)
    material_key = _normalized(material)
    if explicit_override:
        if value <= 0.0:
            raise PhysicalParameterInputError(
                "Açık sıcaklık katsayısı sıfırdan büyük olmalıdır."
            )
        return MaterialAlphaResolution(
            value, "EXPLICIT_COEFFICIENT", "Alan bazlı doğrulanmış kullanıcı/katalog girdisi",
            explicit_override=True,
        )
    if isclose(value, material_default, rel_tol=relative_tolerance, abs_tol=absolute_tolerance):
        return MaterialAlphaResolution(
            material_default, "MATERIAL_DEFAULT", f"MATERIAL_DEFAULT_{material_key}"
        )
    if isclose(value, LEGACY_SCHEMA_ALPHA_DEFAULT, rel_tol=relative_tolerance, abs_tol=absolute_tolerance):
        return MaterialAlphaResolution(
            material_default, "MATERIAL_DEFAULT", f"MATERIAL_DEFAULT_{material_key}",
            migrated_legacy_default=not isclose(
                material_default, LEGACY_SCHEMA_ALPHA_DEFAULT,
                rel_tol=relative_tolerance, abs_tol=absolute_tolerance,
            ),
        )
    if value <= 0.0:
        raise PhysicalParameterInputError(
            "Sıcaklık katsayısı sıfırdan büyük olmalıdır."
        )
    return MaterialAlphaResolution(
        value, "EXPLICIT_COEFFICIENT", "Malzeme varsayılanından farklı skaler girdi",
        explicit_override=True,
    )


def geometry_dc_resistance_20_ohm_km(material: str, area_mm2: float) -> float:
    area = _positive("Gerçek metal kesiti", area_mm2)
    return material_resistivity_20_ohm_m(material) * 1e9 / area


def resolve_construction_coefficients(cable: CableData) -> ConstructionCoefficientResult:
    """Resolve IEC empirical ks/kp coefficients without inventing Milliken details.

    Explicit positive ks/kp values are accepted as a traceable input pair.  Zero
    means resolve from the conductor construction.  A Cu Milliken conductor is
    not resolved until the wire profile is stated because the IEC table contains
    materially different coefficient pairs for insulated, uni-directional and
    bi-directional wire constructions.
    """

    explicit_ks = float(cable.skin_effect_coefficient_ks or 0.0)
    explicit_kp = float(cable.proximity_effect_coefficient_kp or 0.0)
    if explicit_ks > 0.0 or explicit_kp > 0.0:
        if explicit_ks <= 0.0 or explicit_kp <= 0.0:
            return ConstructionCoefficientResult(
                False, 0.0, 0.0, "INCOMPLETE_EXPLICIT_PAIR", "",
                ("ks ve kp birlikte pozitif girilmelidir.",),
            )
        return ConstructionCoefficientResult(
            True,
            explicit_ks,
            explicit_kp,
            "EXPLICIT_TRACEABLE_INPUT",
            "Kullanıcı/üretici tarafından girilmiş ks-kp çifti",
        )

    shape = _normalized(cable.conductor_shape)
    stranding = _normalized(cable.conductor_stranding_type)
    insulation = _normalized(cable.conductor_insulation_system)
    material = _normalized(cable.conductor_material)
    profile = _normalized(cable.milliken_wire_profile)

    if shape not in {"ROUND", "CIRCULAR"}:
        return ConstructionCoefficientResult(
            False, 0.0, 0.0, "UNSUPPORTED_SHAPE", shape,
            ("v0.16.4 yalnız yuvarlak iletken IEC katsayı çözümünü uygular.",),
        )

    is_cu = material in {"CU", "COPPER", "BAKIR"}
    is_al = material in {"AL", "ALUMINIUM", "ALUMINUM", "ALÜMINYUM", "ALUMINYUM"}
    if not (is_cu or is_al):
        return ConstructionCoefficientResult(False, 0.0, 0.0, "UNSUPPORTED_MATERIAL", material)

    if stranding in {"SOLID", "ROUND_SOLID"}:
        return ConstructionCoefficientResult(
            True, 1.0, 1.0, "IEC_60287_1_1_TABLE_2",
            "Yuvarlak masif iletken — standardın konstrüksiyon katsayı çifti (ks = kp = 1)",
        )

    if stranding in {
        "COMPACTED_STRANDED", "COMPACT_ROUND", "ROUND_COMPACTED", "ROUND_STRANDED",
        "STRANDED", "COMPACTED", "CONCENTRIC_STRANDED"
    }:
        if is_al:
            return ConstructionCoefficientResult(
                True, 1.0, 0.8, "IEC_60287_1_1_TABLE_2",
                "Al yuvarlak çok telli — standardın konstrüksiyon katsayı çifti",
            )
        if insulation in {"FLUID", "PAPER", "PPL", "FLUID_PAPER_PPL"}:
            return ConstructionCoefficientResult(
                True, 1.0, 0.8, "IEC_60287_1_1_TABLE_2",
                "Cu yuvarlak çok telli, akışkan/kâğıt/PPL — standardın konstrüksiyon katsayı çifti",
            )
        if insulation in {"EXTRUDED", "MINERAL", "XLPE", "EPR"}:
            return ConstructionCoefficientResult(
                True, 1.0, 1.0, "IEC_60287_1_1_TABLE_2",
                "Cu yuvarlak çok telli, ekstrüde/mineral — standardın konstrüksiyon katsayı çifti",
            )
        return ConstructionCoefficientResult(
            False, 0.0, 0.0, "INSULATION_SYSTEM_REQUIRED", insulation,
            ("Cu yuvarlak çok telli iletken için izolasyon sistemi sınıfı belirtilmelidir.",),
        )

    if stranding in {"MILLIKEN", "ROUND_MILLIKEN"}:
        # IEC 60287-1-1 Table 2 tabulated construction coefficients used by the
        # supported round Milliken cases.  The application implements only the
        # scalar coefficient pairs needed by the equations; it does not ship a
        # reproduction of the standard table, notes, layout or explanatory text.
        if is_al:
            return ConstructionCoefficientResult(
                True, 0.25, 0.15, "IEC_60287_1_1_TABLE_2",
                "Al round Milliken — tabulated construction coefficients",
            )

        if insulation in {"FLUID", "PAPER", "PPL", "FLUID_PAPER_PPL"} and profile in {"", "FLUID_PAPER_PPL"}:
            return ConstructionCoefficientResult(
                True, 0.435, 0.37, "IEC_60287_1_1_TABLE_2",
                "Cu round Milliken, fluid/paper/PPL — tabulated construction coefficients",
            )

        cu_profiles = {
            "INSULATED_WIRES": (0.35, 0.20, "Cu round Milliken, insulated wires, extruded"),
            "BARE_UNIDIRECTIONAL": (0.62, 0.37, "Cu round Milliken, bare uni-directional wires, extruded"),
            "BARE_BIDIRECTIONAL": (0.80, 0.37, "Cu round Milliken, bare bi-directional wires, extruded"),
            "FLUID_PAPER_PPL": (0.435, 0.37, "Cu round Milliken, fluid/paper/PPL"),
        }
        if profile in cu_profiles:
            ks, kp, scope = cu_profiles[profile]
            return ConstructionCoefficientResult(
                True, ks, kp, "IEC_60287_1_1_TABLE_2", scope
            )
        return ConstructionCoefficientResult(
            False, 0.0, 0.0, "MILLIKEN_PROFILE_REQUIRED", profile or "UNKNOWN",
            (
                "Cu Milliken için tel yapısı belirtilmelidir: INSULATED_WIRES, "
                "BARE_UNIDIRECTIONAL, BARE_BIDIRECTIONAL veya FLUID_PAPER_PPL.",
                "Açık kullanıcı ks-kp çifti her zaman bu otomatik çözümün önüne geçer.",
            ),
        )

    return ConstructionCoefficientResult(
        False, 0.0, 0.0, "UNSUPPORTED_STRANDING", stranding or "UNKNOWN",
        ("SEGMENTAL/OTHER/UNKNOWN yapı için doğrulanmış ks-kp çifti gerekir.",),
    )


def skin_effect_factor(xs: float) -> float:
    xs = _positive("xs", xs, allow_zero=True)
    if xs == 0.0:
        return 0.0
    if xs <= 2.8:
        fourth = xs**4
        return fourth / (192.0 + 0.8 * fourth)
    if xs <= 3.8:
        return -0.136 - 0.0177 * xs + 0.0563 * xs**2
    return 0.354 * xs - 0.733


def proximity_effect_factor(xp: float, conductor_diameter_mm: float, spacing_mm: float) -> float:
    xp = _positive("xp", xp, allow_zero=True)
    diameter = _positive("İletken çapı", conductor_diameter_mm)
    spacing = _positive("Faz eksen aralığı", spacing_mm)
    if spacing <= diameter:
        raise PhysicalParameterInputError(
            f"Faz eksen aralığı iletken çapından büyük olmalı: {spacing:.3f} <= {diameter:.3f} mm"
        )
    if xp == 0.0:
        return 0.0
    fourth = xp**4
    fp = fourth / (192.0 + 0.8 * fourth)
    ratio2 = (diameter / spacing) ** 2
    return fp * ratio2 * (0.312 * ratio2 + 1.18 / (fp + 0.27))


def resolve_ac_resistance_at_temperature(
    cable: CableData,
    temperature_c: float,
    *,
    phase_spacing_m: float | None = None,
    allow_legacy_fallback: bool = True,
) -> AcResistanceResolution:
    """Resolve IEC 60287 AC resistance from conductor construction.

    ks/kp are resolved from the declared conductor construction (or an explicit
    traceable pair); ys/yp are then calculated at the requested temperature.
    The historical CableData ys/yp scalars are retained only as a compatibility
    fallback when construction or spacing is unresolved.
    """

    temperature = float(temperature_c)
    if not isfinite(temperature) or temperature < -273.15:
        raise PhysicalParameterInputError(f"İletken sıcaklığı fiziksel olarak geçersiz: {temperature_c}")
    frequency = _positive("Frekans", cable.frequency_hz)
    area = _positive("İletken metal kesiti", cable.conductor_area_mm2)
    rdc20 = float(cable.dc_resistance_20_ohm_km or 0.0)
    rdc_source = "CERTIFIED_OR_PROJECT_INPUT"
    if rdc20 <= 0.0:
        rdc20 = geometry_dc_resistance_20_ohm_km(cable.conductor_material, area)
        rdc_source = "GEOMETRY_DERIVED_PRELIMINARY"
    alpha = resolve_material_alpha_20_per_c(
        cable.conductor_material, cable.temperature_coefficient_20_per_c
    )
    correction = 1.0 + alpha.value_per_c * (temperature - 20.0)
    if not isfinite(correction) or correction <= 0.0:
        raise PhysicalParameterInputError(
            f"Direnç sıcaklık düzeltme katsayısı sıfır veya negatif: {correction}"
        )
    rdc_temperature = rdc20 * correction
    rdc_temperature_ohm_m = rdc_temperature / 1000.0
    coeff = resolve_construction_coefficients(cable)
    spacing = None if phase_spacing_m is None else float(phase_spacing_m)
    trace = [
        f"Rdc20={rdc20:.9f} Ω/km ({rdc_source})",
        f"α20={alpha.value_per_c:.8f} 1/°C ({alpha.source_reference})",
        f"Rdc({temperature:.3f} °C)={rdc_temperature:.9f} Ω/km",
    ]
    if coeff.supported and spacing is not None and spacing > 0.0:
        xs_sq = 8.0 * pi * frequency / rdc_temperature_ohm_m * 1e-7 * coeff.ks
        xp_sq = 8.0 * pi * frequency / rdc_temperature_ohm_m * 1e-7 * coeff.kp
        xs = sqrt(max(0.0, xs_sq))
        xp = sqrt(max(0.0, xp_sq))
        ys = skin_effect_factor(xs)
        yp = proximity_effect_factor(xp, cable.conductor_diameter_mm, spacing * 1000.0)
        rac = rdc_temperature * (1.0 + ys + yp)
        if not isfinite(rac) or rac <= 0.0:
            raise PhysicalParameterInputError(f"Hesaplanan AC direnç geçersiz: {rac}")
        trace.extend((
            f"ks/kp={coeff.ks:.6f}/{coeff.kp:.6f} ({coeff.source}: {coeff.scope})",
            f"xs/xp={xs:.6f}/{xp:.6f}; ys/yp={ys:.8f}/{yp:.8f}",
            f"Faz eksen aralığı={spacing:.6f} m",
            f"Rac={rac:.9f} Ω/km; kaynak=IEC_60287_CONSTRUCTION_RESOLVER",
        ))
        return AcResistanceResolution(
            rdc20, rdc_temperature, rac, alpha.value_per_c, alpha.source_reference,
            coeff.ks, coeff.kp, xs, xp, ys, yp, coeff.source, coeff.scope, spacing, False, tuple(trace)
        )

    reason = (
        "PHASE_SPACING_REQUIRED" if coeff.supported else coeff.source
    )
    detail = (
        "Fiziksel proximity hesabı için pozitif faz eksen aralığı gerekir."
        if coeff.supported else (" ".join(coeff.notes) or coeff.scope or coeff.source)
    )
    if not allow_legacy_fallback:
        raise PhysicalParameterInputError(f"{reason}: {detail}")
    ys = _positive("Legacy ys", cable.skin_effect_factor, allow_zero=True)
    yp = _positive("Legacy yp", cable.proximity_effect_factor, allow_zero=True)
    rac = rdc_temperature * (1.0 + ys + yp)
    if not isfinite(rac) or rac <= 0.0:
        raise PhysicalParameterInputError(f"Hesaplanan legacy AC direnç geçersiz: {rac}")
    trace.extend((
        f"IEC konstrüksiyon çözümü kullanılamadı: {reason}: {detail}",
        f"Legacy ys/yp={ys:.8f}/{yp:.8f}; yalnız uyumluluk fallback'i",
        f"Rac={rac:.9f} Ω/km; kaynak=LEGACY_YS_YP_FALLBACK",
    ))
    return AcResistanceResolution(
        rdc20, rdc_temperature, rac, alpha.value_per_c, alpha.source_reference,
        coeff.ks, coeff.kp, 0.0, 0.0, ys, yp, coeff.source, coeff.scope, spacing, True, tuple(trace)
    )


def _find_insulation_layer(cable: CableData):
    candidates = [
        layer for layer in cable.layers
        if _normalized(layer.layer_type) in {"INSULATION", "MAIN_INSULATION", "XLPE_INSULATION"}
    ]
    return candidates[0] if candidates else None


def geometric_capacitance_uf_km(cable: CableData) -> tuple[float, str]:
    layer = _find_insulation_layer(cable)
    if layer is None:
        raise PhysicalParameterInputError("Katman haritasında ana INSULATION katmanı bulunamadı.")
    d_in = _positive("İzolasyon iç çapı", layer.inner_diameter_mm)
    d_out = _positive("İzolasyon dış çapı", layer.outer_diameter_mm)
    epsilon_r = _positive("Bağıl dielektrik sabiti", layer.relative_permittivity)
    if d_out <= d_in:
        raise PhysicalParameterInputError("İzolasyon dış çapı iç çapından büyük olmalıdır.")
    c_f_m = 2.0 * pi * EPSILON_0_F_M * epsilon_r / log(d_out / d_in)
    return c_f_m * 1e9, f"{layer.name}: εr={epsilon_r:g}, Din/Dout={d_in:g}/{d_out:g} mm"


def dielectric_loss_w_m(cable: CableData, capacitance_uf_km: float) -> float:
    frequency = _positive("Frekans", cable.frequency_hz)
    capacitance_f_m = _positive("Kapasitans", capacitance_uf_km, allow_zero=True) * 1e-9
    tan_delta = _positive("tanδ", cable.dielectric_loss_tan_delta, allow_zero=True)
    phase_voltage_v = _positive("Sistem gerilimi", cable.voltage_kv) * 1000.0 / sqrt(3.0)
    return 2.0 * pi * frequency * capacitance_f_m * phase_voltage_v**2 * tan_delta


def solve_cable_physical_parameters(
    cable: CableData,
    section: RouteSection,
    *,
    target_temperature_c: float | None = None,
    mode: str = "SHADOW_COMPARE",
) -> PhysicalCableParameterResult:
    temperature = float(target_temperature_c if target_temperature_c is not None else cable.max_temperature_c)
    if not isfinite(temperature) or temperature < -273.15:
        raise PhysicalParameterInputError(f"İletken sıcaklığı fiziksel olarak geçersiz: {temperature}")

    issues: list[PhysicalParameterIssue] = []
    trace: list[str] = [
        f"Mod = {mode}",
        f"Referans = {REFERENCE}",
        "v0.16.4 hesapları shadow-mode çalışır; legacy solver girdilerini değiştirmez.",
    ]

    area = _positive("İletken metal kesiti", cable.conductor_area_mm2)
    rdc_geometry = geometry_dc_resistance_20_ohm_km(cable.conductor_material, area)
    rdc_input = max(0.0, float(cable.dc_resistance_20_ohm_km or 0.0))
    if rdc_input > 0.0:
        rdc_basis = rdc_input
        rdc_source = "CERTIFIED_OR_PROJECT_INPUT"
        delta = _percent_difference(rdc_geometry, rdc_input)
        if abs(delta) > 5.0:
            issues.append(PhysicalParameterIssue(
                "WARNING", "RDC_GEOMETRY_MISMATCH", "Rdc20",
                f"Nominal metal alanı tahmini üretici/proje Rdc değerinden %{delta:+.2f} farklı.",
            ))
    else:
        rdc_basis = rdc_geometry
        rdc_source = "GEOMETRY_DERIVED_PRELIMINARY"
        issues.append(PhysicalParameterIssue(
            "WARNING", "RDC_CERTIFIED_VALUE_MISSING", "Rdc20",
            "Üretici/test Rdc20 değeri yok; nominal metal alanından ön hesap kullanıldı.",
        ))
    trace.append(
        f"Rdc20 geometri={rdc_geometry:.9f} Ω/km; giriş={rdc_input:.9f} Ω/km; basis={rdc_basis:.9f} ({rdc_source})"
    )

    alpha_reference = material_alpha_20_per_c(cable.conductor_material)
    alpha_used = _positive(
        "İletken sıcaklık katsayısı", cable.temperature_coefficient_20_per_c, allow_zero=True
    ) or alpha_reference
    alpha_delta = _percent_difference(alpha_used, alpha_reference)
    if abs(alpha_delta) > 2.0:
        issues.append(PhysicalParameterIssue(
            "WARNING", "ALPHA_MATERIAL_MISMATCH", "alpha20",
            f"Girilen α20 malzeme referansından %{alpha_delta:+.2f} farklı.",
        ))
    rdc_temperature = rdc_basis * (1.0 + alpha_used * (temperature - 20.0))
    rdc_temperature_ohm_m = rdc_temperature / 1000.0

    coeff = resolve_construction_coefficients(cable)
    xs = xp = ys = yp = physical_rac = 0.0
    if coeff.supported:
        xs_sq = 8.0 * pi * cable.frequency_hz / rdc_temperature_ohm_m * 1e-7 * coeff.ks
        xp_sq = 8.0 * pi * cable.frequency_hz / rdc_temperature_ohm_m * 1e-7 * coeff.kp
        xs = sqrt(max(0.0, xs_sq))
        xp = sqrt(max(0.0, xp_sq))
        ys = skin_effect_factor(xs)
        yp = proximity_effect_factor(xp, cable.conductor_diameter_mm, section.phase_spacing_m * 1000.0)
        physical_rac = rdc_temperature * (1.0 + ys + yp)
        trace.extend([
            f"ks/kp={coeff.ks:.6f}/{coeff.kp:.6f} ({coeff.scope})",
            f"xs/xp={xs:.6f}/{xp:.6f}",
            f"ys/yp={ys:.8f}/{yp:.8f}",
            f"Rac fiziksel={physical_rac:.9f} Ω/km @ {temperature:.2f} °C",
        ])
    else:
        issues.append(PhysicalParameterIssue(
            "ERROR", coeff.source, "ks/kp",
            " ".join(coeff.notes) or f"İletken yapısı fiziksel katsayı çözümü için desteklenmiyor: {coeff.scope}",
        ))
        trace.append(f"ks/kp çözümü BLOKE: {coeff.source} / {coeff.scope}")

    legacy_ys = _positive("Legacy ys", cable.skin_effect_factor, allow_zero=True)
    legacy_yp = _positive("Legacy yp", cable.proximity_effect_factor, allow_zero=True)
    legacy_rac = rdc_temperature * (1.0 + legacy_ys + legacy_yp)
    rac_delta = _percent_difference(physical_rac, legacy_rac) if coeff.supported else 0.0
    if coeff.supported and abs(rac_delta) > 5.0:
        issues.append(PhysicalParameterIssue(
            "WARNING", "RAC_LEGACY_SHADOW_MISMATCH", "Rac",
            f"Fiziksel Rac, kilitli legacy Rac değerinden %{rac_delta:+.2f} farklı.",
        ))

    capacitance_input = _positive("Kapasitans girdisi", cable.capacitance_uf_km, allow_zero=True)
    capacitance_geometry = 0.0
    capacitance_delta = 0.0
    capacitance_trace = ""
    try:
        capacitance_geometry, capacitance_trace = geometric_capacitance_uf_km(cable)
        capacitance_delta = _percent_difference(capacitance_geometry, capacitance_input)
        if capacitance_input <= 0.0:
            issues.append(PhysicalParameterIssue(
                "WARNING", "CAPACITANCE_CERTIFIED_VALUE_MISSING", "Capacitance",
                "Üretici/test kapasitansı yok; geometrik değer yalnız shadow sonuçtur.",
            ))
        elif abs(capacitance_delta) > 10.0:
            issues.append(PhysicalParameterIssue(
                "WARNING", "CAPACITANCE_GEOMETRY_MISMATCH", "Capacitance",
                f"Geometrik kapasitans giriş değerinden %{capacitance_delta:+.2f} farklı.",
            ))
    except PhysicalParameterInputError as exc:
        issues.append(PhysicalParameterIssue("ERROR", "CAPACITANCE_GEOMETRY_UNAVAILABLE", "Capacitance", str(exc)))
    trace.append(
        f"C giriş/geometri={capacitance_input:.6f}/{capacitance_geometry:.6f} µF/km; {capacitance_trace}"
    )
    wd_input = dielectric_loss_w_m(cable, capacitance_input)
    wd_geometry = dielectric_loss_w_m(cable, capacitance_geometry)

    sheath_input = max(0.0, float(cable.sheath_dc_resistance_20_ohm_km or 0.0))
    sheath_geometry = 0.0
    sheath_basis = sheath_input
    sheath_source = "CERTIFIED_OR_PROJECT_INPUT" if sheath_input > 0.0 else "UNRESOLVED"
    try:
        sheath_geometry = geometry_dc_resistance_20_ohm_km(
            cable.sheath_material, cable.sheath_cross_section_mm2
        )
        if sheath_input <= 0.0:
            sheath_basis = sheath_geometry
            sheath_source = "GEOMETRY_DERIVED_PRELIMINARY"
            issues.append(PhysicalParameterIssue(
                "WARNING", "SHEATH_RDC_CERTIFIED_VALUE_MISSING", "Sheath Rdc20",
                "Üretici/test kılıf direnci yok; metal kesitten ön hesap kullanıldı.",
            ))
        else:
            sheath_delta = _percent_difference(sheath_geometry, sheath_input)
            if abs(sheath_delta) > 5.0:
                issues.append(PhysicalParameterIssue(
                    "WARNING", "SHEATH_RDC_GEOMETRY_MISMATCH", "Sheath Rdc20",
                    f"Kılıf geometri direnci girişten %{sheath_delta:+.2f} farklı.",
                ))
    except PhysicalParameterInputError as exc:
        issues.append(PhysicalParameterIssue("ERROR", "SHEATH_RDC_UNAVAILABLE", "Sheath Rdc20", str(exc)))
    trace.append(
        f"Rsh20 giriş/geometri/basis={sheath_input:.9f}/{sheath_geometry:.9f}/{sheath_basis:.9f} Ω/km ({sheath_source})"
    )

    equivalent_radius = sqrt(area / pi)
    if cable.conductor_gmr_mm > 0.0:
        conductor_gmr = cable.conductor_gmr_mm
        gmr_source = "PROJECT_INPUT"
    else:
        conductor_gmr = 0.7788 * equivalent_radius
        gmr_source = "SOLID_EQUIVALENT_APPROXIMATION"
        if _normalized(cable.conductor_stranding_type) not in {"SOLID", "ROUND_SOLID"}:
            issues.append(PhysicalParameterIssue(
                "WARNING", "GMR_EQUIVALENT_APPROXIMATION", "Conductor GMR",
                "GMR, eşdeğer dolu yuvarlak iletken yaklaşımıdır; üretici/ölçüm değeri tercih edilmelidir.",
            ))
    sheath_gmr = cable.sheath_gmr_mm if cable.sheath_gmr_mm > 0.0 else cable.sheath_mean_diameter_mm / 2.0
    trace.append(
        f"Req/GMRc/GMRsh={equivalent_radius:.6f}/{conductor_gmr:.6f}/{sheath_gmr:.6f} mm; GMRc={gmr_source}"
    )

    t1 = t2 = t3 = 0.0
    try:
        thermal = resolve_internal_thermal_resistance(cable)
        t1, t2, t3 = thermal.t1_km_w, thermal.t2_km_w, thermal.t3_km_w
        trace.extend(thermal.trace)
    except ThermalInputError as exc:
        issues.append(PhysicalParameterIssue("ERROR", "INTERNAL_THERMAL_UNAVAILABLE", "T1-T3", str(exc)))

    final_ready = coeff.supported and not any(issue.severity == "ERROR" for issue in issues)
    if cable.armour_loss_factor != 0.0:
        issues.append(PhysicalParameterIssue(
            "WARNING", "ARMOUR_PHYSICS_NOT_IN_V0164", "Armour",
            "v0.16.4 zırh fiziksel kaybını çözmez; λ2 kilitli legacy katsayı olarak kalır.",
        ))
        final_ready = False

    return PhysicalCableParameterResult(
        cable_id=cable.cable_id,
        cable_name=cable.name,
        route_section_name=section.name,
        mode=mode,
        target_temperature_c=temperature,
        supported_for_ac_resistance=coeff.supported,
        final_design_ready=final_ready,
        rdc20_input_ohm_km=rdc_input,
        rdc20_geometry_ohm_km=rdc_geometry,
        rdc20_basis_ohm_km=rdc_basis,
        rdc20_basis_source=rdc_source,
        material_alpha_reference_per_c=alpha_reference,
        alpha_used_per_c=alpha_used,
        rdc_temperature_ohm_km=rdc_temperature,
        ks=coeff.ks,
        kp=coeff.kp,
        coefficient_source=coeff.source,
        xs=xs,
        xp=xp,
        skin_effect_factor_ys=ys,
        proximity_effect_factor_yp=yp,
        physical_ac_resistance_ohm_km=physical_rac,
        legacy_skin_effect_factor_ys=legacy_ys,
        legacy_proximity_effect_factor_yp=legacy_yp,
        legacy_ac_resistance_ohm_km=legacy_rac,
        ac_resistance_difference_percent=rac_delta,
        capacitance_input_uf_km=capacitance_input,
        capacitance_geometry_uf_km=capacitance_geometry,
        capacitance_difference_percent=capacitance_delta,
        dielectric_loss_input_w_m=wd_input,
        dielectric_loss_geometry_w_m=wd_geometry,
        sheath_resistance_input_ohm_km=sheath_input,
        sheath_resistance_geometry_ohm_km=sheath_geometry,
        sheath_resistance_basis_ohm_km=sheath_basis,
        sheath_resistance_basis_source=sheath_source,
        conductor_equivalent_radius_mm=equivalent_radius,
        conductor_gmr_mm=conductor_gmr,
        sheath_gmr_mm=sheath_gmr,
        t1_km_w=t1,
        t2_km_w=t2,
        t3_km_w=t3,
        issues=issues,
        trace=trace,
        calculated_at=datetime.now().isoformat(timespec="seconds"),
    )


def _resolve_section(project: ProjectData, section_name: str = "") -> RouteSection:
    if section_name:
        for section in project.route_sections:
            if section.name == section_name:
                return section
        raise PhysicalParameterInputError(f"Güzergâh bölümü bulunamadı: {section_name}")
    if not project.route_sections:
        raise PhysicalParameterInputError("Fiziksel parametre karşılaştırması için güzergâh bölümü yok.")
    return project.route_sections[0]


def run_project_physical_parameter_study(
    project: ProjectData,
    *,
    section_name: str = "",
    target_temperature_c: float | None = None,
) -> PhysicalCableParameterResult:
    study = project.physical_parameter_study
    section = _resolve_section(project, section_name or study.selected_route_section_name)
    temperature = (
        float(target_temperature_c)
        if target_temperature_c is not None
        else float(study.target_temperature_c or project.cable.max_temperature_c)
    )
    result = solve_cable_physical_parameters(
        project.cable,
        section,
        target_temperature_c=temperature,
        mode=study.mode,
    )
    study.selected_route_section_name = section.name
    study.target_temperature_c = temperature
    study.last_run_at = result.calculated_at
    if study.persist_last_result:
        study.last_result = result.to_dict()
    return result


def render_physical_parameter_result(result: PhysicalCableParameterResult) -> str:
    state = "HAZIR" if result.final_design_ready else "KOŞULLU/BLOKE"
    lines = [
        "DiTuS v0.16.4 — Kablo Fiziksel Parametre Motoru (SHADOW_COMPARE)",
        f"Kablo: {result.cable_name} [{result.cable_id}]",
        f"Bölüm: {result.route_section_name}",
        f"Hedef sıcaklık: {result.target_temperature_c:.2f} °C",
        f"Fiziksel AC direnç kapsamı: {'DESTEKLENİYOR' if result.supported_for_ac_resistance else 'BLOKE'}",
        f"Nihai fiziksel parametre kapısı: {state}",
        "",
        f"Rdc20 giriş/geometri/basis: {result.rdc20_input_ohm_km:.9f} / "
        f"{result.rdc20_geometry_ohm_km:.9f} / {result.rdc20_basis_ohm_km:.9f} Ω/km",
        f"Rdc({result.target_temperature_c:.1f} °C): {result.rdc_temperature_ohm_km:.9f} Ω/km",
        f"ks/kp: {result.ks:.6f} / {result.kp:.6f} [{result.coefficient_source}]",
        f"xs/xp: {result.xs:.6f} / {result.xp:.6f}",
        f"ys/yp fiziksel: {result.skin_effect_factor_ys:.8f} / {result.proximity_effect_factor_yp:.8f}",
        f"ys/yp legacy: {result.legacy_skin_effect_factor_ys:.8f} / {result.legacy_proximity_effect_factor_yp:.8f}",
        f"Rac fiziksel/legacy: {result.physical_ac_resistance_ohm_km:.9f} / "
        f"{result.legacy_ac_resistance_ohm_km:.9f} Ω/km",
        f"Rac farkı: %{result.ac_resistance_difference_percent:+.3f}",
        f"C giriş/geometri: {result.capacitance_input_uf_km:.6f} / "
        f"{result.capacitance_geometry_uf_km:.6f} µF/km",
        f"Wd giriş/geometri: {result.dielectric_loss_input_w_m:.6f} / "
        f"{result.dielectric_loss_geometry_w_m:.6f} W/m",
        f"Rsh20 giriş/geometri/basis: {result.sheath_resistance_input_ohm_km:.9f} / "
        f"{result.sheath_resistance_geometry_ohm_km:.9f} / "
        f"{result.sheath_resistance_basis_ohm_km:.9f} Ω/km",
        f"Req/GMRc/GMRsh: {result.conductor_equivalent_radius_mm:.6f} / "
        f"{result.conductor_gmr_mm:.6f} / {result.sheath_gmr_mm:.6f} mm",
        f"T1/T2/T3: {result.t1_km_w:.6f} / {result.t2_km_w:.6f} / {result.t3_km_w:.6f} K·m/W",
        "",
        f"Sorunlar: hata={result.error_count}, uyarı={result.warning_count}",
    ]
    lines.extend(
        f"[{issue.severity}] {issue.code} — {issue.parameter}: {issue.message}"
        for issue in result.issues
    )
    lines.extend(["", "Hesap izi:"])
    lines.extend(f"- {item}" for item in result.trace)
    return "\n".join(lines)
