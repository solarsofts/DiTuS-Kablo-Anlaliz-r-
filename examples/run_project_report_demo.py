from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations import (  # noqa: E402
    CalculationResultsBundle,
    ReportConfiguration,
    ReportMetadata,
    REPORT_DESIGN,
    REPORT_TEMPLATES,
    build_project_report,
    solve_project_bonding,
    solve_production_electrothermal_study,
    solve_fault_study,
    solve_nodal_route,
    solve_svl_selection,
    solve_transient_route,
    transfer_fault_tov_to_svl,
    write_project_report,
)
from ucd.models.project import ProjectData  # noqa: E402


def main() -> int:
    examples = ROOT / "examples"
    project_path = examples / "synthetic_20km_applied.ucd.json"
    project = ProjectData.from_dict(json.loads(project_path.read_text(encoding="utf-8")))

    bonding = solve_project_bonding(project)
    production = solve_production_electrothermal_study(project)
    nodal = solve_nodal_route(project, bonding, "DESIGN")
    transient = solve_transient_route(project, bonding, nodal)
    fault = solve_fault_study(project.cable, project.bonding, project.route_sections, project.fault_study)
    transfer_fault_tov_to_svl(project.fault_study, fault, project.svl)
    svl = solve_svl_selection(project.svl, project.bonding, bonding.max_standing_voltage_v)

    configuration = ReportConfiguration(
        metadata=ReportMetadata(
            report_type=REPORT_DESIGN,
            title="Sentetik 20 km Yeraltı Kablo Proje ve Hesap Raporu",
            document_no="DITUS-DEMO-20KM-RPT-001",
            revision="00",
            client="Sentetik 20 km Örnek Hat",
            checked_by="Teknik kontrol bekliyor",
            approval_status="TASLAK - KOŞULLU",
        ),
        selected_modules=REPORT_TEMPLATES[REPORT_DESIGN],
        include_detailed_trace=False,
        output_formats=("json", "markdown", "html", "docx", "pdf"),
    )
    report = build_project_report(
        project,
        configuration,
        CalculationResultsBundle(
            iec_results=(),  # Legacy tek-akım IEC görünümü yerine üretim senaryo × fiziksel kablo çevrimi raporlanır.
            production_electrothermal_result=production,
            nodal_thermal_result=nodal,
            transient_thermal_result=transient,
            bonding_result=bonding,
            fault_result=fault,
            svl_result=svl,
        ),
    )
    paths = write_project_report(
        report,
        examples,
        "synthetic_20km_project_report.latest",
        configuration.output_formats,
    )
    signature_path = examples / "synthetic_20km_project_report_signature.latest.json"
    signature_path.write_text(
        json.dumps(
            {
                "format": "DITUS_PROJECT_REPORT_DEMO",
                "version": "0.16.1",
                "project_file": project_path.name,
                "project_signature_sha256": report.project_signature_sha256,
                "report_status": report.report_status,
                "selected_modules": list(report.selected_modules),
                "outputs": {key: value.name for key, value in paths.items()},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({key: str(value) for key, value in paths.items()}, ensure_ascii=False, indent=2))
    print(f"İmza: {signature_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
