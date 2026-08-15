from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

from ucd.models.project import (
    DesignBasisData,
    GenericCableCandidate,
    LOAD_MODE_ACTIVE_POWER,
    LOAD_MODE_APPARENT_POWER,
    LOAD_MODE_DIRECT_CURRENT,
    MATURITY_LEVEL_1,
    CABLE_STATUS_DRAFT,
    default_cable_layers,
    default_cable_sources,
)


class FirstDesignInputError(ValueError):
    pass


@dataclass(frozen=True)
class LoadCalculationResult:
    normal_total_current_a: float
    normal_current_per_active_circuit_a: float
    n1_current_per_circuit_a: float
    design_current_per_circuit_a: float
    suggested_voltage_class: str
    trace: tuple[str, ...]


_VOLTAGE_CLASSES = (
    (6.0, "3.6/6 (7.2) kV"),
    (10.0, "6/10 (12) kV"),
    (15.0, "8.7/15 (17.5) kV"),
    (20.0, "12/20 (24) kV"),
    (30.0, "18/30 (36) kV"),
    (35.0, "20.3/35 (40.5) kV"),
    (47.0, "26/45 (52) kV"),
    (69.0, "36/60 (72.5) kV"),
    (110.0, "64/110 (123) kV"),
    (154.0, "87/150 (170) kV"),
    (220.0, "127/220 (245) kV"),
    (400.0, "220/380 (420) kV"),
)

_STANDARD_AREAS = (240, 300, 400, 500, 630, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2500)


def suggest_voltage_class(system_voltage_kv: float, grounding_type: str = "") -> str:
    if system_voltage_kv <= 0:
        raise FirstDesignInputError("Sistem gerilimi pozitif olmalıdır.")
    for threshold, label in _VOLTAGE_CLASSES:
        if system_voltage_kv <= threshold * 1.01:
            return label
    return f"> 220/380 (420) kV — özel üretici/şartname teyidi ({system_voltage_kv:g} kV sistem)"


def calculate_load_basis(basis: DesignBasisData) -> LoadCalculationResult:
    voltage_v = float(basis.system_voltage_kv) * 1000.0
    if voltage_v <= 0:
        raise FirstDesignInputError("Sistem gerilimi pozitif olmalıdır.")
    if basis.circuit_count < 1:
        raise FirstDesignInputError("Devre sayısı en az 1 olmalıdır.")
    if basis.active_circuit_count < 1 or basis.active_circuit_count > basis.circuit_count:
        raise FirstDesignInputError("Aktif devre sayısı 1 ile toplam devre sayısı arasında olmalıdır.")

    mode = basis.load_input_mode.upper()
    trace: list[str] = []
    if mode == LOAD_MODE_ACTIVE_POWER:
        if basis.active_power_mw <= 0:
            raise FirstDesignInputError("Aktif güç pozitif olmalıdır.")
        if not 0 < basis.power_factor <= 1:
            raise FirstDesignInputError("Güç faktörü 0 ile 1 arasında olmalıdır.")
        total_current = basis.active_power_mw * 1e6 / (sqrt(3.0) * voltage_v * basis.power_factor)
        trace.append(
            f"I = P/(sqrt(3)·U·cosφ) = {basis.active_power_mw:g} MW / "
            f"(sqrt(3)·{basis.system_voltage_kv:g} kV·{basis.power_factor:g}) = {total_current:.3f} A"
        )
    elif mode == LOAD_MODE_APPARENT_POWER:
        if basis.apparent_power_mva <= 0:
            raise FirstDesignInputError("Görünür güç pozitif olmalıdır.")
        total_current = basis.apparent_power_mva * 1e6 / (sqrt(3.0) * voltage_v)
        trace.append(
            f"I = S/(sqrt(3)·U) = {basis.apparent_power_mva:g} MVA / "
            f"(sqrt(3)·{basis.system_voltage_kv:g} kV) = {total_current:.3f} A"
        )
    elif mode == LOAD_MODE_DIRECT_CURRENT:
        if basis.direct_current_a <= 0:
            raise FirstDesignInputError("Doğrudan girilen akım pozitif olmalıdır.")
        total_current = basis.direct_current_a
        trace.append(f"Toplam hat akımı kullanıcı girdisi = {total_current:.3f} A")
    else:
        raise FirstDesignInputError(f"Desteklenmeyen yük giriş modu: {basis.load_input_mode}")

    normal_per_circuit = total_current / basis.active_circuit_count
    n1_active = max(1, basis.active_circuit_count - 1) if basis.n_minus_one_enabled else basis.active_circuit_count
    n1_per_circuit = total_current / n1_active
    governing = max(normal_per_circuit, n1_per_circuit)
    growth_factor = 1.0 + max(0.0, basis.future_growth_percent) / 100.0
    margin_factor = 1.0 + max(0.0, basis.design_margin_percent) / 100.0
    design_current = governing * growth_factor * margin_factor
    voltage_class = suggest_voltage_class(basis.system_voltage_kv, basis.grounding_type)

    trace.extend([
        f"Normal devre başı akım = {total_current:.3f}/{basis.active_circuit_count} = {normal_per_circuit:.3f} A",
        f"N-1 devre başı akım = {n1_per_circuit:.3f} A",
        f"Tasarım akımı = max(normal,N-1)·büyüme·marj = {design_current:.3f} A",
        f"İlk gerilim sınıfı önerisi = {voltage_class}; topraklama ve şartname teyidi gereklidir.",
    ])
    return LoadCalculationResult(
        normal_total_current_a=total_current,
        normal_current_per_active_circuit_a=normal_per_circuit,
        n1_current_per_circuit_a=n1_per_circuit,
        design_current_per_circuit_a=design_current,
        suggested_voltage_class=voltage_class,
        trace=tuple(trace),
    )


def apply_load_calculation(basis: DesignBasisData) -> LoadCalculationResult:
    result = calculate_load_basis(basis)
    basis.normal_total_current_a = result.normal_total_current_a
    basis.normal_current_per_active_circuit_a = result.normal_current_per_active_circuit_a
    basis.n1_current_per_circuit_a = result.n1_current_per_circuit_a
    basis.design_current_per_circuit_a = result.design_current_per_circuit_a
    basis.suggested_voltage_class = result.suggested_voltage_class
    return result


def _installation_factor(profile: str) -> float:
    return {
        "DIRECT_BURIED_TREFOIL": 1.00,
        "DIRECT_BURIED_FLAT": 0.96,
        "DUCT_BANK": 0.84,
        "CONCRETE_DUCT": 0.80,
        "TUNNEL": 1.05,
        "MIXED_ROUTE": 0.82,
        "UNKNOWN": 0.78,
    }.get(profile.upper(), 0.80)


def _rho20(material: str) -> float:
    return 0.017241 if material.upper() == "CU" else 0.028264


def _candidate_ampacity(area_mm2: float, material: str, cables_per_phase: int, profile: str) -> float:
    # Maturity-level-1 dimensional screening only.  FAZ 6.8 removed the old
    # unexplained 0.90 parallel derating.  Parallel/grouping correction is not
    # guessed here; the value is an arithmetic screening upper bound and the
    # real project rating must come from IEC 60287/nodal or a sourced catalog
    # correction chain.
    base_density = 0.76 if material.upper() == "CU" else 0.58
    return area_mm2 * base_density * _installation_factor(profile) * cables_per_phase


def _candidate_loss_kw_km(area_mm2: float, material: str, cables_per_phase: int, total_phase_current_a: float) -> float:
    rdc = _rho20(material) / area_mm2 * 1000.0
    rac = rdc * 1.08
    current_each = total_phase_current_a / cables_per_phase
    return 3.0 * cables_per_phase * current_each**2 * rac / 1000.0


def generate_generic_candidates(basis: DesignBasisData, maximum_candidates: int = 5) -> list[GenericCableCandidate]:
    load = apply_load_calculation(basis)
    target = load.design_current_per_circuit_a
    materials = [basis.conductor_preference.upper()] if basis.conductor_preference.upper() in {"CU", "AL"} else ["AL", "CU"]
    cpp_values = [int(basis.cables_per_phase_preference)] if str(basis.cables_per_phase_preference).isdigit() else [1, 2]

    raw: list[GenericCableCandidate] = []
    for material in materials:
        for cpp in cpp_values:
            for area in _STANDARD_AREAS:
                ampacity = _candidate_ampacity(area, material, cpp, basis.installation_profile)
                margin = ampacity - target
                if margin < -0.12 * target:
                    continue
                loss = _candidate_loss_kw_km(area, material, cpp, target)
                score = abs(margin) / max(target, 1.0) + loss / max(30.0, target * 0.03)
                rec_type = "DENGELI_BASLANGIC"
                if loss < 0.75 * max(1.0, target * 0.02):
                    rec_type = "DUSUK_KAYIP"
                if cpp > 1:
                    rec_type = "PARALEL_ALTERNATIF"
                raw.append(GenericCableCandidate(
                    candidate_id=f"GEN-{material}-{area}-{cpp}",
                    label=f"{material} {area} mm² · {cpp} kablo/faz",
                    conductor_material=material,
                    conductor_area_mm2=float(area),
                    cables_per_phase=cpp,
                    voltage_class=load.suggested_voltage_class,
                    estimated_ampacity_a=ampacity,
                    estimated_loss_kw_km=loss,
                    estimated_margin_a=margin,
                    recommendation_type=rec_type,
                    maturity_level=MATURITY_LEVEL_1,
                    status=(
                        "GRUPLAMA_DOGRULAMASI_GEREKLI"
                        if cpp > 1 and margin >= 0
                        else ("ON_ELEME_UYGUN" if margin >= 0 else "SINIRDA")
                    ),
                    notes=[
                        "Jenerik ön eleme; üretici kablosu değildir.",
                        "Ampacity, IEC 60287 güzergâh hesabıyla doğrulanmalıdır.",
                        f"Kurulum profili faktörü: {_installation_factor(basis.installation_profile):.2f}",
                        (
                            "Paralel kablo için grouping/derating uygulanmadı; bu değer aritmetik ön-eleme üst sınırıdır."
                            if cpp > 1 else "Tek kablo/faz ön-eleme tahmini."
                        ),
                        f"Sıralama skoru: {score:.4f}",
                    ],
                ))
                # Keep only the first plausible few areas per combination.
                if margin >= 0.25 * target:
                    break

    def sort_key(c: GenericCableCandidate) -> tuple[float, float, int]:
        undersize_penalty = 1000.0 if c.estimated_margin_a < 0 else 0.0
        relative_margin = abs(c.estimated_margin_a) / max(target, 1.0)
        material_penalty = 0.03 if c.conductor_material == "CU" else 0.0
        parallel_penalty = 0.18 * max(0, c.cables_per_phase - 1)
        return (undersize_penalty + relative_margin + material_penalty + parallel_penalty, c.estimated_loss_kw_km, c.cables_per_phase)

    selected: list[GenericCableCandidate] = []
    seen_types: set[str] = set()
    for candidate in sorted(raw, key=sort_key):
        if candidate.recommendation_type not in seen_types or len(selected) >= 3:
            selected.append(candidate)
            seen_types.add(candidate.recommendation_type)
        if len(selected) >= maximum_candidates:
            break
    if not selected:
        raise FirstDesignInputError("Girilen tasarım akımı için jenerik aday üretilemedi; çoklu kablo/faz veya özel kesit gerekir.")
    basis.candidates = selected
    return selected


def apply_candidate_to_project(candidate: GenericCableCandidate, basis: DesignBasisData, cable: object) -> None:
    cable.conductor_material = candidate.conductor_material
    cable.conductor_area_mm2 = candidate.conductor_area_mm2
    cable.conductors_per_cable = 1
    cable.parallel_cables_per_phase = candidate.cables_per_phase
    cable.design_current_a = basis.design_current_per_circuit_a / max(1, candidate.cables_per_phase)
    cable.voltage_kv = basis.system_voltage_kv
    cable.frequency_hz = basis.frequency_hz
    cable.arrangement = "Trefoil" if "TREFOIL" in basis.installation_profile else "Flat"
    cable.name = f"Jenerik {candidate.label}"
    cable.manufacturer = "JENERİK"
    cable.series = "İlk Tasarım"
    cable.model = candidate.label
    cable.voltage_class = candidate.voltage_class
    cable.catalog_record_id = ""
    cable.snapshot_id = ""
    cable.snapshot_hash = ""
    cable.snapshot_created_at = ""
    cable.data_status = CABLE_STATUS_DRAFT
    cable.layers = default_cable_layers(
        candidate.conductor_material, candidate.conductor_area_mm2,
        105.0 + max(0.0, candidate.conductor_area_mm2 - 1200.0) / 100.0,
    )
    cable.parameter_sources = default_cable_sources()
    cable.validation_notes = [
        "Jenerik L1 aday; üretici konstrüksiyonu ve kaynak doğrulaması bekleniyor."
    ]
    basis.selected_candidate_id = candidate.candidate_id
