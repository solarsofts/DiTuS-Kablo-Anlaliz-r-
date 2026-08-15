from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from ucd.calculations.cable_library import (
    catalog_package_from_dict,
    catalog_package_to_dict,
    normalize_catalog_library,
    synchronize_cable_from_layers,
)
from ucd.calculations.cable_template_generator import (
    build_generic_template_library,
    estimate_cable_mass_kg_km,
    load_generic_profile_data,
)
from ucd.calculations.thermal_resistance import resolve_internal_thermal_resistance
from ucd.models.project import (
    CABLE_STATUS_CONDITIONAL,
    CableData,
    CableLibraryData,
    ProjectData,
    default_cable_layers,
    default_cable_sources,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = {
    "GEN-MV24-AL-150-CWS25",
    "GEN-MV24-CU-240-CWS25",
    "GEN-MV24-AL-400-CWS35",
    "GEN-MV40K5-AL-240-CWS25",
    "GEN-MV40K5-CU-400-CWS35",
    "GEN-MV40K5-AL-630-CWS50",
    "GEN-HV170-AL-1600-BOND01",
}


def _snapshot(record_id: str) -> CableData:
    record = next(item for item in build_generic_template_library().records if item.record_id == record_id)
    package = catalog_package_from_dict(catalog_package_to_dict(CableLibraryData(records=[record])))
    from ucd.calculations.cable_library import cable_from_dict

    return cable_from_dict(package.records[0].cable_snapshot)


def test_package_has_no_builtin_manufacturer_product_rows() -> None:
    assert not (ROOT / "examples" / "catalogs").exists()
    resource_dir = ROOT / "src" / "ucd" / "resources" / "catalogs"
    assert resource_dir.is_dir()
    assert not list(resource_dir.glob("*.json"))
    assert not list(resource_dir.glob("*.ditus-cable-catalog.json"))

    library = build_generic_template_library()
    assert {record.record_id for record in library.records} == EXPECTED_IDS
    assert {record.manufacturer for record in library.records} == {"JENERİK"}
    assert all(not record.catalog_dimensions and not record.catalog_electrical for record in library.records)
    assert all("NO_MANUFACTURER_DATA" in record.tags for record in library.records)


def test_seven_generic_templates_cover_selected_voltage_material_and_area_matrix() -> None:
    library = build_generic_template_library()
    assert len(library.records) == 7
    assert {record.conductor_material for record in library.records} == {"Al", "Cu"}
    assert {record.voltage_class for record in library.records} == {
        "12/20 (24) kV",
        "20.3/35 (40.5) kV",
        "87/150 (170) kV",
    }
    assert {record.conductor_area_mm2 for record in library.records} == {
        150.0, 240.0, 400.0, 630.0, 1600.0
    }
    assert all(record.status == CABLE_STATUS_CONDITIONAL for record in library.records)


def test_parametric_layer_chain_is_continuous_and_outer_diameter_is_output() -> None:
    cable = _snapshot("GEN-MV40K5-AL-630-CWS50")
    previous_outer = 0.0
    for layer in cable.layers:
        assert layer.inner_diameter_mm == pytest.approx(previous_outer, abs=1e-9)
        assert layer.outer_diameter_mm > layer.inner_diameter_mm
        previous_outer = layer.outer_diameter_mm
    assert cable.overall_diameter_mm == pytest.approx(previous_outer)

    ignored_a = default_cable_layers("Al", 630.0, 70.0, voltage_class="20.3/35 (40.5) kV")
    ignored_b = default_cable_layers("Al", 630.0, 140.0, voltage_class="20.3/35 (40.5) kV")
    assert ignored_a[-1].outer_diameter_mm == pytest.approx(ignored_b[-1].outer_diameter_mm)


def test_outer_sheath_is_standard_profile_output_not_residual_fill() -> None:
    library = build_generic_template_library()
    walls = []
    for record in library.records:
        cable = _snapshot(record.record_id)
        outer = next(layer for layer in cable.layers if layer.layer_type == "OUTER_SHEATH")
        wall = (outer.outer_diameter_mm - outer.inner_diameter_mm) / 2.0
        walls.append(wall)
        assert 3.0 <= wall <= 5.0
        assert cable.t3_outer_diameter_mm if hasattr(cable, "t3_outer_diameter_mm") else True
        result = resolve_internal_thermal_resistance(cable)
        assert result.t3_km_w > 0
    assert min(walls) >= 3.0
    assert max(walls) <= 5.0


def test_different_conductor_sections_produce_different_t1_geometry_and_result() -> None:
    small = _snapshot("GEN-MV24-AL-150-CWS25")
    large = _snapshot("GEN-MV24-AL-400-CWS35")
    assert small.conductor_diameter_mm != pytest.approx(large.conductor_diameter_mm)
    assert small.t1_outer_diameter_mm != pytest.approx(large.t1_outer_diameter_mm)
    small_result = resolve_internal_thermal_resistance(small)
    large_result = resolve_internal_thermal_resistance(large)
    assert small_result.t1_km_w != pytest.approx(large_result.t1_km_w)


def test_synchronization_is_mandatory_for_seed_project_import_and_catalog_import() -> None:
    layers = default_cable_layers("Al", 400.0, voltage_class="20.3/35 (40.5) kV")
    stale = CableData(
        voltage_class="20.3/35 (40.5) kV",
        conductor_material="Al",
        conductor_area_mm2=400.0,
        conductor_diameter_mm=1.0,
        t1_outer_diameter_mm=2.0,
        t2_outer_diameter_mm=3.0,
        overall_diameter_mm=999.0,
        layers=deepcopy(layers),
        parameter_sources=default_cable_sources("20.3/35 (40.5) kV"),
    )
    synchronize_cable_from_layers(stale)
    assert stale.conductor_diameter_mm == pytest.approx(layers[0].outer_diameter_mm)
    assert stale.overall_diameter_mm == pytest.approx(layers[-1].outer_diameter_mm)

    raw_project = ProjectData(cable=deepcopy(stale)).to_dict()
    raw_project["cable"]["overall_diameter_mm"] = 777.0
    loaded_project = ProjectData.from_dict(raw_project)
    assert loaded_project.cable.overall_diameter_mm == pytest.approx(layers[-1].outer_diameter_mm)

    library = build_generic_template_library()
    raw_package = catalog_package_to_dict(library)
    raw_package["package"]["records"][0]["cable_snapshot"]["overall_diameter_mm"] = 555.0
    imported = catalog_package_from_dict(raw_package)
    imported_cable = imported.records[0].cable_snapshot
    assert imported_cable["overall_diameter_mm"] == pytest.approx(
        imported_cable["layers"][-1]["outer_diameter_mm"]
    )


def test_known_material_thermal_resistivities_are_central_and_import_safe() -> None:
    data = load_generic_profile_data()
    assert data["materials"]["PE"]["thermal_resistivity_km_w"] == 3.5
    assert data["materials"]["PVC"]["thermal_resistivity_km_w"] == 6.0

    raw = catalog_package_to_dict(build_generic_template_library())
    mv_record = next(
        item for item in raw["package"]["records"] if item["record_id"] == "GEN-MV40K5-AL-240-CWS25"
    )
    outer = next(
        item for item in mv_record["cable_snapshot"]["layers"] if item["layer_type"] == "OUTER_SHEATH"
    )
    outer["thermal_resistivity_km_w"] = 123.0
    imported = catalog_package_from_dict(raw)
    imported_record = next(item for item in imported.records if item.record_id == "GEN-MV40K5-AL-240-CWS25")
    imported_outer = next(
        item for item in imported_record.cable_snapshot["layers"] if item["layer_type"] == "OUTER_SHEATH"
    )
    assert imported_outer["material"] == "PVC"
    assert imported_outer["thermal_resistivity_km_w"] == 6.0


def test_catalog_diameter_and_mass_gates_fail_closed_without_overwriting_geometry() -> None:
    library = build_generic_template_library()
    record = deepcopy(library.records[0])
    cable_od = float(record.cable_snapshot["overall_diameter_mm"])
    cable_mass = estimate_cable_mass_kg_km(_snapshot(record.record_id))
    record.catalog_dimensions = {
        "overall_diameter_mm": cable_od * 1.50,
        "net_weight_kg_km": cable_mass * 1.50,
    }
    normalize_catalog_library(CableLibraryData(records=[record]))
    gates = record.reference_conditions["validation_gates"]
    assert gates["status"] == "FAIL"
    assert gates["diameter_gate"]["status"] == "FAIL"
    assert gates["mass_gate"]["status"] == "FAIL"
    assert record.status == CABLE_STATUS_CONDITIONAL
    assert record.cable_snapshot["data_status"] == CABLE_STATUS_CONDITIONAL
    assert record.cable_snapshot["overall_diameter_mm"] == pytest.approx(cable_od)
    assert "DIAMETER_GATE" in record.notes
    assert "MASS_GATE" in record.notes


def test_generic_templates_have_no_cat_provenance_and_keep_assume_calc_classes() -> None:
    library = build_generic_template_library()
    for record in library.records:
        source_types = {
            source["source_type"] for source in record.cable_snapshot["parameter_sources"]
        }
        assert "CATALOG" not in source_types
        assert "CALCULATED" in source_types
        assert "USER_ASSUMPTION" in source_types
        assert "STANDARD_DERIVED" in source_types


def test_manufacturer_link_list_is_separate_and_uses_stable_pages() -> None:
    path = ROOT / "src" / "ucd" / "resources" / "manufacturer_catalog_links.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "onay" in payload["notice"].lower()
    assert "işbirliği" in payload["notice"].lower()
    assert len(payload["links"]) >= 4
    assert all(item["url"].startswith("https://") for item in payload["links"])
    assert all(not item["url"].lower().endswith(".pdf") for item in payload["links"])
