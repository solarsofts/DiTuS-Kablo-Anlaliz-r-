from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
from html import escape
from pathlib import Path
import json
from typing import Iterable

from ucd.calculations.catalog_reference_validation import validate_catalog_reference_rating
from ucd.calculations.cable_selection import (
    CatalogCandidateEvaluation,
    evaluate_catalog_candidates,
)
from ucd.calculations.project_application import (
    ProjectCableApplicationError,
    apply_catalog_candidate_to_project,
    evaluate_application_iteration_gates,
)
from ucd.models.project import CableCatalogRecord, ProjectData

REFERENCE = (
    "DiTuS v0.16.9.4.34 FAZ 6.8 katalog referans-normalizasyon ve fiziksel model karşılaştırma raporu. "
    "Katalog ampacity değerleri yalnız yayımlandıkları referans koşullar için benchmarktır; "
    "karşılaştırma sonucu nihai kablo uygunluk onayı değildir."
)


@dataclass(frozen=True)
class CatalogComparisonCandidate:
    rank: int
    candidate_id: str
    record_id: str
    manufacturer: str
    model: str
    series: str
    conductor_material: str
    conductor_area_mm2: float
    voltage_class: str
    parallel_cables_per_phase: int
    required_design_current_a: float
    reference_ampacity_a_per_cable: float
    combined_reference_ampacity_a: float
    adjusted_reference_ampacity_a: float | None
    normalized_design_margin_a: float | None
    reference_validation_status: str
    governing_reference_region_id: str
    correction_factors_source_verified: bool
    physical_model_ampacity_a: float | None
    physical_minus_catalog_a: float | None
    physical_minus_catalog_percent: float | None
    physical_comparison_status: str
    design_margin_a: float
    design_margin_percent: float
    voltage_drop_percent: float | None
    screening_status: str
    completion_status: str
    iteration_gate_status: str
    verification_status: str
    source_quality: str
    source_page: str
    source_file_hashes: tuple[str, ...]
    catalog_scalar_count: int
    catalog_scalar_missing_count: int
    blocking_missing_count: int
    manufacturer_confirmation_count: int
    assumption_count: int
    reference_condition_summary: str
    missing_or_conditional_items: tuple[str, ...]
    warnings: tuple[str, ...]
    decision_basis: tuple[str, ...]


@dataclass(frozen=True)
class CatalogParameterRow:
    key: str
    label: str
    unit: str
    values: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CatalogComparisonResult:
    generated_at: str
    project_name: str
    project_code: str
    system_voltage_kv: float
    design_current_a: float
    candidates: tuple[CatalogComparisonCandidate, ...]
    parameter_rows: tuple[CatalogParameterRow, ...]
    trace: tuple[str, ...]

    @property
    def recommended_for_further_verification(self) -> CatalogComparisonCandidate | None:
        return self.candidates[0] if self.candidates else None

    def to_dict(self) -> dict:
        return asdict(self)


_SCALAR_FIELDS: tuple[tuple[str, str, str, str], ...] = (
    ("conductor_rdc20_ohm_km", "İletken Rdc @20 °C", "Ω/km", "electrical"),
    ("conductor_rdc90_ohm_km", "İletken Rdc @90 °C", "Ω/km", "electrical"),
    ("inductance_trefoil_mh_km", "Endüktans — üçgen demet", "mH/km", "electrical"),
    ("inductance_flat_mh_km", "Endüktans — düz tertip", "mH/km", "electrical"),
    ("capacitance_uf_km", "Kapasitans", "µF/km", "electrical"),
    ("ampacity_ground_trefoil_a", "Katalog ampacity — toprak/üçgen", "A", "electrical"),
    ("ampacity_ground_flat_a", "Katalog ampacity — toprak/düz", "A", "electrical"),
    ("overall_diameter_mm", "Kablo dış çapı", "mm", "dimensions"),
    ("net_weight_kg_km", "Net ağırlık", "kg/km", "dimensions"),
)


def _record(project: ProjectData, record_id: str) -> CableCatalogRecord:
    record = next((item for item in project.cable_library.records if item.record_id == record_id), None)
    if record is None:
        raise ValueError(f"Katalog kaydı bulunamadı: {record_id}")
    return record


def _format_value(value: object) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Evet" if value else "Hayır"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _catalog_scalar_counts(record: CableCatalogRecord) -> tuple[int, int]:
    present = 0
    missing = 0
    for key, _label, _unit, area in _SCALAR_FIELDS:
        mapping = record.catalog_electrical if area == "electrical" else record.catalog_dimensions
        value = mapping.get(key)
        if isinstance(value, (int, float)) and float(value) != 0.0:
            present += 1
        else:
            missing += 1
    return present, missing


def _source_hashes(record: CableCatalogRecord) -> tuple[str, ...]:
    snapshot = record.cable_snapshot or {}
    sources = snapshot.get("parameter_sources", []) if isinstance(snapshot, dict) else []
    hashes = {
        str(item.get("file_sha256", "")).strip()
        for item in sources
        if isinstance(item, dict) and str(item.get("file_sha256", "")).strip()
    }
    return tuple(sorted(hashes))


def _verification_status(evaluation: CatalogCandidateEvaluation, completion_status: str, gate_status: str) -> str:
    if evaluation.catalog_screening_status == "FAIL":
        return "REJECTED_PRECHECK"
    if evaluation.catalog_screening_status == "NORMALIZED_FAIL":
        return "REFERENCE_BENCHMARK_BELOW_DESIGN"
    if evaluation.catalog_screening_status == "REFERENCE_ONLY":
        return "REFERENCE_NORMALIZATION_REQUIRED"
    if gate_status == "BLOCKED":
        return "BLOCKED_BY_PROJECT_DATA"
    if completion_status == "FINAL_DATA_READY" and gate_status == "READY":
        return "DATA_READY_FOR_FULL_CALCULATION"
    return "CONDITIONAL_VERIFICATION_REQUIRED"


def _ranking_key(item: CatalogComparisonCandidate) -> tuple:
    tier = {
        "DATA_READY_FOR_FULL_CALCULATION": 0,
        "CONDITIONAL_VERIFICATION_REQUIRED": 1,
        "REFERENCE_NORMALIZATION_REQUIRED": 2,
        "REFERENCE_BENCHMARK_BELOW_DESIGN": 3,
        "BLOCKED_BY_PROJECT_DATA": 4,
        "REJECTED_PRECHECK": 5,
    }.get(item.verification_status, 9)
    margin_ratio_distance = abs(item.design_margin_percent - 20.0)
    reference_penalty = 0 if item.adjusted_reference_ampacity_a is not None else 1
    voltage_drop = item.voltage_drop_percent if item.voltage_drop_percent is not None else 999.0
    return (
        tier,
        item.blocking_missing_count,
        item.manufacturer_confirmation_count,
        item.assumption_count,
        item.catalog_scalar_missing_count,
        reference_penalty,
        item.parallel_cables_per_phase,
        margin_ratio_distance,
        voltage_drop,
        item.manufacturer,
        item.model,
    )


def _pick_default_candidates(evaluations: Iterable[CatalogCandidateEvaluation]) -> list[CatalogCandidateEvaluation]:
    # Compare the best parallel-cable variant of each distinct real catalog record.
    picked: dict[str, CatalogCandidateEvaluation] = {}
    for item in evaluations:
        current = picked.get(item.record_id)
        if current is None or (item.catalog_screening_status != "NORMALIZED_PASS", item.score) < (
            current.catalog_screening_status != "NORMALIZED_PASS", current.score
        ):
            picked[item.record_id] = item
    return list(picked.values())


def compare_catalog_candidates(
    project: ProjectData,
    candidate_ids: Iterable[str] | None = None,
    maximum_parallel_cables: int = 2,
    include_draft: bool = False,
    physical_model_ampacity_a: float | None = None,
) -> CatalogComparisonResult:
    wanted = {item for item in (candidate_ids or []) if item}
    comparison_basis = deepcopy(project.design_basis)
    if not wanted:
        # The technical comparison screen intentionally shows all real catalog
        # alternatives, including a different conductor material. The project
        # preference remains a visible warning and is not silently changed.
        comparison_basis.conductor_preference = ""
    selection = evaluate_catalog_candidates(
        project.cable_library,
        comparison_basis,
        maximum_parallel_cables=maximum_parallel_cables,
        include_draft=include_draft,
        project=project,
    )
    if wanted:
        evaluations = [item for item in selection.evaluations if item.candidate_id in wanted]
        unknown = sorted(wanted - {item.candidate_id for item in evaluations})
        if unknown:
            raise ValueError("Karşılaştırma adayı bulunamadı: " + ", ".join(unknown))
    else:
        real_record_ids = {
            record.record_id
            for record in project.cable_library.records
            if "REAL_CATALOG" in {str(tag).upper() for tag in record.tags}
        }
        evaluations = _pick_default_candidates(
            item for item in selection.evaluations if item.record_id in real_record_ids
        )

    candidates: list[CatalogComparisonCandidate] = []
    for evaluation in evaluations:
        record = _record(project, evaluation.record_id)
        cloned = deepcopy(project)
        completion_status = "BLOCKED"
        gate_status = "BLOCKED"
        blocking_count = 0
        manufacturer_count = 0
        assumption_count = 0
        missing_items: tuple[str, ...] = ()
        vdrop = evaluation.voltage_drop_percent
        warnings = list(evaluation.warnings)
        preferred_material = project.design_basis.conductor_preference.strip().upper()
        if preferred_material in {"AL", "CU"} and evaluation.conductor_material.strip().upper() != preferred_material:
            warnings.append(
                f"Aday iletken malzemesi ({evaluation.conductor_material}) proje tercihinden ({preferred_material}) farklıdır."
            )
        basis: list[str] = [
            f"Katalog ön eleme: {evaluation.catalog_screening_status}",
            f"Katalog referans marjı: {evaluation.design_margin_a:+.3f} A",
        ]
        try:
            applied = apply_catalog_candidate_to_project(
                cloned,
                evaluation.record_id,
                evaluation.candidate_id,
                evaluation.parallel_cables_per_phase,
            )
            completion = applied.completion
            gates = evaluate_application_iteration_gates(cloned)
            completion_status = completion.status
            gate_status = gates.status
            blocking_count = completion.blocking_count
            manufacturer_count = completion.manufacturer_confirmation_count
            assumption_count = completion.assumption_count
            missing_items = tuple(
                item.label
                for item in completion.items
                if item.status in {"MISSING", "MANUFACTURER_CONFIRMATION_REQUIRED", "ENGINEERING_ASSUMPTION"}
            )
            if gates.voltage_drop is not None:
                vdrop = gates.voltage_drop.voltage_drop_percent
            basis.append(f"Veri tamamlama: {completion.status}")
            basis.append(f"İterasyon kapıları: {gates.status}")
        except (ProjectCableApplicationError, ValueError) as exc:
            warnings.append(f"Proje uygulama değerlendirmesi tamamlanamadı: {exc}")
            basis.append("Proje uygulama katmanı bloke oldu.")

        applied_match = (
            project.cable.catalog_record_id == evaluation.record_id
            and int(project.cable.parallel_cables_per_phase) == int(evaluation.parallel_cables_per_phase)
        )
        reference_validation = validate_catalog_reference_rating(
            record,
            project,
            reference_ampacity_per_cable_a=evaluation.reference_ampacity_a_per_cable,
            ampacity_key=evaluation.reference_ampacity_key,
            target_parallel_cables_per_phase=evaluation.parallel_cables_per_phase,
            physical_model_ampacity_a=(physical_model_ampacity_a if applied_match else None),
        )
        adjusted = reference_validation.governing_adjusted_ampacity_a
        normalized_margin = None if adjusted is None else adjusted - evaluation.required_design_current_a
        warnings.extend(reference_validation.warnings)
        warnings.extend(
            f"{region.region_name}: eksik düzeltme -> {', '.join(region.missing_parameters)}"
            for region in reference_validation.regions if region.missing_parameters
        )
        basis.append(f"Referans normalizasyonu: {reference_validation.status}")
        if adjusted is not None:
            basis.append(
                f"Normalize katalog benchmarkı: {adjusted:.3f} A; tasarım marjı {normalized_margin:+.3f} A; "
                f"kritik bölge={reference_validation.governing_region_id}."
            )
        for region in reference_validation.regions:
            if region.adjusted_total_ampacity_a is not None:
                basis.append(
                    f"{region.region_name}: k_toplam={region.combined_factor:.6g}; "
                    f"Iref,düzeltilmiş={region.adjusted_total_ampacity_a:.3f} A."
                )
            for factor in region.applied_factors:
                basis.append(
                    f"{region.region_name}/{factor.parameter}: k={factor.factor:.6g}; "
                    f"{factor.source_type}; {factor.source_reference or 'kaynak belirtilmemiş'}."
                )
        if reference_validation.physical_model_ampacity_a is not None:
            basis.append(
                f"Fiziksel model karşılaştırması: {reference_validation.physical_comparison_status}; "
                f"ΔI={reference_validation.physical_minus_catalog_a:+.3f} A "
                f"({reference_validation.physical_minus_catalog_percent:+.3f}%)."
                if reference_validation.physical_minus_catalog_a is not None else
                f"Fiziksel model karşılaştırması: {reference_validation.physical_comparison_status}."
            )
        present, missing = _catalog_scalar_counts(record)
        effective_margin = normalized_margin if normalized_margin is not None else evaluation.design_margin_a
        margin_pct = 100.0 * effective_margin / max(evaluation.required_design_current_a, 1e-12)
        verification = _verification_status(evaluation, completion_status, gate_status)
        candidates.append(CatalogComparisonCandidate(
            rank=0,
            candidate_id=evaluation.candidate_id,
            record_id=evaluation.record_id,
            manufacturer=evaluation.manufacturer,
            model=evaluation.model,
            series=record.series,
            conductor_material=evaluation.conductor_material,
            conductor_area_mm2=evaluation.conductor_area_mm2,
            voltage_class=evaluation.voltage_class,
            parallel_cables_per_phase=evaluation.parallel_cables_per_phase,
            required_design_current_a=evaluation.required_design_current_a,
            reference_ampacity_a_per_cable=evaluation.reference_ampacity_a_per_cable,
            combined_reference_ampacity_a=evaluation.combined_reference_ampacity_a,
            adjusted_reference_ampacity_a=adjusted,
            normalized_design_margin_a=normalized_margin,
            reference_validation_status=reference_validation.status,
            governing_reference_region_id=reference_validation.governing_region_id,
            correction_factors_source_verified=reference_validation.source_verified,
            physical_model_ampacity_a=reference_validation.physical_model_ampacity_a,
            physical_minus_catalog_a=reference_validation.physical_minus_catalog_a,
            physical_minus_catalog_percent=reference_validation.physical_minus_catalog_percent,
            physical_comparison_status=reference_validation.physical_comparison_status,
            design_margin_a=evaluation.design_margin_a,
            design_margin_percent=margin_pct,
            voltage_drop_percent=vdrop,
            screening_status=evaluation.catalog_screening_status,
            completion_status=completion_status,
            iteration_gate_status=gate_status,
            verification_status=verification,
            source_quality=record.source_quality,
            source_page=record.source_page,
            source_file_hashes=_source_hashes(record),
            catalog_scalar_count=present,
            catalog_scalar_missing_count=missing,
            blocking_missing_count=blocking_count,
            manufacturer_confirmation_count=manufacturer_count,
            assumption_count=assumption_count,
            reference_condition_summary=evaluation.reference_condition_summary,
            missing_or_conditional_items=missing_items,
            warnings=tuple(dict.fromkeys(warnings)),
            decision_basis=tuple(basis),
        ))

    candidates.sort(key=_ranking_key)
    ranked = [CatalogComparisonCandidate(**{**asdict(item), "rank": index}) for index, item in enumerate(candidates, 1)]

    rows: list[CatalogParameterRow] = []
    for key, label, unit, area in _SCALAR_FIELDS:
        values = []
        for candidate in ranked:
            record = _record(project, candidate.record_id)
            mapping = record.catalog_electrical if area == "electrical" else record.catalog_dimensions
            values.append((candidate.candidate_id, _format_value(mapping.get(key))))
        rows.append(CatalogParameterRow(key, label, unit, tuple(values)))

    trace = [REFERENCE, *selection.trace]
    trace.append(f"{len(ranked)} farklı katalog kaydı/aday varyantı teknik karşılaştırmaya alındı.")
    if ranked:
        trace.append(
            f"İlk sıra yalnız ileri doğrulama önceliğidir: {ranked[0].manufacturer} {ranked[0].model}; "
            f"durum {ranked[0].verification_status}."
        )
    trace.append("Hiçbir aday 'nihai uygun' olarak etiketlenmedi.")
    return CatalogComparisonResult(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        project_name=project.project_name,
        project_code=project.project_code,
        system_voltage_kv=project.design_basis.system_voltage_kv,
        design_current_a=ranked[0].required_design_current_a if ranked else 0.0,
        candidates=tuple(ranked),
        parameter_rows=tuple(rows),
        trace=tuple(trace),
    )


def render_catalog_comparison_markdown(result: CatalogComparisonResult) -> str:
    lines = [
        "# DiTuS Kablo Katalog Teknik Karşılaştırma Raporu",
        "",
        f"- Proje: **{result.project_name}** ({result.project_code})",
        f"- Sistem: **{result.system_voltage_kv:g} kV**",
        f"- Tasarım akımı: **{result.design_current_a:.3f} A/devre**",
        f"- Üretim: `{result.generated_at}`",
        "",
        "> Bu rapor katalog verilerini, kaynak izlenebilirliğini ve hesap hazırlığını karşılaştırır. Nihai kablo uygunluk onayı değildir.",
        "",
        "## Aday özeti",
        "",
        "| Sıra | Üretici / model | Kablo/faz | Iref aritmetik | Iref normalize | Norm. marj | Ref. durumu | Fizik model | ΔV | Veri | Kapılar | Doğrulama hükmü |",
        "|---:|---|---:|---:|---:|---:|---|---|---:|---|---|---|",
    ]
    for item in result.candidates:
        vdrop = "—" if item.voltage_drop_percent is None else f"%{item.voltage_drop_percent:.5f}"
        lines.append(
            f"| {item.rank} | {item.manufacturer} / {item.model} | {item.parallel_cables_per_phase} | "
            f"{item.combined_reference_ampacity_a:.1f} A | "
            f"{'—' if item.adjusted_reference_ampacity_a is None else f'{item.adjusted_reference_ampacity_a:.1f} A'} | "
            f"{'—' if item.normalized_design_margin_a is None else f'{item.normalized_design_margin_a:+.1f} A'} | "
            f"{item.reference_validation_status} | {item.physical_comparison_status} | {vdrop} | "
            f"{item.completion_status} | {item.iteration_gate_status} | {item.verification_status} |"
        )
    lines.extend(["", "## Katalog parametre matrisi", ""])
    header = "| Parametre | Birim | " + " | ".join(item.manufacturer for item in result.candidates) + " |"
    sep = "|---|---|" + "---|" * len(result.candidates)
    lines.extend([header, sep])
    for row in result.parameter_rows:
        lookup = dict(row.values)
        lines.append(
            f"| {row.label} | {row.unit} | "
            + " | ".join(lookup.get(item.candidate_id, "—") for item in result.candidates)
            + " |"
        )
    for item in result.candidates:
        lines.extend([
            "",
            f"## {item.rank}. {item.manufacturer} — {item.model}",
            "",
            f"- Kaynak seviyesi: `{item.source_quality}`",
            f"- Kaynak sayfası: {item.source_page or 'belirtilmemiş'}",
            f"- Referans koşulu: {item.reference_condition_summary}",
            f"- Referans normalizasyonu: `{item.reference_validation_status}`; kritik bölge `{item.governing_reference_region_id or '—'}`",
            f"- Aritmetik Iref toplamı: {item.combined_reference_ampacity_a:.3f} A (uygunluk rating'i değildir)",
            f"- Normalize katalog benchmarkı: {'—' if item.adjusted_reference_ampacity_a is None else f'{item.adjusted_reference_ampacity_a:.3f} A'}",
            f"- Fiziksel model karşılaştırması: `{item.physical_comparison_status}`" + (
                "" if item.physical_model_ampacity_a is None else f"; fiziksel={item.physical_model_ampacity_a:.3f} A"
            ),
            f"- Katalog skaler kapsamı: {item.catalog_scalar_count} mevcut / {item.catalog_scalar_missing_count} eksik",
            f"- Bloke eksik: {item.blocking_missing_count}; üretici teyidi: {item.manufacturer_confirmation_count}; varsayım: {item.assumption_count}",
            "",
            "### Eksik/koşullu veriler",
            *(f"- {value}" for value in item.missing_or_conditional_items),
            "",
            "### Uyarılar",
            *(f"- {value}" for value in item.warnings),
        ])
    lines.extend(["", "## Hesap izi", "", *(f"- {line}" for line in result.trace), ""])
    return "\n".join(lines)


def render_catalog_comparison_html(result: CatalogComparisonResult) -> str:
    def td(value: object) -> str:
        return f"<td>{escape(_format_value(value))}</td>"

    summary_rows = []
    for item in result.candidates:
        summary_rows.append(
            "<tr>"
            f"<td>{item.rank}</td><td>{escape(item.manufacturer)}</td><td>{escape(item.model)}</td>"
            f"<td>{item.parallel_cables_per_phase}</td><td>{item.combined_reference_ampacity_a:.1f}</td>"
            f"<td>{'—' if item.adjusted_reference_ampacity_a is None else f'{item.adjusted_reference_ampacity_a:.1f}'}</td>"
            f"<td>{'—' if item.normalized_design_margin_a is None else f'{item.normalized_design_margin_a:+.1f}'}</td>"
            f"<td>{escape(item.reference_validation_status)}</td><td>{escape(item.physical_comparison_status)}</td>"
            f"<td>{'—' if item.voltage_drop_percent is None else f'{item.voltage_drop_percent:.5f}%'}</td>"
            f"<td>{escape(item.completion_status)}</td><td>{escape(item.iteration_gate_status)}</td>"
            f"<td>{escape(item.verification_status)}</td></tr>"
        )
    matrix_rows = []
    for row in result.parameter_rows:
        lookup = dict(row.values)
        matrix_rows.append(
            "<tr><th>" + escape(row.label) + "</th><td>" + escape(row.unit) + "</td>" +
            "".join(td(lookup.get(item.candidate_id, "—")) for item in result.candidates) + "</tr>"
        )
    details = []
    for item in result.candidates:
        details.append(
            f"<section><h2>{item.rank}. {escape(item.manufacturer)} — {escape(item.model)}</h2>"
            f"<p><b>Kaynak:</b> {escape(item.source_quality)} · {escape(item.source_page or 'sayfa belirtilmemiş')}</p>"
            f"<p><b>Referans koşulu:</b> {escape(item.reference_condition_summary)}</p>"
            f"<p><b>Referans normalizasyonu:</b> {escape(item.reference_validation_status)} · kritik bölge {escape(item.governing_reference_region_id or '—')} · "
            f"aritmetik Iref {item.combined_reference_ampacity_a:.1f} A · normalize "
            f"{'—' if item.adjusted_reference_ampacity_a is None else f'{item.adjusted_reference_ampacity_a:.1f} A'} · "
            f"fizik model {escape(item.physical_comparison_status)}</p>"
            f"<p><b>Veri kapsamı:</b> {item.catalog_scalar_count} mevcut / {item.catalog_scalar_missing_count} eksik; "
            f"bloke {item.blocking_missing_count}; üretici teyidi {item.manufacturer_confirmation_count}; varsayım {item.assumption_count}</p>"
            "<h3>Eksik/koşullu veriler</h3><ul>" +
            "".join(f"<li>{escape(value)}</li>" for value in item.missing_or_conditional_items) +
            "</ul><h3>Uyarılar</h3><ul>" +
            "".join(f"<li>{escape(value)}</li>" for value in item.warnings) + "</ul></section>"
        )
    candidate_headers = "".join(f"<th>{escape(item.manufacturer)}</th>" for item in result.candidates)
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><title>DiTuS Katalog Teknik Karşılaştırma</title>
<style>
body{{font-family:Arial,sans-serif;margin:28px;color:#1f2933}} h1{{margin-bottom:4px}} .notice{{background:#fff4cc;border-left:5px solid #b38700;padding:12px;margin:16px 0}}
table{{border-collapse:collapse;width:100%;margin:14px 0 24px}} th,td{{border:1px solid #b9c3cc;padding:7px;text-align:left;vertical-align:top}} th{{background:#eaf0f5}} tr:nth-child(even){{background:#f8fafb}}
section{{page-break-inside:avoid;border-top:2px solid #7890a3;margin-top:24px}} code{{background:#eef2f5;padding:2px 4px}}
</style></head><body>
<h1>DiTuS Kablo Katalog Teknik Karşılaştırma Raporu</h1>
<p>{escape(result.project_name)} ({escape(result.project_code)}) · {result.system_voltage_kv:g} kV · Tasarım akımı {result.design_current_a:.3f} A/devre</p>
<div class="notice">Bu rapor nihai uygunluk onayı değildir. Katalog değerleri yalnız yayımlandıkları referans koşullarda benchmark olarak kullanılmıştır.</div>
<h2>Aday özeti</h2><table><thead><tr><th>Sıra</th><th>Üretici</th><th>Model</th><th>Kablo/faz</th><th>Iref aritmetik A</th><th>Iref normalize A</th><th>Norm. marj A</th><th>Ref. durumu</th><th>Fizik model</th><th>ΔV</th><th>Veri</th><th>Kapılar</th><th>Doğrulama</th></tr></thead><tbody>{''.join(summary_rows)}</tbody></table>
<h2>Katalog parametre matrisi</h2><table><thead><tr><th>Parametre</th><th>Birim</th>{candidate_headers}</tr></thead><tbody>{''.join(matrix_rows)}</tbody></table>
{''.join(details)}
<h2>Hesap izi</h2><ul>{''.join(f'<li>{escape(line)}</li>' for line in result.trace)}</ul>
</body></html>"""


def write_catalog_comparison_report(
    result: CatalogComparisonResult,
    output_directory: str | Path,
    base_name: str = "ditus_catalog_comparison",
) -> dict[str, Path]:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / f"{base_name}.json"
    md_path = output / f"{base_name}.md"
    html_path = output / f"{base_name}.html"
    json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_catalog_comparison_markdown(result), encoding="utf-8")
    html_path.write_text(render_catalog_comparison_html(result), encoding="utf-8")
    return {"json": json_path, "markdown": md_path, "html": html_path}
