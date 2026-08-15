from __future__ import annotations

from ucd.calculations.model_applicability import require_production_physics

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from math import isfinite, pi, sqrt

from ucd.calculations.cable_physical_parameters import (
    MaterialAlphaResolution,
    PhysicalParameterInputError,
    material_resistivity_20_ohm_m as shared_material_resistivity_20_ohm_m,
    resolve_ac_resistance_at_temperature,
    resolve_material_alpha_20_per_c,
)
from ucd.calculations.result_status import STATUS_SUITABLE, STATUS_UNSUITABLE, is_suitable
from ucd.calculations.soil_dryout import (
    IecDryoutRatingResult,
    SoilDryoutInputError,
    SoilDryoutProfile,
    iec_two_zone_ampacity,
    iec_two_zone_temperature_residual,
)
from ucd.calculations.thermal_resistance import ThermalInputError, solve_section_thermal
from ucd.models.project import CableData, RouteSection


STANDARD_REFERENCE = "IEC 60287-1-1:2023 steady-state current-rating equation core"
THERMAL_REFERENCE = "IEC 60287-2-1:2023 thermal-resistance preprocessor (pre-validation)"
VALIDATION_REFERENCE = "CIGRE TB 880:2022 verification cases (validation pending)"


class CalculationInputError(ValueError):
    pass


COMPLETION_COMPLETE = "COMPLETE"
COMPLETION_PARTIAL = "PARTIAL"
COMPLETION_FAILED = "FAILED"
SUITABILITY_SUITABLE = "UYGUN"
SUITABILITY_UNSUITABLE = "UYGUN_DEGIL"
SUITABILITY_INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class Iec60287SectionOutcome:
    section_name: str
    result: "Iec60287SectionResult | None" = None
    error_code: str = ""
    error_message: str = ""
    physical_rejection: bool = False

    @property
    def success(self) -> bool:
        return self.result is not None


@dataclass(frozen=True)
class Iec60287ProjectResult(Sequence["Iec60287SectionResult"]):
    outcomes: tuple[Iec60287SectionOutcome, ...]
    completion_status: str
    suitability_status: str
    status: str

    @property
    def results(self) -> tuple["Iec60287SectionResult", ...]:
        return tuple(item.result for item in self.outcomes if item.result is not None)

    def __iter__(self) -> Iterator["Iec60287SectionResult"]:
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)

    def __getitem__(self, index):
        return self.results[index]


def _display_status(completion: str, suitability: str) -> str:
    if completion == COMPLETION_COMPLETE:
        return STATUS_SUITABLE if suitability == SUITABILITY_SUITABLE else STATUS_UNSUITABLE
    if completion == COMPLETION_PARTIAL:
        return "HESAP EKSİK — UYGUN DEĞİL" if suitability == SUITABILITY_UNSUITABLE else "HESAP EKSİK"
    return "BAŞARISIZ — UYGUN DEĞİL" if suitability == SUITABILITY_UNSUITABLE else "BAŞARISIZ"


def classify_calculation_error(message: str) -> tuple[str, bool]:
    text = str(message)
    if "İzin verilen sıcaklık artışı pozitif değil" in text:
        return "DELTA_THETA_NONPOSITIVE", True
    if "Dielektrik kayıplar tek başına" in text:
        return "DIELECTRIC_LOSS_LIMIT", True
    if "termal kararsızlığa ulaştı" in text:
        return "THERMAL_INSTABILITY", True
    for code in (
        "ANALYTIC_MODEL_SCOPE_REQUIRES_NODAL",
        "ANALYTIC_LAYERED_GEOMETRY_REQUIRES_NODAL",
        "CUSTOM_POSITIONS_REQUIRED",
        "ARRANGEMENT_INSTALLATION_CONFLATION",
        "BONDING_SINGLE_REQUIRES_RETURN_PATH_GEOMETRY",
        "ANALYTIC_DRYOUT_REQUIRES_NODAL",
    ):
        if code in text:
            return code, False
    if "VERTICAL_PHASE_OVERLAP" in text:
        return "VERTICAL_PHASE_OVERLAP", True
    return "CALCULATION_INPUT", False


@dataclass(frozen=True)
class Iec60287SectionResult:
    section_name: str
    ampacity_a: float
    design_current_a: float
    conductor_temperature_at_design_c: float
    temperature_limit_c: float
    ambient_temperature_c: float
    margin_a: float
    ac_resistance_ohm_km: float
    ac_resistance_at_design_ohm_km: float
    dc_resistance_20_ohm_km: float
    dielectric_loss_w_m: float
    conductor_loss_at_design_w_m: float
    sheath_loss_at_design_w_m: float
    armour_loss_at_design_w_m: float
    total_loss_at_design_w_m: float
    t1_km_w: float
    t2_km_w: float
    t3_km_w: float
    t4_km_w: float
    t4_phase_km_w: tuple[float, ...]
    internal_thermal_source: str
    external_thermal_source: str
    sheath_loss_factor: float
    armour_loss_factor: float
    status: str
    notes: tuple[str, ...]
    thermal_trace: tuple[str, ...]

    def trace_lines(self) -> list[str]:
        return [
            f"Bölüm: {self.section_name}",
            f"Standart profili: {STANDARD_REFERENCE}",
            f"Termal profil: {THERMAL_REFERENCE}",
            f"Doğrulama hedefi: {VALIDATION_REFERENCE}",
            f"Rdc20 = {self.dc_resistance_20_ohm_km:.8f} ohm/km",
            f"Rac({self.temperature_limit_c:.1f} °C) = {self.ac_resistance_ohm_km:.8f} ohm/km",
            f"Rac(Tasarım sıcaklığı) = {self.ac_resistance_at_design_ohm_km:.8f} ohm/km",
            f"Wd = {self.dielectric_loss_w_m:.6f} W/m",
            f"T1/T2/T3/T4 = {self.t1_km_w:.6f} / {self.t2_km_w:.6f} / "
            f"{self.t3_km_w:.6f} / {self.t4_km_w:.6f} K.m/W",
            "Faz T4 = " + " / ".join(f"{value:.6f}" for value in self.t4_phase_km_w) + " K.m/W",
            f"İç termal kaynak = {self.internal_thermal_source}",
            f"Dış termal kaynak = {self.external_thermal_source}",
            f"lambda1/lambda2 = {self.sheath_loss_factor:.5f} / {self.armour_loss_factor:.5f}",
            f"Ampacity = {self.ampacity_a:.2f} A",
            f"Tasarım akımında iletken sıcaklığı = {self.conductor_temperature_at_design_c:.2f} °C",
            f"Tasarım akımında toplam kayıp = {self.total_loss_at_design_w_m:.3f} W/m",
            f"Durum = {self.status}",
            "Termal ön işlem izi:",
            *(f"  {line}" for line in self.thermal_trace),
            *(f"Not: {n}" for n in self.notes),
        ]


def _positive(name: str, value: float, allow_zero: bool = False) -> float:
    if (allow_zero and value < 0) or (not allow_zero and value <= 0):
        comparator = "negatif olamaz" if allow_zero else "sıfırdan büyük olmalı"
        raise CalculationInputError(f"{name} {comparator}: {value}")
    return float(value)


def material_resistivity_20_ohm_m(material: str) -> float:
    try:
        return shared_material_resistivity_20_ohm_m(material)
    except PhysicalParameterInputError as exc:
        raise CalculationInputError(str(exc)) from exc


def dc_resistance_20_ohm_km(cable: CableData) -> float:
    if cable.dc_resistance_20_ohm_km > 0:
        return cable.dc_resistance_20_ohm_km
    area_mm2 = _positive("İletken kesiti", cable.conductor_area_mm2)
    rho = material_resistivity_20_ohm_m(cable.conductor_material)
    return rho * 1e9 / area_mm2


def ac_resistance_at_temperature_ohm_km(
    cable: CableData,
    temperature_c: float,
    phase_spacing_m: float | None = None,
    *,
    allow_legacy_fallback: bool = True,
) -> tuple[float, float]:
    """Return Rdc20 and Rac at temperature.

    When a phase spacing is supplied, IEC 60287 ks/kp -> xs/xp -> ys/yp is
    resolved from conductor construction. Calls without geometry retain the
    historical ys/yp path only as an explicit compatibility fallback.
    """
    try:
        resolved = resolve_ac_resistance_at_temperature(
            cable,
            temperature_c,
            phase_spacing_m=phase_spacing_m,
            allow_legacy_fallback=allow_legacy_fallback,
        )
    except PhysicalParameterInputError as exc:
        raise CalculationInputError(str(exc)) from exc
    return resolved.rdc20_ohm_km, resolved.ac_resistance_ohm_km


def ac_resistance_at_limit_ohm_km(
    cable: CableData,
    phase_spacing_m: float | None = None,
    *,
    allow_legacy_fallback: bool = True,
) -> tuple[float, float]:
    return ac_resistance_at_temperature_ohm_km(
        cable,
        cable.max_temperature_c,
        phase_spacing_m,
        allow_legacy_fallback=allow_legacy_fallback,
    )

def dielectric_loss_w_m(cable: CableData) -> float:
    frequency = _positive("Frekans", cable.frequency_hz)
    capacitance_f_m = _positive("Kapasitans", cable.capacitance_uf_km, allow_zero=True) * 1e-9
    tan_delta = _positive("Dielektrik kayıp faktörü", cable.dielectric_loss_tan_delta, allow_zero=True)
    phase_voltage_v = _positive("Sistem gerilimi", cable.voltage_kv) * 1000.0 / sqrt(3.0)
    return 2.0 * pi * frequency * capacitance_f_m * phase_voltage_v**2 * tan_delta


def _section_dryout_profile(section: RouteSection) -> SoilDryoutProfile | None:
    critical = float(getattr(section, "soil_critical_dryout_temperature_c", 0.0) or 0.0)
    dry_rho = float(getattr(section, "soil_dry_state_thermal_resistivity_km_w", 0.0) or 0.0)
    moist_rho = float(getattr(section, "soil_thermal_resistivity_km_w", 0.0) or 0.0)
    if critical <= 0.0 and dry_rho <= 0.0:
        return None
    if critical <= 0.0 or dry_rho <= 0.0:
        raise CalculationInputError("Kuruma modeli için kritik sıcaklık ve kuru-durum ısıl özdirenci birlikte gereklidir.")
    if moist_rho <= 0.0 or dry_rho <= moist_rho:
        raise CalculationInputError("Kuruma modelinde kuru zemin ısıl özdirenci nemli zemin değerinden büyük olmalıdır.")
    return SoilDryoutProfile(
        "ROUTE_NATIVE_SOIL",
        "Route native soil",
        moist_rho,
        dry_rho,
        critical,
        dry_rho / moist_rho,
        str(getattr(section, "soil_dryout_data_state", "")),
        str(getattr(section, "soil_dryout_source_reference", "")),
    )


def solve_section(
    cable: CableData,
    section: RouteSection,
    explicit_positions_m: tuple[tuple[float, float], ...] | None = None,
    *,
    temperature_coefficient_resolution: MaterialAlphaResolution | None = None,
) -> Iec60287SectionResult:
    """Solve the IEC 60287 steady-state rating equation for one cable section.

    v0.3 resolves T1-T3 from equivalent concentric geometry and T4 from a
    homogeneous-soil direct-buried image matrix when automatic modes are used.
    Manual modes preserve the v0.2 traceable-input workflow.
    """

    try:
        require_production_physics(cable, engine_label="IEC 60287")
    except ValueError as exc:
        raise CalculationInputError(str(exc)) from exc

    design_current = _positive("Tasarım akımı", cable.design_current_a, allow_zero=True)
    n = int(cable.conductors_per_cable)
    if n < 1:
        raise CalculationInputError("Kablo başına iletken sayısı en az 1 olmalı.")

    try:
        alpha_resolution = temperature_coefficient_resolution or resolve_material_alpha_20_per_c(
            cable.conductor_material, cable.temperature_coefficient_20_per_c
        )
    except PhysicalParameterInputError as exc:
        raise CalculationInputError(str(exc)) from exc
    effective_cable = replace(
        cable, temperature_coefficient_20_per_c=alpha_resolution.value_per_c
    )

    ambient = float(section.ambient_temperature_c)
    theta_max = float(cable.max_temperature_c)
    delta_theta = theta_max - ambient
    if delta_theta <= 0:
        raise CalculationInputError(
            f"İzin verilen sıcaklık artışı pozitif değil: {theta_max} - {ambient} = {delta_theta} °C"
        )

    try:
        thermal = solve_section_thermal(effective_cable, section, explicit_positions_m)
    except ThermalInputError as exc:
        raise CalculationInputError(str(exc)) from exc

    t1 = thermal.internal.t1_km_w
    t2 = thermal.internal.t2_km_w
    t3 = thermal.internal.t3_km_w
    t4 = thermal.external.effective_t4_km_w
    lambda1 = _positive("Metalik kılıf kayıp faktörü lambda1", effective_cable.sheath_loss_factor, allow_zero=True)
    lambda2 = _positive("Zırh kayıp faktörü lambda2", effective_cable.armour_loss_factor, allow_zero=True)

    try:
        rac_limit = resolve_ac_resistance_at_temperature(
            effective_cable, theta_max, phase_spacing_m=section.phase_spacing_m, allow_legacy_fallback=True
        )
    except PhysicalParameterInputError as exc:
        raise CalculationInputError(str(exc)) from exc
    r20, rac_ohm_km = rac_limit.rdc20_ohm_km, rac_limit.ac_resistance_ohm_km
    rac_ohm_m = rac_ohm_km / 1000.0
    wd = dielectric_loss_w_m(effective_cable)

    thermal_chain = t1 + n * (1.0 + lambda1) * t2 + n * (1.0 + lambda1 + lambda2) * (t3 + t4)
    current_heat_coefficient = rac_ohm_m * thermal_chain
    dielectric_temperature_rise = wd * (0.5 * t1 + n * (t2 + t3 + t4))
    numerator = delta_theta - dielectric_temperature_rise
    if current_heat_coefficient <= 0:
        raise CalculationInputError("Akım kaynaklı ısıl katsayı sıfır veya negatif.")
    if numerator <= 0:
        raise CalculationInputError("Dielektrik kayıplar tek başına izin verilen sıcaklık artışını aşıyor.")

    wet_ampacity = sqrt(numerator / current_heat_coefficient)
    ampacity = wet_ampacity
    dryout_profile = _section_dryout_profile(section)
    dryout_rating: IecDryoutRatingResult | None = None
    dryout_trace: tuple[str, ...] = ()
    if dryout_profile is not None:
        if section.external_thermal_mode.strip().upper() != "AUTO_IMAGE" or len(thermal.external.positions_m) != 1:
            raise CalculationInputError(
                "ANALYTIC_DRYOUT_REQUIRES_NODAL: IEC iki-bölge kuruma denklemi yalnız tek izole "
                "doğrudan gömülü kablo temsilinde uygulanır; çok kablolu/katmanlı geometri için nodal "
                "kritik-izoterm çözümü gereklidir."
            )
        try:
            dryout_rating = iec_two_zone_ampacity(
                delta_theta_c=delta_theta,
                dielectric_loss_w_m=wd,
                t1_km_w=t1,
                t2_km_w=t2,
                t3_km_w=t3,
                t4_moist_km_w=t4,
                ac_resistance_ohm_m=rac_ohm_m,
                conductors_per_cable=n,
                lambda1=lambda1,
                lambda2=lambda2,
                profile=dryout_profile,
                ambient_temperature_c=ambient,
                wet_ampacity_a=wet_ampacity,
            )
        except SoilDryoutInputError as exc:
            raise CalculationInputError(str(exc)) from exc
        ampacity = dryout_rating.ampacity_a
        dryout_trace = dryout_rating.trace

    alpha = alpha_resolution.value_per_c

    # Rac depends on temperature through Rdc(T) and the IEC skin/proximity
    # functions.  First solve the moist-soil operating point.  When a simple
    # IEC dry zone is active at the actual current, solve the two-zone residual
    # with the same temperature-dependent Rac.
    base_temperature = ambient + dielectric_temperature_rise

    def _wet_temperature_residual(value_c: float) -> float:
        try:
            local = resolve_ac_resistance_at_temperature(
                effective_cable, value_c, phase_spacing_m=section.phase_spacing_m, allow_legacy_fallback=True
            )
        except PhysicalParameterInputError as exc:
            raise CalculationInputError(str(exc)) from exc
        predicted = base_temperature + design_current**2 * (local.ac_resistance_ohm_km / 1000.0) * thermal_chain
        return predicted - value_c

    def _solve_temperature_residual(residual, lower_hint: float) -> float:
        lower = max(-273.149999, float(lower_hint))
        f_lower = residual(lower)
        if abs(f_lower) <= 1e-10:
            return lower
        upper = max(theta_max + 200.0, lower + 200.0)
        f_upper = residual(upper)
        growth_steps = 0
        while f_upper > 0.0 and upper < 1000.0 and growth_steps < 8:
            upper = min(1000.0, upper + 150.0)
            f_upper = residual(upper)
            growth_steps += 1
        if f_lower < 0.0:
            return lower
        if f_upper > 0.0:
            raise CalculationInputError("Sıcaklığa bağlı direnç çözümü termal kararsızlığa ulaştı.")
        lo, hi = lower, upper
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            f_mid = residual(mid)
            if abs(f_mid) <= 1e-9 or hi - lo <= 1e-7:
                return mid
            if f_mid > 0.0:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    wet_design_temperature = _solve_temperature_residual(
        _wet_temperature_residual, max(-273.149999, min(base_temperature, theta_max))
    )
    design_temperature = wet_design_temperature

    if dryout_profile is not None:
        try:
            wet_design_rac = resolve_ac_resistance_at_temperature(
                effective_cable, wet_design_temperature,
                phase_spacing_m=section.phase_spacing_m, allow_legacy_fallback=True,
            )
        except PhysicalParameterInputError as exc:
            raise CalculationInputError(str(exc)) from exc
        wet_external_heat = (
            design_current**2 * (wet_design_rac.ac_resistance_ohm_km / 1000.0) * n * (1.0 + lambda1 + lambda2)
            + wd * n
        )
        wet_interface_temperature = ambient + wet_external_heat * t4
        if wet_interface_temperature > dryout_profile.critical_temperature_c + 1e-9:
            def _dry_temperature_residual(value_c: float) -> float:
                try:
                    local = resolve_ac_resistance_at_temperature(
                        effective_cable, value_c, phase_spacing_m=section.phase_spacing_m, allow_legacy_fallback=True
                    )
                except PhysicalParameterInputError as exc:
                    raise CalculationInputError(str(exc)) from exc
                try:
                    return iec_two_zone_temperature_residual(
                        value_c,
                        ambient_temperature_c=ambient,
                        current_a=design_current,
                        ac_resistance_ohm_m=local.ac_resistance_ohm_km / 1000.0,
                        dielectric_loss_w_m=wd,
                        t1_km_w=t1, t2_km_w=t2, t3_km_w=t3, t4_moist_km_w=t4,
                        conductors_per_cable=n, lambda1=lambda1, lambda2=lambda2,
                        profile=dryout_profile,
                    )
                except SoilDryoutInputError as exc:
                    raise CalculationInputError(str(exc)) from exc
            design_temperature = _solve_temperature_residual(
                _dry_temperature_residual, max(ambient, dryout_profile.critical_temperature_c)
            )
            dryout_trace = dryout_trace + (
                f"Tasarım akımında nemli-model kablo/zemin ara yüzü={wet_interface_temperature:.3f} °C > "
                f"kritik={dryout_profile.critical_temperature_c:.3f} °C; iki-bölge sıcaklık çözümü etkin.",
            )
        else:
            dryout_trace = dryout_trace + (
                f"Tasarım akımında kablo/zemin ara yüzü={wet_interface_temperature:.3f} °C <= "
                f"kritik={dryout_profile.critical_temperature_c:.3f} °C; kuruma etkin değil.",
            )

    try:
        rac_design = resolve_ac_resistance_at_temperature(
            effective_cable, design_temperature, phase_spacing_m=section.phase_spacing_m, allow_legacy_fallback=True
        )
    except PhysicalParameterInputError as exc:
        raise CalculationInputError(str(exc)) from exc
    rac_design_ohm_km = rac_design.ac_resistance_ohm_km
    rac_design_ohm_m = rac_design_ohm_km / 1000.0

    conductor_loss = design_current**2 * rac_design_ohm_m
    sheath_loss = conductor_loss * lambda1
    armour_loss = conductor_loss * lambda2
    total_loss = conductor_loss + sheath_loss + armour_loss + wd

    notes: list[str] = [
        "Skin/proximity faktörleri IEC konstrüksiyon ks/kp çözümünden sıcaklığa bağlı hesaplanır; çözülemeyen legacy yapı açık fallback olarak izlenir.",
        "Metalik kılıf kayıp faktörü lambda1 bu legacy bölüm çözücüsünde skaler girdidir; üretim kapalı çevriminde fiziksel bonding kaybından türetilir.",
    ]
    if rac_limit.used_legacy_fallback or rac_design.used_legacy_fallback:
        notes.append("AC direnç konstrüksiyon bilgisi eksik olduğu için legacy ys/yp fallback kullandı; nihai tasarım için ks/kp yapı kaynağı doğrulanmalıdır.")
    if cable.dc_resistance_20_ohm_km <= 0:
        notes.append("Rdc20 malzeme özdirenci ve nominal kesitten türetildi; üretici değeri tercih edilmelidir.")
    if dryout_profile is not None:
        notes.append(
            "Toprak kuruma modeli etkin: kritik izoterm ve kuru-durum ρ kullanıcı/proje malzeme verisinden alınır; "
            "çok kablolu geometri için nodal kritik-izoterm çözümü zorunludur."
        )
    if section.external_thermal_mode.strip().upper() == "AUTO_IMAGE" and section.section_type.lower() not in {
        "standart hendek", "direct buried", "doğrudan gömülü", "dogrudan gomulu"
    }:
        notes.append("AUTO_IMAGE özel geçiş geometrisini temsil etmez; bölüm tipi için manuel veya nodal T4 kullanın.")
    notes.append("T1-T4 hesapları CIGRE TB 880 referans vakalarıyla henüz regresyon doğrulamasından geçmedi.")

    status = "UYGUN" if design_current <= ampacity and design_temperature <= theta_max else "UYGUN DEĞİL"
    return Iec60287SectionResult(
        section_name=section.name,
        ampacity_a=ampacity,
        design_current_a=design_current,
        conductor_temperature_at_design_c=design_temperature,
        temperature_limit_c=theta_max,
        ambient_temperature_c=ambient,
        margin_a=ampacity - design_current,
        ac_resistance_ohm_km=rac_ohm_km,
        ac_resistance_at_design_ohm_km=rac_design_ohm_km,
        dc_resistance_20_ohm_km=r20,
        dielectric_loss_w_m=wd,
        conductor_loss_at_design_w_m=conductor_loss,
        sheath_loss_at_design_w_m=sheath_loss,
        armour_loss_at_design_w_m=armour_loss,
        total_loss_at_design_w_m=total_loss,
        t1_km_w=t1,
        t2_km_w=t2,
        t3_km_w=t3,
        t4_km_w=t4,
        t4_phase_km_w=thermal.external.phase_t4_km_w,
        internal_thermal_source=thermal.internal.source,
        external_thermal_source=thermal.external.source,
        sheath_loss_factor=lambda1,
        armour_loss_factor=lambda2,
        status=status,
        notes=tuple(notes),
        thermal_trace=thermal.internal.trace + thermal.external.trace + dryout_trace + (
            "AC direnç @ sıcaklık limiti:",
            *(f"  {line}" for line in rac_limit.trace),
            "AC direnç @ tasarım çalışma noktası:",
            *(f"  {line}" for line in rac_design.trace),
            f"Rdc20, {design_temperature:.3f} °C iletken sıcaklığına düzeltildi: "
            f"alpha20={alpha:.6f} 1/°C, katsayı={1.0 + alpha * (design_temperature - 20.0):.6f}, "
            f"kaynak={alpha_resolution.source_reference}.",
        ) + ((
            f"Saklanan {cable.temperature_coefficient_20_per_c:.6f} değeri tarihsel CableData "
            f"varsayılanıdır; {cable.conductor_material} malzeme profili kullanıldı.",
        ) if alpha_resolution.migrated_legacy_default else ()),
    )


def validate_common_cable_inputs(cable: CableData) -> None:
    """Fail fast only for inputs shared by every route section/scenario."""
    _positive("Tasarım akımı", cable.design_current_a, allow_zero=True)
    if int(cable.conductors_per_cable) < 1:
        raise CalculationInputError("Kablo başına iletken sayısı en az 1 olmalı.")
    dc_resistance_20_ohm_km(cable)
    try:
        resolve_material_alpha_20_per_c(
            cable.conductor_material, cable.temperature_coefficient_20_per_c
        )
    except PhysicalParameterInputError as exc:
        raise CalculationInputError(str(exc)) from exc
    dielectric_loss_w_m(cable)


def solve_project(cable: CableData, sections: list[RouteSection]) -> Iec60287ProjectResult:
    """Solve legacy/headless route sections with section-level error isolation."""
    if not sections:
        raise CalculationInputError("Hesaplanacak güzergâh bölümü yok.")
    validate_common_cable_inputs(cable)

    outcomes: list[Iec60287SectionOutcome] = []
    for section in sections:
        try:
            result = solve_section(cable, section)
        except CalculationInputError as exc:
            code, physical = classify_calculation_error(str(exc))
            outcomes.append(Iec60287SectionOutcome(
                section.name, None, code, str(exc), physical
            ))
        else:
            outcomes.append(Iec60287SectionOutcome(section.name, result))

    successes = tuple(item.result for item in outcomes if item.result is not None)
    if len(successes) == len(outcomes):
        completion = COMPLETION_COMPLETE
    elif successes:
        completion = COMPLETION_PARTIAL
    else:
        completion = COMPLETION_FAILED
    definitely_unsuitable = any(
        not is_suitable(item.status) for item in successes
    ) or any(item.physical_rejection for item in outcomes)
    if definitely_unsuitable:
        suitability = SUITABILITY_UNSUITABLE
    elif completion == COMPLETION_COMPLETE:
        suitability = SUITABILITY_SUITABLE
    else:
        suitability = SUITABILITY_INDETERMINATE
    return Iec60287ProjectResult(
        tuple(outcomes), completion, suitability, _display_status(completion, suitability)
    )

