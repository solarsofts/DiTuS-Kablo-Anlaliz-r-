from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
import re
from typing import Any

from ucd.calculations.cable_library import cable_from_dict, validate_cable
from ucd.calculations.catalog_reference_validation import validate_catalog_reference_rating
from ucd.calculations.first_design import apply_load_calculation
from ucd.models.project import CableCatalogRecord, CableLibraryData, DesignBasisData, ProjectData


REFERENCE = (
    "DiTuS v0.16.9.4.34 FAZ 6.8 catalog reference-condition screening. Catalog current ratings are used only "
    "under their stated reference conditions; final design requires project IEC 60287, "
    "2D thermal, bonding and fault validation."
)


@dataclass(frozen=True)
class CatalogCandidateEvaluation:
    candidate_id: str
    record_id: str
    manufacturer: str
    model: str
    voltage_class: str
    conductor_material: str
    conductor_area_mm2: float
    parallel_cables_per_phase: int
    voltage_compatible: bool
    reference_ampacity_a_per_cable: float
    reference_ampacity_key: str
    combined_reference_ampacity_a: float
    adjusted_reference_ampacity_a: float | None
    reference_validation_status: str
    governing_reference_region_id: str
    correction_factors_source_verified: bool
    required_normal_current_a: float
    required_n1_current_a: float
    required_design_current_a: float
    design_margin_a: float
    normalized_design_margin_a: float | None
    voltage_drop_percent: float | None
    catalog_screening_status: str
    data_readiness: str
    source_quality: str
    score: float
    reference_condition_summary: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class CatalogSelectionResult:
    evaluations: tuple[CatalogCandidateEvaluation, ...]
    trace: tuple[str, ...]

    @property
    def recommended(self) -> CatalogCandidateEvaluation | None:
        return next(
            (item for item in self.evaluations if item.catalog_screening_status == "NORMALIZED_PASS"),
            self.evaluations[0] if self.evaluations else None,
        )


def _numbers(text: str) -> list[float]:
    return [float(item.replace(",", ".")) for item in re.findall(r"\d+(?:[.,]\d+)?", text)]


def voltage_class_compatible(system_voltage_kv: float, voltage_class: str) -> bool:
    values = _numbers(voltage_class)
    if not values or system_voltage_kv <= 0:
        return False
    # U0/U(Um) forms can include three values. System labels such as 154 kV
    # commonly pair with 87/150 (170) kV cable class, while a 36 kV nominal
    # system must not be accepted against 18/30 (36) merely because Um=36 kV.
    # The 15% band around rated U covers established nominal-system naming
    # without treating Um itself as the continuous system voltage.
    rated_u = values[1] if len(values) >= 2 else values[0]
    tolerance = 1.15 if len(values) >= 3 else 1.01
    return system_voltage_kv <= rated_u * tolerance + 1e-9


def _get_number(mapping: dict[str, Any], *keys: str) -> float:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


def reference_ampacity_details(record: CableCatalogRecord, installation_profile: str) -> tuple[float, str, str]:
    data = record.catalog_electrical
    profile = installation_profile.upper()
    if "TREFOIL" in profile:
        for key in ("ampacity_ground_trefoil_a", "ampacity_ground_a"):
            value = _get_number(data, key)
            if value > 0:
                return value, "toprakta üçgen demet", key
        return 0.0, "toprakta üçgen demet", "ampacity_ground_trefoil_a"
    if "FLAT" in profile:
        for key in ("ampacity_ground_flat_a", "ampacity_ground_a"):
            value = _get_number(data, key)
            if value > 0:
                return value, "toprakta düz/yan yana", key
        return 0.0, "toprakta düz/yan yana", "ampacity_ground_flat_a"
    if "DUCT" in profile or "HDD" in profile:
        for key in ("ampacity_ground_trefoil_a", "ampacity_ground_a", "ampacity_ground_flat_a"):
            value = _get_number(data, key)
            if value > 0:
                return value, "toprak referansı (duct/HDD için yalnız benchmark)", key
        return 0.0, "toprak referansı (duct/HDD için yalnız benchmark)", "ampacity_ground_a"
    for key in ("ampacity_ground_trefoil_a", "ampacity_ground_a", "ampacity_ground_flat_a"):
        value = _get_number(data, key)
        if value > 0:
            return value, "toprak referansı", key
    return 0.0, "toprak referansı", "ampacity_ground_a"


def reference_ampacity(record: CableCatalogRecord, installation_profile: str) -> tuple[float, str]:
    value, label, _key = reference_ampacity_details(record, installation_profile)
    return value, label


def _reference_summary(record: CableCatalogRecord, ampacity_label: str) -> str:
    conditions = record.reference_conditions
    parts = [ampacity_label]
    for key, label, suffix in (
        ("soil_temperature_c", "toprak", "°C"),
        ("burial_depth_m", "derinlik", " m"),
        ("soil_thermal_resistivity_km_w", "ρth", " K·m/W"),
        ("load_factor", "katalog yük faktörü", ""),
    ):
        value = conditions.get(key)
        if isinstance(value, (int, float)):
            parts.append(f"{label} {value:g}{suffix}")
    if conditions.get("arrangement_note"):
        parts.append(str(conditions["arrangement_note"]))
    if len(parts) == 1:
        parts.append("referans koşulları katalogda tam tanımlı değil")
    return "; ".join(parts)


def _voltage_drop_percent(
    record: CableCatalogRecord,
    basis: DesignBasisData,
    current_a: float,
    parallel_count: int,
) -> float | None:
    data = record.catalog_electrical
    resistance = _get_number(data, "conductor_rac90_ohm_km", "conductor_rdc90_ohm_km")
    if resistance <= 0:
        resistance = _get_number(data, "conductor_rdc20_ohm_km")
    profile = basis.installation_profile.upper()
    inductance = (
        _get_number(data, "inductance_trefoil_mh_km", "inductance_mh_km")
        if "TREFOIL" in profile
        else _get_number(data, "inductance_flat_mh_km", "inductance_mh_km")
    )
    if resistance <= 0 or inductance <= 0 or basis.system_voltage_kv <= 0 or basis.total_route_length_m <= 0:
        return None
    pf = basis.power_factor if 0 < basis.power_factor <= 1 else 1.0
    sin_phi = sqrt(max(0.0, 1.0 - pf * pf))
    x_ohm_km = 2.0 * pi * basis.frequency_hz * inductance / 1000.0
    current_each = current_a / max(1, parallel_count)
    length_km = basis.total_route_length_m / 1000.0
    drop_v = sqrt(3.0) * current_each * length_km * (resistance * pf + x_ohm_km * sin_phi)
    return 100.0 * drop_v / (basis.system_voltage_kv * 1000.0)


def evaluate_catalog_candidates(
    library: CableLibraryData,
    basis: DesignBasisData,
    maximum_parallel_cables: int = 2,
    include_draft: bool = False,
    project: ProjectData | None = None,
) -> CatalogSelectionResult:
    load = apply_load_calculation(basis)
    evaluations: list[CatalogCandidateEvaluation] = []
    trace = [
        REFERENCE,
        f"Sistem: {basis.system_voltage_kv:g} kV; normal {load.normal_current_per_active_circuit_a:.3f} A/devre; "
        f"N-1 {load.n1_current_per_circuit_a:.3f} A/devre; tasarım {load.design_current_per_circuit_a:.3f} A/devre.",
    ]
    preferred_material = basis.conductor_preference.strip().upper()
    for record in library.records:
        if record.manufacturer.upper() in {"JENERİK", "GENERIC"} and not include_draft:
            continue
        if preferred_material in {"AL", "CU"} and record.conductor_material.strip().upper() != preferred_material:
            continue
        if record.status.upper() == "DRAFT" and not include_draft:
            continue
        voltage_ok = voltage_class_compatible(basis.system_voltage_kv, record.voltage_class)
        ampacity, ampacity_label, ampacity_key = reference_ampacity_details(record, basis.installation_profile)
        for parallel in range(1, max(1, maximum_parallel_cables) + 1):
            combined = ampacity * parallel if ampacity > 0 else 0.0
            margin = combined - load.design_current_per_circuit_a
            normalization_project = project or type(
                "_CatalogScreenProject", (), {"route_sections": [], "design_basis": basis}
            )()
            normalization = validate_catalog_reference_rating(
                record,
                project=normalization_project,
                reference_ampacity_per_cable_a=ampacity,
                ampacity_key=ampacity_key,
                target_parallel_cables_per_phase=parallel,
            )
            # The lightweight selection path has only the design-basis target. The
            # full project comparison below re-runs the same validator against every
            # physical route section.
            adjusted = normalization.governing_adjusted_ampacity_a
            normalized_margin = None if adjusted is None else adjusted - load.design_current_per_circuit_a
            warnings: list[str] = list(normalization.warnings)
            if not voltage_ok:
                warnings.append("Gerilim sınıfı sistem gerilimiyle uyumlu değil.")
            if ampacity <= 0:
                warnings.append("Seçilen kurulum için katalog ampacity değeri yok.")
            elif "DUCT" in basis.installation_profile.upper() or "HDD" in basis.installation_profile.upper():
                warnings.append("Duct/HDD için toprak ampacity değeri yalnız ön benchmark olarak kullanıldı.")

            readiness = "MISSING"
            if record.cable_snapshot:
                report = validate_cable(cable_from_dict(record.cable_snapshot))
                readiness = report.status
                if report.status != "VERIFIED":
                    warnings.append("Konstrüksiyon/model verisi koşullu; üretici çizimi veya test verisi gerekiyor.")
            else:
                warnings.append("Parametrik kablo konstrüksiyon kaydı bulunmuyor.")

            if not voltage_ok or ampacity <= 0:
                status = "FAIL"
            elif adjusted is None:
                status = "REFERENCE_ONLY"
                warnings.append("Katalog Iref proje koşullarına kaynaklı faktörlerle normalize edilmedi; ham ×N değeri uygunluk kapısı değildir.")
            elif normalized_margin is not None and normalized_margin < 0:
                status = "NORMALIZED_FAIL"
                warnings.append("Normalize katalog benchmarkı tasarım akımının altında; nihai hüküm yine fiziksel proje hesabından verilir.")
            else:
                status = "NORMALIZED_PASS"
                warnings.append("Normalize katalog sonucu yalnız benchmarktır; nihai uygunluk fiziksel IEC/nodal proje hesabıdır.")

            voltage_drop = _voltage_drop_percent(
                record, basis, load.design_current_per_circuit_a, parallel
            )
            score_margin = normalized_margin if normalized_margin is not None else margin
            margin_ratio = score_margin / max(load.design_current_per_circuit_a, 1.0)
            score = 0.0
            if not voltage_ok:
                score += 10000.0
            if ampacity <= 0:
                score += 5000.0
            if normalized_margin is None:
                score += 500.0
            if score_margin < 0:
                score += 2000.0 + abs(margin_ratio) * 100.0
            else:
                # Prefer a practical positive margin, not the largest cable.
                score += abs(margin_ratio - 0.20) * 10.0
            score += 1.5 * (parallel - 1)
            if readiness != "VERIFIED":
                score += 2.0
            if record.source_quality == "CATALOG_ONLY":
                score += 1.0
            if voltage_drop is not None:
                score += min(voltage_drop, 10.0) * 0.05

            evaluations.append(CatalogCandidateEvaluation(
                candidate_id=f"{record.record_id}::P{parallel}",
                record_id=record.record_id,
                manufacturer=record.manufacturer,
                model=record.model,
                voltage_class=record.voltage_class,
                conductor_material=record.conductor_material,
                conductor_area_mm2=record.conductor_area_mm2,
                parallel_cables_per_phase=parallel,
                voltage_compatible=voltage_ok,
                reference_ampacity_a_per_cable=ampacity,
                reference_ampacity_key=ampacity_key,
                combined_reference_ampacity_a=combined,
                adjusted_reference_ampacity_a=adjusted,
                reference_validation_status=normalization.status,
                governing_reference_region_id=normalization.governing_region_id,
                correction_factors_source_verified=normalization.source_verified,
                required_normal_current_a=load.normal_current_per_active_circuit_a,
                required_n1_current_a=load.n1_current_per_circuit_a,
                required_design_current_a=load.design_current_per_circuit_a,
                design_margin_a=margin,
                normalized_design_margin_a=normalized_margin,
                voltage_drop_percent=voltage_drop,
                catalog_screening_status=status,
                data_readiness=readiness,
                source_quality=record.source_quality,
                score=score,
                reference_condition_summary=_reference_summary(record, ampacity_label),
                warnings=tuple(warnings),
            ))

    evaluations.sort(key=lambda item: (item.catalog_screening_status != "NORMALIZED_PASS", item.score, item.manufacturer, item.model))
    trace.append(f"{len(evaluations)} katalog/parallel varyantı değerlendirildi.")
    trace.append("Katalog ampacity değerleri proje güzergâhı için doğrudan nihai rating kabul edilmedi.")
    return CatalogSelectionResult(tuple(evaluations), tuple(trace))
