from __future__ import annotations

import json
from pathlib import Path
import zipfile

from ucd.calculations.procurement import (
    VIEW_RFQ,
    build_procurement_package,
    write_procurement_package,
)
from ucd.models.project import ProcurementQuantityOverride, ProjectData

ROOT = Path(__file__).resolve().parents[1]


def _synthetic_project() -> ProjectData:
    raw = json.loads((ROOT / "examples" / "synthetic_20km_applied.ucd.json").read_text(encoding="utf-8"))
    return ProjectData.from_dict(raw)


def test_synthetic_project_boq_bom_quantities_are_derived_from_project_graph() -> None:
    package = build_procurement_package(_synthetic_project())
    assert package.summary.net_route_length_m == 20000.0
    assert package.summary.order_single_core_length_m == 122349.0
    assert package.summary.termination_units == 12
    assert package.summary.joint_units == 120
    assert package.summary.link_box_units == 40
    assert package.summary.svl_units == 84
    assert package.summary.svl_set_units == 28
    assert package.summary.cross_bonding_link_box_units == 28
    assert package.summary.grounding_link_box_units == 12
    assert package.summary.drum_count == 126
    by_id = {item.item_id: item for item in package.lines}
    assert by_id["CBL-001"].basis.formula.startswith("route × 3 faz")
    assert by_id["CIV-EXC-001"].final_quantity == 48400.0
    assert abs(by_id["CIV-TBF-001"].final_quantity - 5350.0) < 1e-9


def test_user_quantity_override_preserves_auto_quantity_and_rationale() -> None:
    project = _synthetic_project()
    project.procurement.quantity_overrides = [
        ProcurementQuantityOverride("BND-LB-CROSS-001", 30.0, "İki adet işletme yedeği")
    ]
    package = build_procurement_package(project)
    line = next(item for item in package.lines if item.item_id == "BND-LB-CROSS-001")
    assert line.auto_quantity == 28.0
    assert line.final_quantity == 30.0
    assert line.override_rationale == "İki adet işletme yedeği"
    assert any("kullanıcı" in warning.lower() for warning in package.warnings)


def test_drum_plan_contains_every_route_cut_and_visible_reserve() -> None:
    package = build_procurement_package(_synthetic_project())
    cuts = [cut for drum in package.drums for cut in drum.cuts]
    route_cuts = [cut for cut in cuts if cut.cut_type == "ROUTE_SEGMENT"]
    reserve = [cut for cut in cuts if cut.cut_type == "ORDER_RESERVE"]
    assert len(route_cuts) == 126
    assert not reserve
    assert package.summary.drum_count == 126
    assert package.summary.drum_plan_status == "VALID"
    assert package.summary.overload_total_m == 0.0
    assert all(drum.loaded_length_m <= drum.maximum_length_m for drum in package.drums)
    assert abs(sum(drum.loaded_length_m for drum in package.drums) - package.summary.order_single_core_length_m) < 1e-9
    assert abs(sum(drum.order_allowance_m for drum in package.drums) - package.summary.order_allowance_total_m) < 1e-9


def test_rfq_view_contains_required_documents_and_supplier_columns() -> None:
    package = build_procurement_package(_synthetic_project())
    rfq = package.lines_for_view(VIEW_RFQ)
    cable = next(item for item in rfq if item.item_id == "CBL-001")
    assert cable.required_documents
    assert "Birim fiyat" in cable.supplier_response_fields


def test_procurement_writer_creates_xlsx_csv_json_html_markdown_docx_pdf(tmp_path: Path) -> None:
    package = build_procurement_package(_synthetic_project())
    paths = write_procurement_package(
        package,
        tmp_path,
        "synthetic_20km_procurement_test",
        ("xlsx", "csv", "json", "html", "markdown", "docx", "pdf"),
    )
    assert {"xlsx", "json", "html", "markdown", "docx", "pdf", "csv_boq", "csv_bom", "csv_rfq", "csv_drum_plan"} <= set(paths)
    assert all(path.exists() and path.stat().st_size > 100 for path in paths.values())
    assert paths["xlsx"].read_bytes().startswith(b"PK")
    assert paths["docx"].read_bytes().startswith(b"PK")
    assert paths["pdf"].read_bytes().startswith(b"%PDF")
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["summary"]["order_single_core_length_m"] == 122349.0
    html = paths["html"].read_text(encoding="utf-8")
    assert "background:var(--navy);color:#fff" in html
    with zipfile.ZipFile(paths["xlsx"]) as archive:
        styles = archive.read("xl/styles.xml").decode("utf-8")
    assert "FF17324A" in styles
    assert "FFFFFFFF" in styles
