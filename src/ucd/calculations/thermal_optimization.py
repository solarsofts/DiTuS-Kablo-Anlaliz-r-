from __future__ import annotations

from ucd.calculations.result_status import is_suitable

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from ucd.calculations.nodal_thermal import (
    NodalRouteStudyResult,
    NodalThermalInputError,
    solve_nodal_region,
)
from ucd.calculations.thermal_review import find_nodal_region_result
from ucd.calculations.thermal_route import resolve_thermal_region
from ucd.models.project import (
    ProjectData,
    THERMAL_INSTALL_DIRECT_BURIED,
    THERMAL_INSTALL_DUCT_BANK,
    THERMAL_INSTALL_HDD,
)


@dataclass(frozen=True)
class ThermalParameterChange:
    key: str
    label: str
    old_value: float
    new_value: float
    unit: str


@dataclass(frozen=True)
class ThermalDesignAlternative:
    alternative_id: str
    title: str
    rationale: str
    scenario_id: str
    region_id: str
    changes: tuple[ThermalParameterChange, ...]
    baseline_ampacity_a: float
    ampacity_a: float
    ampacity_delta_a: float
    ampacity_delta_percent: float
    baseline_temperature_c: float
    maximum_temperature_c: float
    temperature_delta_c: float
    current_margin_a: float
    status: str
    warnings: tuple[str, ...]


def _region_values(project: ProjectData, region_id: str) -> tuple[Any, dict[str, Any]]:
    region = next((item for item in project.thermal_design.regions if item.region_id == region_id), None)
    if region is None:
        raise NodalThermalInputError(f"Termal bölge bulunamadı: {region_id}")
    template = next(
        (item for item in project.thermal_design.templates if item.template_id == region.template_id),
        None,
    )
    if template is None:
        raise NodalThermalInputError(f"Kesit şablonu bulunamadı: {region.template_id}")
    values = dict(vars(template))
    values.update(dict(region.overrides or {}))
    return region, values


def _candidate_specs(project: ProjectData, region_id: str) -> list[tuple[str, str, str, dict[str, float], tuple[tuple[str, str], ...]]]:
    region, values = _region_values(project, region_id)
    profile = resolve_thermal_region(project.thermal_design, region, project.cable)
    installation = profile.installation_type.upper()
    burial = float(values.get("burial_depth_m", profile.burial_depth_m))
    phase_spacing = float(values.get("phase_spacing_m", profile.phase_spacing_m))
    trench_width = float(values.get("trench_width_m", profile.trench_width_m))
    cover_height = float(values.get("cable_cover_height_m", profile.cable_cover_height_m))
    side_width = float(values.get("side_backfill_width_m", profile.side_backfill_width_m))
    native_rho = float(values.get("native_soil_thermal_resistivity_km_w", 0.0) or profile.native_soil.thermal_resistivity_km_w)
    backfill_rho = float(values.get("backfill_thermal_resistivity_km_w", 0.0) or profile.cable_cover.thermal_resistivity_km_w)

    specs: list[tuple[str, str, str, dict[str, float], tuple[tuple[str, str], ...]]] = []
    specs.append((
        "BETTER_NATIVE",
        "Doğal zemin koşulunu iyileştir",
        "Bölgesel zemin iyileştirmesi veya daha güvenilir düşük ısıl özdirençli çevre koşulu.",
        {"native_soil_thermal_resistivity_km_w": max(0.45, native_rho * 0.85)},
        (("native_soil_thermal_resistivity_km_w", "Doğal zemin ısıl özdirenci"),),
    ))
    specs.append((
        "BETTER_BACKFILL",
        "Termal dolgu kalitesini iyileştir",
        "Kablo çevresi dolgusunun ısıl özdirencini düşürerek yakın alan termal direncini azaltır.",
        {"backfill_thermal_resistivity_km_w": max(0.40, backfill_rho * 0.80)},
        (("backfill_thermal_resistivity_km_w", "Termal dolgu ısıl özdirenci"),),
    ))
    specs.append((
        "WIDER_BACKFILL",
        "Termal dolgu hacmini büyüt",
        "Kablo çevresindeki düşük dirençli dolgu kesitini yatay ve düşey yönde genişletir.",
        {
            "trench_width_m": trench_width + 0.30,
            "side_backfill_width_m": side_width + 0.15,
            "cable_cover_height_m": cover_height + 0.15,
        },
        (
            ("trench_width_m", "Hendek genişliği"),
            ("side_backfill_width_m", "Yan dolgu genişliği"),
            ("cable_cover_height_m", "Kablo üstü dolgu yüksekliği"),
        ),
    ))
    specs.append((
        "SHALLOWER",
        "Gömülme derinliğini azalt",
        "Uygulanabilirlik ve mekanik koruma koşulları ayrıca kontrol edilmek üzere kablo eksenini 0,20 m sığlaştırır.",
        {"burial_depth_m": max(0.60, burial - 0.20)},
        (("burial_depth_m", "Kablo eksen derinliği"),),
    ))
    specs.append((
        "PHASE_SPACING",
        "Faz aralığını artır",
        "Faz kabloları arasındaki termal etkileşimi azaltmak için eksen aralığını artırır.",
        {"phase_spacing_m": phase_spacing + 0.05},
        (("phase_spacing_m", "Faz aralığı"),),
    ))

    if installation in {THERMAL_INSTALL_DUCT_BANK, THERMAL_INSTALL_HDD}:
        grout_id = str(values.get("grout_material_id", ""))
        grout = next((item for item in project.thermal_design.materials if item.material_id == grout_id), None)
        grout_rho = float(values.get("grout_thermal_resistivity_km_w", 0.0) or (grout.thermal_resistivity_km_w if grout else 1.0))
        specs.insert(0, (
            "BETTER_GROUT",
            "Grout ısıl özdirencini iyileştir",
            "Duct bank/HDD çevresindeki grout malzemesinin termal performansını yükseltir.",
            {"grout_thermal_resistivity_km_w": max(0.35, grout_rho * 0.80)},
            (("grout_thermal_resistivity_km_w", "Grout ısıl özdirenci"),),
        ))
        duct_inner = float(values.get("duct_inner_diameter_m", 0.13))
        bank_width = float(values.get("duct_bank_width_m", 0.90))
        specs.insert(1, (
            "DUCT_GEOMETRY",
            "Duct ve bank geometrisini rahatlat",
            "Duct iç çapını ve bank genişliğini artırarak kablo çevresindeki ısı yayılım alanını büyütür.",
            {
                "duct_inner_diameter_m": duct_inner * 1.10,
                "duct_bank_width_m": bank_width + 0.15,
            },
            (
                ("duct_inner_diameter_m", "Duct iç çapı"),
                ("duct_bank_width_m", "Duct bank genişliği"),
            ),
        ))
    elif installation == THERMAL_INSTALL_DIRECT_BURIED:
        # Direct buried candidates above are all directly meaningful.
        pass
    return specs


def evaluate_thermal_design_alternatives(
    project: ProjectData,
    study: NodalRouteStudyResult,
    scenario_id: str,
    region_id: str,
    *,
    scope_id: str = "SCENARIO_COMBINED",
    maximum_candidates: int = 6,
) -> tuple[ThermalDesignAlternative, ...]:
    baseline = find_nodal_region_result(study, scenario_id, region_id, scope_id)
    scenario = study.scope_result(scenario_id, scope_id)
    iec_scenario = next(
        (item for item in study.iec_route_result.scenarios if item.scenario_id == scenario_id),
        None,
    )
    iec_region = next(
        (item for item in iec_scenario.regions if item.region_id == region_id),
        None,
    ) if iec_scenario else None
    if baseline is None or scenario is None or iec_region is None:
        raise NodalThermalInputError("Seçili bölge/senaryo için 2D ve IEC referans sonucu bulunamadı.")

    _, original_values = _region_values(project, region_id)
    results: list[ThermalDesignAlternative] = []
    for candidate_id, title, rationale, overrides, labels in _candidate_specs(project, region_id)[:maximum_candidates]:
        candidate_project = deepcopy(project)
        candidate_region = next(
            item for item in candidate_project.thermal_design.regions if item.region_id == region_id
        )
        candidate_region.overrides.update(overrides)
        changes = tuple(
            ThermalParameterChange(
                key,
                label,
                float(original_values.get(key, 0.0) or 0.0),
                float(overrides[key]),
                "K·m/W" if "resistivity" in key else "m",
            )
            for key, label in labels
        )
        try:
            solved = solve_nodal_region(
                candidate_project,
                region_id,
                baseline.design_current_per_cable_a,
                baseline.active_circuit_count,
                baseline.regional_lambda1,
                iec_region.iec,
                scenario_id=scenario_id,
                calculate_ampacity=True,
                energized_circuit_ids=baseline.energized_circuit_ids,
                solution_scope_id=scope_id,
                solution_scope_name=scenario.solution_scope_name,
            )
            delta_a = solved.ampacity_per_cable_a - baseline.ampacity_per_cable_a
            delta_pct = delta_a / max(baseline.ampacity_per_cable_a, 1e-12) * 100.0
            delta_t = solved.maximum_conductor_temperature_c - baseline.maximum_conductor_temperature_c
            warnings = tuple(solved.warnings)
            if delta_a > 0.5 or delta_t < -0.05:
                status = "İYİLEŞME"
            elif delta_a < -0.5 or delta_t > 0.05:
                status = "OLUMSUZ"
            else:
                status = "ETKİ SINIRLI"
            if not is_suitable(solved.status):
                status = "YETERSİZ"
            results.append(ThermalDesignAlternative(
                candidate_id,
                title,
                rationale,
                scenario_id,
                region_id,
                changes,
                baseline.ampacity_per_cable_a,
                solved.ampacity_per_cable_a,
                delta_a,
                delta_pct,
                baseline.maximum_conductor_temperature_c,
                solved.maximum_conductor_temperature_c,
                delta_t,
                solved.ampacity_per_cable_a - solved.design_current_per_cable_a,
                status,
                warnings,
            ))
        except Exception as exc:  # Candidate failure must remain visible, not abort the review.
            results.append(ThermalDesignAlternative(
                candidate_id,
                title,
                rationale,
                scenario_id,
                region_id,
                changes,
                baseline.ampacity_per_cable_a,
                baseline.ampacity_per_cable_a,
                0.0,
                0.0,
                baseline.maximum_conductor_temperature_c,
                baseline.maximum_conductor_temperature_c,
                0.0,
                baseline.ampacity_per_cable_a - baseline.design_current_per_cable_a,
                "HESAPLANAMADI",
                (str(exc),),
            ))
    return tuple(sorted(results, key=lambda item: (-item.ampacity_delta_a, item.title)))


def apply_thermal_design_alternative(project: ProjectData, alternative: ThermalDesignAlternative) -> None:
    region = next(
        (item for item in project.thermal_design.regions if item.region_id == alternative.region_id),
        None,
    )
    if region is None:
        raise NodalThermalInputError(f"Termal bölge bulunamadı: {alternative.region_id}")
    for change in alternative.changes:
        region.overrides[change.key] = change.new_value
    note = f"{alternative.title} ({alternative.alternative_id}) tasarım alternatifi uygulandı."
    region.notes = f"{region.notes}\n{note}".strip()
