from copy import deepcopy

from ucd.calculations.cable_library import (
    apply_catalog_record,
    cable_snapshot_hash,
    catalog_package_from_dict,
    catalog_package_to_dict,
    catalog_record_from_cable,
    create_project_snapshot,
    filter_catalog_records,
    synchronize_cable_from_layers,
    validate_cable,
)
from ucd.models.project import (
    CableData,
    ProjectData,
    default_cable_layers,
    default_cable_sources,
)


def test_default_project_has_parametric_cable_and_generic_library() -> None:
    project = ProjectData()
    assert project.schema_version == "0.16.4"
    assert len(project.cable.layers) >= 7
    assert len(project.cable_library.records) == 7
    assert all(record.manufacturer == "JENERİK" for record in project.cable_library.records)
    assert all(record.cable_snapshot for record in project.cable_library.records)


def test_layer_geometry_synchronizes_solver_fields_and_ignores_legacy_outer_input() -> None:
    cable = CableData(
        voltage_class="87/150 (170) kV",
        conductor_material="Al",
        conductor_area_mm2=1600.0,
        layers=default_cable_layers(
            "Al", 1600.0, 116.0,
            voltage_class="87/150 (170) kV",
            screen_area_mm2=150.0,
            screen_profile="HV-BOND-01",
            stranding_type="MILLIKEN",
        ),
        parameter_sources=default_cable_sources("87/150 (170) kV"),
    )
    derived = synchronize_cable_from_layers(cable)
    assert cable.conductor_area_mm2 == 1600.0
    assert cable.conductor_material == "Al"
    assert cable.overall_diameter_mm == derived.overall_diameter_mm
    assert cable.overall_diameter_mm != 116.0
    assert cable.capacitance_uf_km > 0
    assert cable.dc_resistance_20_ohm_km > 0
    assert cable.sheath_dc_resistance_20_ohm_km > 0
    assert derived.sheath_cross_section_mm2 == 150.0


def test_screen_wire_geometry_mismatch_is_rejected() -> None:
    cable = CableData(
        voltage_class="20.3/35 (40.5) kV",
        layers=default_cable_layers(
            "Al", 400.0,
            voltage_class="20.3/35 (40.5) kV",
            screen_area_mm2=35.0,
            screen_profile="CWS",
        ),
        parameter_sources=default_cable_sources("20.3/35 (40.5) kV"),
    )
    screen = next(layer for layer in cable.layers if layer.layer_type == "METALLIC_SCREEN")
    screen.wire_count = 5
    screen.wire_diameter_mm = 1.0
    report = validate_cable(cable)
    assert report.has_errors
    assert any(issue.code == "SCREEN_GEOMETRY_MISMATCH" for issue in report.issues)


def test_snapshot_hash_is_stable_and_project_copy_is_immutable() -> None:
    cable = CableData(layers=default_cable_layers(), parameter_sources=default_cable_sources())
    first_hash = cable_snapshot_hash(cable)
    snapshot = create_project_snapshot(cable, "REC-001")
    assert snapshot.snapshot_hash == first_hash
    old_area = snapshot.conductor_area_mm2
    cable.conductor_area_mm2 = 2000.0
    assert snapshot.conductor_area_mm2 == old_area
    assert snapshot.catalog_record_id == "REC-001"


def test_catalog_record_applies_as_new_synchronized_snapshot() -> None:
    cable = CableData(
        manufacturer="TEST",
        series="SERIES",
        model="MODEL",
        voltage_class="20.3/35 (40.5) kV",
        layers=default_cable_layers(
            "Cu", 400.0,
            voltage_class="20.3/35 (40.5) kV",
            screen_area_mm2=35.0,
            screen_profile="CWS",
        ),
        parameter_sources=default_cable_sources("20.3/35 (40.5) kV"),
    )
    record = catalog_record_from_cable(cable, "REC-001")
    target = CableData()
    apply_catalog_record(record, target)
    assert target.catalog_record_id == "REC-001"
    assert target.snapshot_id.startswith("SNAP-")
    assert target.manufacturer == "TEST"
    assert target.layers is not cable.layers
    assert target.overall_diameter_mm == max(layer.outer_diameter_mm for layer in target.layers)


def test_catalog_package_round_trip_and_filter() -> None:
    project = ProjectData()
    payload = catalog_package_to_dict(project.cable_library)
    loaded = catalog_package_from_dict(deepcopy(payload))
    assert len(loaded.records) == len(project.cable_library.records)
    selected = filter_catalog_records(
        loaded,
        manufacturer="JENERİK",
        conductor_material="Al",
        minimum_area_mm2=1500.0,
    )
    assert selected
    assert all(item.conductor_material == "Al" for item in selected)
    assert all(item.conductor_area_mm2 >= 1500.0 for item in selected)


def test_v013_project_migrates_with_generated_layers_and_library() -> None:
    raw = {
        "schema_version": "0.13",
        "project_name": "Legacy",
        "cable": {
            "name": "Legacy cable",
            "conductor_material": "Al",
            "conductor_area_mm2": 1600.0,
            "overall_diameter_mm": 114.0,
        },
    }
    loaded = ProjectData.from_dict(raw)
    assert loaded.schema_version == "0.16.4"
    assert loaded.project_name == "Legacy"
    assert loaded.cable.layers
    assert loaded.cable.layers[0].conductor_area_mm2 == 1600.0
    assert loaded.cable.overall_diameter_mm == max(layer.outer_diameter_mm for layer in loaded.cable.layers)
    assert len(loaded.cable_library.records) == 7


def test_armour_and_metallic_sheath_are_validated_as_separate_layers() -> None:
    cable = CableData(layers=default_cable_layers(), parameter_sources=default_cable_sources())
    cable.armour_loss_factor = 0.08
    report = validate_cable(cable)
    assert any(issue.code == "ARMOUR_FACTOR_WITHOUT_LAYER" for issue in report.issues)

    outer = next(layer for layer in cable.layers if layer.layer_type == "OUTER_SHEATH")
    source_id = cable.parameter_sources[0].source_id
    outer.outer_diameter_mm += 4.0
    cable.layers.insert(-1, type(outer)(
        layer_id="L06A", name="Çelik tel zırh", layer_type="ARMOUR",
        inner_diameter_mm=outer.inner_diameter_mm, outer_diameter_mm=outer.inner_diameter_mm + 4.0,
        material="Steel", source_id=source_id,
    ))
    outer.inner_diameter_mm += 4.0
    cable.armour_loss_factor = 0.0
    report = validate_cable(cable)
    assert any(issue.code == "ARMOUR_LAYER_WITH_ZERO_FACTOR" for issue in report.issues)
    assert not any(issue.code == "NO_METALLIC_SCREEN" for issue in report.issues)
