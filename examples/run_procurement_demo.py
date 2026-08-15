from __future__ import annotations

import json
from pathlib import Path

from ucd import __version__
from ucd.calculations.procurement import build_procurement_package, write_procurement_package
from ucd.models.project import ProjectData

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def main() -> None:
    source = EXAMPLES / "synthetic_20km_applied.ucd.json"
    project = ProjectData.from_dict(json.loads(source.read_text(encoding="utf-8")))
    project.project_code = "DITUS-DEMO-20KM-APPLIED"
    project.procurement.installation_allowance_percent = 1.0
    project.procurement.waste_percent = 2.0
    project.procurement.spare_cable_percent = 0.0
    project.procurement.termination_tail_m_per_end = 5.0
    project.procurement.joint_tail_m_per_side = 2.0
    project.procurement.maximum_drum_length_m = 1000.0
    project.procurement.include_civil_items = True
    project_file = EXAMPLES / "synthetic_20km_procurement.ucd.json"
    project_file.write_text(json.dumps(project.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    package = build_procurement_package(project)
    paths = write_procurement_package(
        package,
        EXAMPLES,
        "synthetic_20km_boq_bom_rfq.latest",
        ("xlsx", "csv", "json", "html", "markdown", "docx", "pdf"),
    )
    expected = {
        "version": __version__,
        "project_code": package.project_code,
        "net_route_length_m": package.summary.net_route_length_m,
        "installed_single_core_length_m": package.summary.installed_single_core_length_m,
        "order_single_core_length_m": package.summary.order_single_core_length_m,
        "termination_units": package.summary.termination_units,
        "joint_units": package.summary.joint_units,
        "link_box_units": package.summary.link_box_units,
        "cross_bonding_link_box_units": package.summary.cross_bonding_link_box_units,
        "grounding_link_box_units": package.summary.grounding_link_box_units,
        "svl_set_units": package.summary.svl_set_units,
        "svl_units": package.summary.svl_units,
        "drum_count": package.summary.drum_count,
        "drum_plan_status": package.summary.drum_plan_status,
        "order_allowance_total_m": package.summary.order_allowance_total_m,
        "overload_total_m": package.summary.overload_total_m,
        "line_count": len(package.lines),
        "status": package.summary.status,
        "files": {name: path.name for name, path in sorted(paths.items())},
    }
    (EXAMPLES / "synthetic_20km_procurement_expected.json").write_text(
        json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(expected, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
