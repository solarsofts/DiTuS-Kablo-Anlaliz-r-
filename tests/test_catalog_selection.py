from __future__ import annotations

from pathlib import Path
import sys

from ucd.calculations.cable_library import (
    apply_catalog_record,
    builtin_catalog_directory,
    cable_snapshot_hash,
    merge_builtin_catalogs,
)
from ucd.calculations.cable_selection import (
    evaluate_catalog_candidates,
    reference_ampacity,
    voltage_class_compatible,
)
from ucd.models.project import ProjectData


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
from synthetic_catalog_factory import build_synthetic_catalog_library, merge_synthetic_catalogs  # noqa: E402


def _synthetic_20km_basis_project() -> ProjectData:
    project = ProjectData()
    project.design_basis.system_voltage_kv = 34.5
    project.design_basis.apparent_power_mva = 20.0
    project.design_basis.circuit_count = 2
    project.design_basis.active_circuit_count = 2
    project.design_basis.n_minus_one_enabled = True
    project.design_basis.design_margin_percent = 10.0
    project.design_basis.total_route_length_m = 20000.0
    project.design_basis.installation_profile = "DIRECT_BURIED_TREFOIL"
    project.design_basis.conductor_preference = "AUTO"
    merge_synthetic_catalogs(project.cable_library)
    return project


def test_builtin_catalog_location_is_package_resource_and_contains_no_producer_json() -> None:
    directory = builtin_catalog_directory()
    assert "examples" not in directory.parts
    assert directory.name == "catalogs"
    assert directory.exists()
    assert list(directory.glob("*.ditus-cable-catalog.json")) == []
    assert not (ROOT / "examples" / "catalogs").exists()


def test_builtin_library_contains_only_seven_generic_conditional_templates() -> None:
    project = ProjectData()
    records = project.cable_library.records
    assert len(records) == 7
    assert all(record.manufacturer == "JENERİK" for record in records)
    assert all(record.status == "CONDITIONAL" for record in records)
    assert all("GENERIC_TEMPLATE" in record.tags for record in records)
    assert all("REAL_CATALOG" not in record.tags for record in records)
    assert all(not record.catalog_dimensions for record in records)
    assert all(not record.catalog_electrical for record in records)
    assert all(source.file_name == "" for source in project.cable_library.sources)


def test_builtin_merge_is_idempotent() -> None:
    project = ProjectData()
    first = merge_builtin_catalogs(project.cable_library)
    second = merge_builtin_catalogs(project.cable_library)
    assert first[0] == 0
    assert second[0] == 0
    assert len(project.cable_library.records) == 7
    assert "üretici verisi paketlenmedi" in first[2][0].lower()


def test_voltage_class_matching() -> None:
    assert voltage_class_compatible(34.5, "20.3/35 (40.5) kV")
    assert not voltage_class_compatible(36.0, "18/30 (36) kV")
    assert voltage_class_compatible(154.0, "87/150 (170) kV")


def test_synthetic_20km_catalog_screening_returns_traceable_conditional_candidates() -> None:
    project = _synthetic_20km_basis_project()
    result = evaluate_catalog_candidates(project.cable_library, project.design_basis)
    singles = [item for item in result.evaluations if item.parallel_cables_per_phase == 1]
    assert len(singles) == 3
    assert {item.manufacturer for item in singles} == {"Üretici A", "Üretici B", "Üretici C"}
    assert all(item.catalog_screening_status == "REFERENCE_ONLY" for item in singles)
    assert all(item.data_readiness == "CONDITIONAL" for item in singles)
    assert all(any("normalize" in warning.lower() for warning in item.warnings) for item in singles)
    assert all(item.voltage_drop_percent is not None for item in singles)


def test_reference_ampacity_uses_arrangement_specific_value() -> None:
    record = build_synthetic_catalog_library().records[0]
    trefoil, _ = reference_ampacity(record, "DIRECT_BURIED_TREFOIL")
    flat, _ = reference_ampacity(record, "DIRECT_BURIED_FLAT")
    assert trefoil == 545.0
    assert flat == 558.0


def test_catalog_snapshot_is_immutable_after_application() -> None:
    record = build_synthetic_catalog_library().records[0]
    cable = apply_catalog_record(record)
    before = cable_snapshot_hash(cable)
    record.catalog_electrical["ampacity_ground_trefoil_a"] = 1.0
    after = cable_snapshot_hash(cable)
    assert before == after
    assert cable.dc_resistance_20_ohm_km == 0.0778


def test_catalog_values_are_validation_evidence_not_solver_geometry_override() -> None:
    for record in build_synthetic_catalog_library().records:
        cable = apply_catalog_record(record)
        screen = next(
            layer for layer in cable.layers
            if layer.layer_type in {"WIRE_SCREEN", "METALLIC_SCREEN", "METALLIC_SHEATH"}
        )
        insulation = next(layer for layer in cable.layers if layer.layer_type == "INSULATION")
        conductor = next(layer for layer in cable.layers if layer.layer_type == "CONDUCTOR")
        assert cable.conductor_diameter_mm == conductor.outer_diameter_mm
        assert cable.t1_outer_diameter_mm == insulation.outer_diameter_mm
        assert cable.t2_outer_diameter_mm == screen.outer_diameter_mm
        assert cable.sheath_mean_diameter_mm == (screen.inner_diameter_mm + screen.outer_diameter_mm) / 2
        assert cable.overall_diameter_mm != record.catalog_dimensions["overall_diameter_mm"]
        assert cable.dc_resistance_20_ohm_km == record.catalog_electrical["conductor_rdc20_ohm_km"]
        assert cable.capacitance_uf_km == record.catalog_electrical["capacitance_uf_km"]
        gates = record.reference_conditions["validation_gates"]
        assert gates["diameter_gate"]["status"] == "PASS"
        assert gates["mass_gate"]["status"] == "PASS"


def test_synthetic_sources_have_no_local_file_name_or_hash_dependency() -> None:
    package = build_synthetic_catalog_library()
    assert package.records
    assert package.sources
    assert all(source.file_name == "" for source in package.sources)
    assert all(source.file_sha256 == "" for source in package.sources)
    assert all(source.page_reference.startswith("Sentetik satır") for source in package.sources)
