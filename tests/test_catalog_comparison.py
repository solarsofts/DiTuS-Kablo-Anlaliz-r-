from __future__ import annotations

import json
from pathlib import Path

from ucd.calculations.catalog_comparison import (
    compare_catalog_candidates,
    render_catalog_comparison_html,
    render_catalog_comparison_markdown,
    write_catalog_comparison_report,
)
from ucd.models.project import ProjectData


ROOT = Path(__file__).resolve().parents[1]


def _project() -> ProjectData:
    raw = json.loads((ROOT / "examples" / "synthetic_20km_line.ucd.json").read_text(encoding="utf-8"))
    return ProjectData.from_dict(raw)


def test_default_comparison_uses_three_synthetic_manufacturer_candidates() -> None:
    result = compare_catalog_candidates(_project())
    assert {item.manufacturer for item in result.candidates} == {"Üretici A", "Üretici B", "Üretici C"}
    assert [item.rank for item in result.candidates] == [1, 2, 3]


def test_comparison_never_labels_candidate_as_final_approved() -> None:
    result = compare_catalog_candidates(_project())
    forbidden = {"FINAL_APPROVED", "APPROVED", "NİHAİ UYGUN"}
    assert all(item.verification_status not in forbidden for item in result.candidates)
    assert "Hiçbir aday 'nihai uygun' olarak etiketlenmedi." in result.trace


def test_project_is_not_mutated_by_comparison() -> None:
    project = _project()
    before = project.to_dict()
    compare_catalog_candidates(project)
    assert project.to_dict() == before


def test_voltage_drop_uses_synthetic_20km_length() -> None:
    result = compare_catalog_candidates(_project())
    candidate = next(item for item in result.candidates if item.manufacturer == "Üretici A")
    assert candidate.voltage_drop_percent is not None
    assert 4.3 < candidate.voltage_drop_percent < 4.5


def test_parameter_matrix_preserves_synthetic_catalog_values() -> None:
    result = compare_catalog_candidates(_project())
    rows = {row.key: row for row in result.parameter_rows}
    rdc = dict(rows["conductor_rdc20_ohm_km"].values)
    a_id = next(item.candidate_id for item in result.candidates if item.manufacturer == "Üretici A")
    c_id = next(item.candidate_id for item in result.candidates if item.manufacturer == "Üretici C")
    assert rdc[a_id] == "0.0778"
    assert rdc[c_id] == "0.047"


def test_reports_include_traceability_and_nonapproval_warning() -> None:
    result = compare_catalog_candidates(_project())
    md = render_catalog_comparison_markdown(result)
    html = render_catalog_comparison_html(result)
    assert "Nihai kablo uygunluk onayı değildir" in md
    assert "Kaynak seviyesi" in md
    assert "nihai uygunluk onayı değildir" in html
    assert "Üretici A" in html and "Üretici B" in html and "Üretici C" in html


def test_report_writer_creates_json_markdown_and_html(tmp_path: Path) -> None:
    result = compare_catalog_candidates(_project())
    paths = write_catalog_comparison_report(result, tmp_path, "comparison")
    assert set(paths) == {"json", "markdown", "html"}
    assert all(path.exists() and path.stat().st_size > 100 for path in paths.values())
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert len(payload["candidates"]) == 3


def test_full_project_reference_normalization_is_route_aware_and_raw_total_is_not_rating() -> None:
    project = _project()
    result = compare_catalog_candidates(project)
    assert all(item.reference_validation_status == "REFERENCE_ONLY_INCOMPLETE" for item in result.candidates)
    assert all(item.adjusted_reference_ampacity_a is None for item in result.candidates)
    assert all(item.screening_status == "REFERENCE_ONLY" for item in result.candidates)
    md = render_catalog_comparison_markdown(result)
    assert "Iref aritmetik" in md
    assert "Iref normalize" in md


def test_applied_matching_candidate_can_compare_normalized_reference_to_physical_model() -> None:
    from ucd.models.project import RouteSection

    project = _project()
    record = next(item for item in project.cable_library.records if item.manufacturer == "Üretici A")
    record.reference_conditions.update({
        "soil_temperature_c": 20.0,
        "burial_depth_m": 0.70,
        "soil_thermal_resistivity_km_w": 1.0,
        "load_factor": 1.0,
        "cables_per_phase": 1,
        "installation_method": "DIRECT_BURIED",
    })
    project.route_sections = [RouteSection(
        "R1", 100.0, section_type="Standart hendek", burial_depth_m=0.70,
        soil_thermal_resistivity_km_w=1.0, ambient_temperature_c=20.0,
        resolved_arrangement="TREFOIL", thermal_region_id="TR1",
    )]
    project.cable.catalog_record_id = record.record_id
    project.cable.parallel_cables_per_phase = 1
    result = compare_catalog_candidates(
        project,
        candidate_ids=[f"{record.record_id}::P1"],
        physical_model_ampacity_a=500.0,
    )
    item = result.candidates[0]
    assert item.adjusted_reference_ampacity_a == 545.0
    assert item.physical_model_ampacity_a == 500.0
    assert item.physical_comparison_status == "PHYSICAL_MODEL_LOWER"
    assert item.physical_minus_catalog_a == -45.0
