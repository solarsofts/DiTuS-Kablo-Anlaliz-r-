from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from ucd.calculations import solve_bonding, solve_project
from ucd.calculations.reporting import (
    MODULE_BONDING,
    MODULE_IEC60287,
    MODULE_PROJECT,
    MODULE_WARNINGS,
    REPORT_CALCULATION,
    REPORT_DESIGN,
    CalculationResultsBundle,
    ReportConfiguration,
    ReportMetadata,
    build_project_report,
    render_project_report_html,
    render_project_report_markdown,
    write_project_report,
)
from ucd.models.project import ProjectData


ROOT = Path(__file__).resolve().parents[1]


def _sample_project() -> ProjectData:
    raw = json.loads((ROOT / "examples" / "sample_project.ucd.json").read_text(encoding="utf-8"))
    return ProjectData.from_dict(raw)


def _synthetic_audit_project() -> ProjectData:
    raw = json.loads((ROOT / "examples" / "synthetic_20km_audit_case.ucd.json").read_text(encoding="utf-8"))
    return ProjectData.from_dict(raw)


def test_report_builder_does_not_mutate_project() -> None:
    project = _synthetic_audit_project()
    before = deepcopy(project)
    build_project_report(project)
    assert project == before


def test_warnings_module_is_mandatory_even_when_not_selected() -> None:
    project = _synthetic_audit_project()
    config = ReportConfiguration(
        metadata=ReportMetadata(report_type=REPORT_DESIGN),
        selected_modules=(MODULE_PROJECT,),
    )
    report = build_project_report(project, config)
    assert MODULE_WARNINGS in report.selected_modules
    assert report.sections[-1].section_id == MODULE_WARNINGS
    assert report.mandatory_warnings


def test_selected_modules_limit_report_sections() -> None:
    project = _sample_project()
    config = ReportConfiguration(
        metadata=ReportMetadata(report_type=REPORT_DESIGN),
        selected_modules=(MODULE_PROJECT,),
    )
    report = build_project_report(project, config)
    assert [section.section_id for section in report.sections] == [MODULE_PROJECT, MODULE_WARNINGS]


def test_calculation_results_are_rendered_in_tables() -> None:
    project = _sample_project()
    bonding = solve_bonding(project.cable, project.bonding, project.route_sections)
    iec = tuple(solve_project(project.cable, project.route_sections))
    config = ReportConfiguration(
        metadata=ReportMetadata(report_type=REPORT_CALCULATION),
        selected_modules=(MODULE_PROJECT, MODULE_IEC60287, MODULE_BONDING),
    )
    report = build_project_report(
        project,
        config,
        CalculationResultsBundle(iec_results=iec, bonding_result=bonding),
    )
    by_id = {section.section_id: section for section in report.sections}
    assert by_id[MODULE_IEC60287].status == "AVAILABLE"
    assert by_id[MODULE_IEC60287].tables[0].rows
    assert by_id[MODULE_BONDING].tables[0].rows


def test_missing_selected_calculation_is_explicitly_not_run() -> None:
    project = _sample_project()
    config = ReportConfiguration(
        metadata=ReportMetadata(report_type=REPORT_CALCULATION),
        selected_modules=(MODULE_IEC60287,),
    )
    report = build_project_report(project, config)
    section = next(item for item in report.sections if item.section_id == MODULE_IEC60287)
    assert section.status == "NOT_RUN"
    assert "nihai hesap kanıtı" in section.warnings[0]


def test_synthetic_source_conflicts_are_visible_in_report() -> None:
    report = build_project_report(_synthetic_audit_project())
    markdown = render_project_report_markdown(report)
    assert "0.95" in markdown
    assert "Sentetik güç faktörü doğrulama uyuşmazlığı" in markdown
    assert report.report_status == "CONDITIONAL"


def test_markdown_and_html_include_traceability_and_limitation() -> None:
    report = build_project_report(_sample_project())
    markdown = render_project_report_markdown(report)
    html = render_project_report_html(report)
    assert report.project_signature_sha256 in markdown
    assert report.project_signature_sha256 in html
    assert "nihai uygunluk" in markdown.lower()
    assert "nihai uygunluk" in html.lower()
    assert "DiTuS Kablo Analizör" in html


def test_project_signature_is_stable_for_same_project_state() -> None:
    project = _sample_project()
    first = build_project_report(project).project_signature_sha256
    second = build_project_report(project).project_signature_sha256
    assert first == second


def test_report_writer_creates_all_supported_formats(tmp_path: Path) -> None:
    report = build_project_report(
        _sample_project(),
        ReportConfiguration(
            metadata=ReportMetadata(report_type=REPORT_DESIGN, title="DiTuS Test Raporu"),
            selected_modules=(MODULE_PROJECT,),
        ),
    )
    paths = write_project_report(
        report,
        tmp_path,
        "ditus_test_report",
        ("json", "markdown", "html", "docx", "pdf"),
    )
    assert set(paths) == {"json", "markdown", "html", "docx", "pdf"}
    assert all(path.exists() and path.stat().st_size > 100 for path in paths.values())
    assert paths["pdf"].read_bytes().startswith(b"%PDF")
    assert paths["docx"].read_bytes().startswith(b"PK")
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["metadata"]["title"] == "DiTuS Test Raporu"


def test_detailed_trace_is_opt_in() -> None:
    project = _sample_project()
    bonding = solve_bonding(project.cable, project.bonding, project.route_sections)
    config_compact = ReportConfiguration(
        metadata=ReportMetadata(report_type=REPORT_CALCULATION),
        selected_modules=(MODULE_BONDING,),
        include_detailed_trace=False,
    )
    compact = build_project_report(project, config_compact, CalculationResultsBundle(bonding_result=bonding))
    bonding_compact = next(item for item in compact.sections if item.section_id == MODULE_BONDING)
    assert bonding_compact.trace == ()

    config_detailed = ReportConfiguration(
        metadata=ReportMetadata(report_type=REPORT_CALCULATION),
        selected_modules=(MODULE_BONDING,),
        include_detailed_trace=True,
    )
    detailed = build_project_report(project, config_detailed, CalculationResultsBundle(bonding_result=bonding))
    bonding_detailed = next(item for item in detailed.sections if item.section_id == MODULE_BONDING)
    assert bonding_detailed.trace


def test_dark_report_bands_use_white_text_in_html_and_docx(tmp_path: Path) -> None:
    import zipfile

    report = build_project_report(
        _sample_project(),
        ReportConfiguration(
            metadata=ReportMetadata(report_type=REPORT_DESIGN, title="Kontrast Testi"),
            selected_modules=(MODULE_PROJECT,),
        ),
    )
    html = render_project_report_html(report)
    assert "background:var(--ink); color:#fff" in html
    assert "h2 { color:#fff" in html
    paths = write_project_report(report, tmp_path, "contrast_test", ("docx",))
    with zipfile.ZipFile(paths["docx"]) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    assert 'w:fill="17324A"' in document_xml
    assert 'w:color w:val="FFFFFF"' in document_xml


def test_design_report_can_include_procurement_summary() -> None:
    from ucd.calculations.reporting import MODULE_PROCUREMENT

    report = build_project_report(
        _synthetic_audit_project(),
        ReportConfiguration(
            metadata=ReportMetadata(report_type=REPORT_DESIGN),
            selected_modules=(MODULE_PROCUREMENT,),
        ),
    )
    section = next(item for item in report.sections if item.section_id == MODULE_PROCUREMENT)
    assert section.tables
    assert any("Sipariş" in row[0] for row in section.tables[0].rows)
