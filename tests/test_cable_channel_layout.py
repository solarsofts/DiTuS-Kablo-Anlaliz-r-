from __future__ import annotations

from pathlib import Path

from ucd.calculations.installation import (
    channel_geometry_defaults,
    channel_geometry_bounds,
    channel_half_width_at_depth,
    channel_polygon_vertices,
    direct_buried_envelope,
    direct_buried_warning_depths,
    synchronise_direct_buried_geometry,
    point_inside_channel,
    insert_material_region_vertex,
    remove_material_region_vertex,
    polygon_self_intersects,
    section_clearance_records,
    update_channel_geometry_for_installation,
    validate_installation_design,
)
from ucd.calculations.cable_channel_templates import (
    apply_cable_channel_template,
    built_in_cable_channel_templates,
    reposition_existing_cables,
)
from ucd.calculations.multiconductor_thermal import _channel_profile_and_overrides
from ucd.calculations.thermal_material_library import (
    built_in_reference_materials,
    merge_reference_materials,
    validate_material_for_final_design,
)
from ucd.calculations.thermal_route import resolve_thermal_region
from ucd.calculations.nodal_thermal import _NodalModel
from ucd.models.project import ProjectData, ThermalMaterialData, ThermalMaterialRegionData


ROOT = Path(__file__).resolve().parents[1]


def test_default_project_has_additive_channel_geometry_and_round_trip() -> None:
    project = ProjectData()
    design = project.installation_design
    assert design.model_revision == "0.16.9.4.34"
    section = design.cross_sections[0]
    assert section.channel_geometry.trench_width_m > 0
    assert section.channel_geometry.trench_depth_m > 0
    section.channel_geometry.trench_width_m = 1.234
    section.channel_geometry.cover_slab_enabled = True
    section.channel_geometry.cover_slab_material_id = "MAT-CONCRETE-01"
    section.channel_geometry.source_reference = "USER_INTERACTIVE_GEOMETRY"

    loaded = ProjectData.from_dict(project.to_dict())
    geometry = loaded.installation_design.cross_sections[0].channel_geometry
    assert geometry.trench_width_m == 1.234
    assert geometry.cover_slab_enabled is True
    assert geometry.cover_slab_material_id == "MAT-CONCRETE-01"
    assert geometry.source_reference == "USER_INTERACTIVE_GEOMETRY"


def test_installation_type_changes_parametric_structure() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    update_channel_geometry_for_installation(section, "DUCT_BANK", reset_dimensions=True)
    assert section.installation_type == "DUCT_BANK"
    assert section.channel_geometry.geometry_mode == "PARAMETRIC_DUCT_BANK"
    assert section.channel_geometry.duct_bank_width_m > 0

    update_channel_geometry_for_installation(section, "CONCRETE_TROUGH", reset_dimensions=True)
    assert section.channel_geometry.geometry_mode == "PARAMETRIC_CONCRETE_TROUGH"
    assert section.channel_geometry.trough_inner_width_m > 0

    defaults = channel_geometry_defaults("TUNNEL", burial_depth_m=2.0, cable_span_m=0.8)
    assert defaults.geometry_mode == "PARAMETRIC_TUNNEL"
    assert defaults.cover_slab_enabled is False


def test_channel_validation_detects_invalid_stack_and_outside_cable() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    geometry = section.channel_geometry
    geometry.trench_depth_m = 0.50
    geometry.bedding_thickness_m = 0.30
    geometry.thermal_backfill_height_m = 0.30
    geometry.selected_fill_thickness_m = 0.20
    section.physical_cables[0].x_m = geometry.center_x_m + geometry.trench_width_m
    codes = {item.code for item in validate_installation_design(project)}
    assert "CHANNEL_LAYER_STACK" in codes
    assert "CABLE_OUTSIDE_CHANNEL" in codes


def test_reference_material_library_keeps_rock_and_granular_fill_distinct() -> None:
    materials = built_in_reference_materials()
    by_id = {item.material_id: item for item in materials}
    assert "REF-BASALT-INTACT-01" in by_id
    assert "REF-LIMESTONE-INTACT-01" in by_id
    assert "REF-CRUSHED-BASALT-01" in by_id
    assert by_id["REF-BASALT-INTACT-01"].name != by_id["REF-CRUSHED-BASALT-01"].name
    assert by_id["REF-CRUSHED-BASALT-01"].requires_project_test is True
    assert any(
        item.code == "PROJECT_TEST_REQUIRED"
        for item in validate_material_for_final_design(by_id["REF-CRUSHED-BASALT-01"])
    )


def test_reference_material_merge_does_not_overwrite_project_rows() -> None:
    project = ProjectData()
    initial = len(project.thermal_design.materials)
    first = merge_reference_materials(project.thermal_design)
    second = merge_reference_materials(project.thermal_design)
    assert first > 0
    assert second == 0
    assert len(project.thermal_design.materials) == initial + first


def test_user_accepted_channel_geometry_maps_to_shadow_profile() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    region = project.thermal_design.regions[0]
    profile = resolve_thermal_region(project.thermal_design, region, project.cable)

    # Legacy projections must preserve the locked thermal profile.
    legacy_profile, legacy_overrides, legacy_issues = _channel_profile_and_overrides(
        project, profile, section
    )
    assert legacy_profile == profile
    assert legacy_overrides == {}
    assert legacy_issues == ()

    section.channel_geometry.source_reference = "USER_INTERACTIVE_GEOMETRY"
    section.channel_geometry.trench_width_m = 1.35
    section.channel_geometry.cover_slab_enabled = True
    resolved, overrides, issues = _channel_profile_and_overrides(project, profile, section)
    assert resolved.trench_width_m == 1.35
    assert overrides["cover_slab_enabled"] is True
    assert any(item.code == "INSTALLATION_CHANNEL_GEOMETRY_ACTIVE" for item in issues)



def test_migrated_pre_channel_project_does_not_silently_override_shadow_profile() -> None:
    original = ProjectData()
    payload = original.to_dict()
    for section in payload["installation_design"]["cross_sections"]:
        section.pop("channel_geometry", None)
    migrated = ProjectData.from_dict(payload)
    section = migrated.installation_design.cross_sections[0]
    assert section.channel_geometry.source_reference == "MIGRATED_PARAMETRIC_DEFAULT"
    region = migrated.thermal_design.regions[0]
    profile = resolve_thermal_region(migrated.thermal_design, region, migrated.cable)
    resolved, overrides, issues = _channel_profile_and_overrides(migrated, profile, section)
    assert resolved == profile
    assert overrides == {}
    assert issues == ()

def test_ui_contract_contains_interactive_geometry_and_real_material_library() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    material_dialog = (ROOT / "src" / "ucd" / "ui" / "thermal_material_library_dialog.py").read_text(encoding="utf-8")
    main = (ROOT / "src" / "ucd" / "ui" / "main_window.py").read_text(encoding="utf-8")
    thermal_bridge = (ROOT / "src" / "ucd" / "calculations" / "multiconductor_thermal.py").read_text(encoding="utf-8")

    assert "Kablo-Kanal Düzeni" in dialog
    assert "geometryChanged" in dialog
    assert "Kaynaklı Referans Malzemeleri Projeye Ekle" in dialog
    assert "ThermalMaterialLibraryDialog" in material_dialog
    assert "show_thermal_material_library" in main
    assert "INSTALLATION_CHANNEL_GEOMETRY_ACTIVE" in thermal_bridge
    assert "value_overrides=channel_overrides" in thermal_bridge


def test_sloped_trench_uses_bottom_width_and_expands_toward_surface() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    g = section.channel_geometry
    g.center_x_m = 0.20
    g.trench_width_m = 0.80
    g.trench_depth_m = 1.50
    g.side_slope_h_to_v = 0.50

    assert abs(channel_half_width_at_depth(section, 1.50) - 0.40) < 1e-12
    assert abs(channel_half_width_at_depth(section, 0.0) - 1.15) < 1e-12
    vertices = channel_polygon_vertices(section)
    assert vertices[0] == (-0.95, 0.0)
    assert abs(vertices[2][0] - 0.60) < 1e-12 and vertices[2][1] == 1.50
    left, right, bottom = channel_geometry_bounds(section)
    assert abs(left + 0.95) < 1e-12 and abs(right - 1.35) < 1e-12 and bottom == 1.50
    assert point_inside_channel(section, 1.20, 0.10) is True
    assert point_inside_channel(section, 0.80, 1.45) is False


def test_custom_material_region_round_trip_and_shadow_override() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.channel_geometry.source_reference = "USER_INTERACTIVE_GEOMETRY"
    section.material_regions.append(ThermalMaterialRegionData(
        "MR-01", "Kaya merceği", "MAT-NATIVE-01",
        [[-0.80, 0.90], [-0.10, 0.85], [0.05, 1.40], [-0.75, 1.45]],
        priority=150,
    ))
    loaded = ProjectData.from_dict(project.to_dict())
    loaded_section = loaded.installation_design.cross_sections[0]
    region = loaded_section.material_regions[0]
    assert region.region_id == "MR-01"
    assert region.vertices_m[2] == [0.05, 1.40]
    thermal_region = loaded.thermal_design.regions[0]
    profile = resolve_thermal_region(loaded.thermal_design, thermal_region, loaded.cable)
    _resolved, overrides, issues = _channel_profile_and_overrides(loaded, profile, loaded_section)
    custom = overrides["custom_material_regions"]
    assert custom[0]["region_id"] == "MR-01"
    assert custom[0]["priority"] == 150
    assert any(item.code == "INSTALLATION_CHANNEL_GEOMETRY_ACTIVE" for item in issues)


def test_custom_material_region_validation_rejects_degenerate_polygon() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.material_regions.append(ThermalMaterialRegionData(
        "MR-BAD", "Bozuk", "MAT-NATIVE-01", [[0.0, 1.0], [0.1, 1.0]],
    ))
    codes = {item.code for item in validate_installation_design(project)}
    assert "MATERIAL_REGION_GEOMETRY" in codes


def test_ui_contract_contains_object_dragging_and_material_polygons() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    nodal = (ROOT / "src" / "ucd" / "calculations" / "nodal_thermal.py").read_text(encoding="utf-8")
    assert "ductMoved = Signal" in dialog
    assert "heatSourceMoved = Signal" in dialog
    assert "materialRegionMoved = Signal" in dialog
    assert "side_slope_h_to_v" in dialog
    assert "Malzeme Bölgeleri" in dialog
    assert "custom_material_regions" in nodal
    assert "_point_in_polygon" in nodal


def test_custom_material_polygon_is_rasterized_into_nodal_material_grid() -> None:
    project = ProjectData()
    project.thermal_design.materials.append(
        ThermalMaterialData("MAT-CUSTOM-X", "Özel test bölgesi", "NATIVE_SOIL", 4.0)
    )
    thermal_region = project.thermal_design.regions[0]
    profile = resolve_thermal_region(project.thermal_design, thermal_region, project.cable)
    model = _NodalModel(
        project, thermal_region, profile, 1,
        value_overrides={
            "custom_material_regions": ({
                "region_id": "MR-X",
                "material_id": "MAT-CUSTOM-X",
                "vertices_m": ((-0.50, 0.80), (0.50, 0.80), (0.50, 1.40), (-0.50, 1.40)),
                "priority": 100,
            },),
        },
    )
    assert int((model.material_ids == "MAT-CUSTOM-X").sum()) > 0


def test_material_polygon_vertex_insert_and_remove_are_topology_safe() -> None:
    vertices = [[0.0, 0.8], [1.0, 0.8], [1.0, 1.2], [0.0, 1.2]]
    inserted, index = insert_material_region_vertex(vertices, edge_index=0)
    assert index == 1
    assert inserted[index] == [0.5, 0.8]
    assert len(inserted) == 5
    restored = remove_material_region_vertex(inserted, index)
    assert restored == vertices


def test_material_polygon_cannot_delete_below_three_vertices() -> None:
    from ucd.calculations.installation import InstallationInputError
    try:
        remove_material_region_vertex([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], 1)
    except InstallationInputError:
        pass
    else:
        raise AssertionError("Üç köşeli polygon silme kapısı hata üretmeliydi")


def test_ui_contract_contains_vertex_contour_material_id_and_engineering_export() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "_MaterialVertexHandleItem" in dialog
    assert "materialRegionVertexMoved = Signal" in dialog
    assert "Köşe Ekle" in dialog
    assert "Seçili Köşeyi Sil" in dialog
    assert "Malzeme ID" in dialog
    assert "Konturu Hesapla" in dialog
    assert "Kesit Çıktısı" in dialog
    assert "export_png" in dialog
    assert "_objects.csv" in dialog
    assert "_model.json" in dialog


def test_section_template_preserves_physical_ids_and_builds_duct_slots() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    original_ids = [item.physical_cable_id for item in section.physical_cables]
    templates = {item.template_id for item in built_in_cable_channel_templates()}
    assert "TPL-DUCT-2X3" in templates
    result = apply_cable_channel_template(
        section, "TPL-DUCT-2X3", cable_outer_diameter_m=project.cable.overall_diameter_mm / 1000.0
    )
    assert section.installation_type == "DUCT_BANK"
    assert [item.physical_cable_id for item in section.physical_cables] == original_ids
    assert result.moved_cable_count == len(original_ids)
    assert result.duct_slot_count == 6
    assigned = [item for item in section.physical_cables if item.active]
    assert all(item.duct_slot_id for item in assigned)
    slots = {item.slot_id: item for item in section.duct_slots}
    assert all(abs(item.x_m - slots[item.duct_slot_id].x_m) < 1e-12 for item in assigned)
    assert section.channel_geometry.source_reference == "USER_SECTION_TEMPLATE:TPL-DUCT-2X3"


def test_polygon_self_intersection_and_clearance_validation() -> None:
    assert polygon_self_intersects([[0.0, 0.0], [1.0, 1.0], [0.0, 1.0], [1.0, 0.0]]) is True
    assert polygon_self_intersects([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]) is False

    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    apply_cable_channel_template(section, "TPL-DUCT-2X3", cable_outer_diameter_m=0.105)
    section.duct_slots[1].x_m = section.duct_slots[0].x_m
    section.duct_slots[1].depth_m = section.duct_slots[0].depth_m
    section.duct_slots[0].inner_diameter_m = 0.09
    records = section_clearance_records(section, cable_outer_diameter_m=0.105)
    assert any(item.category == "DUCT_DUCT" and item.status == "FAIL" for item in records)
    assert any(item.category == "CABLE_DUCT_ANNULUS" and item.status == "FAIL" for item in records)
    codes = {item.code for item in validate_installation_design(project)}
    assert "DUCT_OVERLAP" in codes
    assert "CABLE_DOES_NOT_FIT_DUCT" in codes


def test_material_polygon_self_intersection_is_explicit_validation_error() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.material_regions.append(ThermalMaterialRegionData(
        "MR-X", "Kesişen polygon", "MAT-NATIVE-01",
        [[-0.5, 0.7], [0.5, 1.3], [-0.5, 1.3], [0.5, 0.7]],
    ))
    codes = {item.code for item in validate_installation_design(project)}
    assert "MATERIAL_REGION_SELF_INTERSECTION" in codes


def test_ui_contract_contains_templates_clearance_report_dimensions_and_result_labels() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "Section şablonu" in dialog
    assert "Şablonu Seçili Section'a Uygula" in dialog
    assert "Çakışma Raporu" in dialog
    assert "İnşaat ölçüleri" in dialog
    assert "Elektriksel ölçüler" in dialog
    assert "Kablo T/q" in dialog
    assert "_validation.csv" in dialog
    assert "show_result_labels" in dialog


def test_side_formation_selector_repositions_existing_cables_as_trefoil_without_overlap() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    # Two circuits and two parallels expose the old overlap failure.
    from ucd.models.project import InstallationCircuitData, PhysicalCableData
    section.circuits = [
        InstallationCircuitData("C1", "Devre 1", "ABC", 500.0),
        InstallationCircuitData("C2", "Devre 2", "ABC", 500.0),
    ]
    section.physical_cables = [
        PhysicalCableData(f"{circuit}-{phase}-{parallel}", circuit, phase, parallel, 0.0, 1.2)
        for circuit in ("C1", "C2")
        for parallel in (1, 2)
        for phase in "ABC"
    ]
    result = reposition_existing_cables(
        section, "TREFOIL", burial_depth_m=1.2, phase_spacing_m=0.07,
        circuit_spacing_m=0.40, parallel_spacing_m=0.10,
        cable_outer_diameter_m=0.105,
    )
    assert result.moved_cable_count == 12
    assert section.arrangement_label == "TREFOIL"
    for circuit in ("C1", "C2"):
        for parallel in (1, 2):
            group = [item for item in section.physical_cables if item.circuit_id == circuit and item.parallel_index == parallel]
            depths = {round(item.depth_m, 6) for item in group}
            assert len(depths) == 2  # one upper, two lower: actual trefoil, not flat
    clearances = section_clearance_records(section, cable_outer_diameter_m=0.105)
    assert not [item for item in clearances if item.category == "CABLE_CABLE" and item.status == "FAIL"]


def test_trefoil_template_uses_collision_safe_parallel_and_circuit_pitches() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    from ucd.models.project import InstallationCircuitData, PhysicalCableData
    section.circuits = [
        InstallationCircuitData("C1", "Devre 1", "ABC", 500.0),
        InstallationCircuitData("C2", "Devre 2", "ABC", 500.0),
    ]
    section.physical_cables = [
        PhysicalCableData(f"{circuit}-{phase}-{parallel}", circuit, phase, parallel, 0.0, 1.2)
        for circuit in ("C1", "C2")
        for parallel in (1, 2)
        for phase in "ABC"
    ]
    result = apply_cable_channel_template(section, "TPL-DB-TREFOIL-2C", cable_outer_diameter_m=0.105)
    assert section.arrangement_label == "TREFOIL"
    assert result.warning_messages  # requested template pitches are tightened only when needed
    clearances = section_clearance_records(section, cable_outer_diameter_m=0.105)
    assert not [item for item in clearances if item.category == "CABLE_CABLE" and item.status == "FAIL"]


def test_ui_contract_has_stable_fit_deferred_redraw_and_clear_contour_status() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "Kesite Sığdır" in dialog
    assert "_content_rect_for_section" in dialog
    assert "_queue_canvas_redraw" in dialog
    assert "QTimer.singleShot(0" in dialog
    assert "Gölge 2D önizleme" in dialog
    assert "reposition_existing_cables" in dialog
    assert "seçim tek başına uygulanmaz" in dialog


def test_kablo_kanal_canvas_is_read_only_and_all_geometry_is_panel_driven() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "self.setInteractive(False)" in dialog
    assert "self.setDragMode(QGraphicsView.ScrollHandDrag)" in dialog
    assert "Çizim salt okunur ve ölçeklidir" in dialog
    assert "Salt okunur ölçekli önizleme" in dialog
    assert "def mousePressEvent" in dialog and "super().mousePressEvent(event)" in dialog
    assert "if self._interactive_editing:" in dialog


def test_formation_selector_uses_turkish_display_and_stable_machine_codes() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert '"TREFOIL": "Üçgen formasyon (TREFOIL)"' in dialog
    assert '"FLAT": "Düz formasyon (FLAT)"' in dialog
    assert "self.preset_arrangement.addItem(FORMATION_DISPLAY[code], code)" in dialog
    assert "self.preset_arrangement.currentData()" in dialog
    assert "self.arrangement_edit.setReadOnly(True)" in dialog
    assert "Faz merkez aralığı [m] (FLAT/VERTICAL)" in dialog
    assert 'for code in ("TREFOIL", "FLAT", "VERTICAL", "CUSTOM")' in dialog
    assert 'for code in ("TREFOIL", "FLAT", "VERTICAL", "DUCT_BANK", "CUSTOM")' not in dialog


def test_bedding_backfill_and_native_soil_have_fixed_role_visuals() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    for key in (
        '"NATIVE_SOIL"', '"GENERAL_BACKFILL"', '"SELECTED_BACKFILL"',
        '"THERMAL_BACKFILL"', '"BEDDING_SAND"',
    ):
        assert key in dialog
    assert "Native soil / doğal zemin" in dialog
    assert "General backfill / üst dolgu" in dialog
    assert "Thermal backfill / kablo çevresi" in dialog
    assert "Bedding sand / yatak kumu" in dialog
    assert "Material IDs are communicated by labels" in dialog


def test_canvas_uses_physical_cable_and_duct_diameters_without_large_fake_minimums() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "max(self._diameter_m * self.scale_px_m, 3.0)" in dialog
    assert "max(slot.outer_diameter_m * self.scale_px_m, 3.0)" in dialog
    assert "çizimde gerçek ölçek" in dialog


def test_ui_contract_duct_bank_is_immediate_scaled_and_layers_are_explicit() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "self._schedule_layout_regeneration()" in dialog
    assert "inner_diameter_px" in dialog
    assert "Hendek katmanları — üstten alta" in dialog
    assert "Katman renklerini sıfırla" in dialog
    assert "Detay yazıları" in dialog
    assert "DUCT BANK / GROUT" in dialog
    assert "Duct kapasitesi" in dialog



def test_direct_buried_bedding_envelope_uses_real_cable_diameter_and_covers() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.installation_type = "DIRECT_BURIED"
    section.arrangement_label = "TREFOIL"
    g = section.channel_geometry
    g.trench_depth_m = 1.50
    g.bedding_bottom_cover_m = 0.10
    g.bedding_top_cover_m = 0.10
    g.bedding_side_clearance_m = 0.12
    g.cable_group_bottom_locked = True
    diameter = project.cable.overall_diameter_mm / 1000.0
    envelope = synchronise_direct_buried_geometry(section, diameter)
    assert abs(envelope.bedding_bottom_m - g.trench_depth_m) < 1e-12
    assert abs(g.bedding_thickness_m - (g.trench_depth_m - envelope.bedding_top_m)) < 1e-12
    assert abs(g.trench_depth_m - envelope.cable_bottom_m - g.bedding_bottom_cover_m) < 1e-12
    assert abs(envelope.cable_top_m - envelope.bedding_top_m - g.bedding_top_cover_m) < 1e-12
    assert g.trench_width_m + 1e-12 >= envelope.required_bottom_width_m


def test_direct_buried_warning_depths_are_referenced_to_sand_envelope() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.installation_type = "DIRECT_BURIED"
    g = section.channel_geometry
    g.trench_depth_m = 1.40
    g.warning_mesh_enabled = True
    g.warning_tape_enabled = True
    g.warning_mesh_offset_above_bedding_m = 0.20
    g.warning_tape_offset_above_bedding_m = 0.30
    diameter = project.cable.overall_diameter_mm / 1000.0
    synchronise_direct_buried_geometry(section, diameter)
    envelope = direct_buried_envelope(section, diameter)
    mesh, tape = direct_buried_warning_depths(section, diameter)
    assert mesh is not None and tape is not None
    assert abs(mesh - max(0.02, envelope.bedding_top_m - 0.20)) < 1e-12
    assert abs(tape - max(0.02, envelope.bedding_top_m - 0.30)) < 1e-12


def test_new_trench_construction_fields_round_trip_without_schema_break() -> None:
    project = ProjectData()
    g = project.installation_design.cross_sections[0].channel_geometry
    g.bedding_bottom_cover_m = 0.12
    g.bedding_top_cover_m = 0.15
    g.bedding_side_clearance_m = 0.18
    g.warning_mesh_enabled = False
    g.warning_tape_offset_above_bedding_m = 0.35
    g.spacer_enabled = True
    g.spacer_width_m = 0.09
    loaded = ProjectData.from_dict(project.to_dict())
    restored = loaded.installation_design.cross_sections[0].channel_geometry
    assert restored.bedding_bottom_cover_m == 0.12
    assert restored.bedding_top_cover_m == 0.15
    assert restored.bedding_side_clearance_m == 0.18
    assert restored.warning_mesh_enabled is False
    assert restored.warning_tape_offset_above_bedding_m == 0.35
    assert restored.spacer_enabled is True
    assert restored.spacer_width_m == 0.09


def test_ui_contract_has_parametric_sand_envelope_warning_system_spacers_and_real_layers() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert "Kablo altı yatak kumu" in dialog
    assert "En üst kablo üstü kum" in dialog
    assert "Uyarı ağı etkin" in dialog
    assert "Uyarı bandı etkin" in dialog
    assert "Düz formasyonda spacer/bims göster" in dialog
    assert "_draw_warning_system" in dialog
    assert "_draw_flat_spacers" in dialog
    assert "_cable_layer_specs" in dialog
    assert "Gerçek kablo dış çapı" in dialog


def _pairwise_phase_distances(section, circuit_id="C1", parallel_index=1):
    from math import hypot
    by_phase = {
        item.phase: item
        for item in section.physical_cables
        if item.circuit_id == circuit_id and item.parallel_index == parallel_index
    }
    return tuple(
        hypot(by_phase[a].x_m - by_phase[b].x_m, by_phase[a].depth_m - by_phase[b].depth_m)
        for a, b in (("A", "B"), ("B", "C"), ("C", "A"))
    )


def test_trefoil_global_phase_spacing_is_locked_to_real_outer_diameter() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    diameter = 0.105

    reposition_existing_cables(
        section, "TREFOIL", burial_depth_m=1.2, phase_spacing_m=0.07,
        circuit_spacing_m=0.80, parallel_spacing_m=0.25,
        cable_outer_diameter_m=diameter,
    )
    first = {
        item.physical_cable_id: (item.x_m, item.depth_m)
        for item in section.physical_cables
    }
    reposition_existing_cables(
        section, "TREFOIL", burial_depth_m=1.2, phase_spacing_m=0.80,
        circuit_spacing_m=0.80, parallel_spacing_m=0.25,
        cable_outer_diameter_m=diameter,
    )
    second = {
        item.physical_cable_id: (item.x_m, item.depth_m)
        for item in section.physical_cables
    }

    assert second == first
    assert all(abs(distance - diameter) < 1e-12 for distance in _pairwise_phase_distances(section))


def test_trefoil_generated_cross_section_ignores_user_phase_spacing() -> None:
    from ucd.calculations.installation import generate_standard_cross_section

    diameter = 0.105
    section = generate_standard_cross_section(
        cross_section_id="ICS-TREFOIL-CONTACT",
        name="Trefoil temas testi",
        arrangement="TREFOIL",
        circuit_count=1,
        parallel_cables_per_phase=1,
        phase_spacing_m=0.90,
        outer_diameter_m=diameter,
    )
    assert all(abs(distance - diameter) < 1e-12 for distance in _pairwise_phase_distances(section))


def test_ui_hides_global_trefoil_spacing_and_locks_per_circuit_cell() -> None:
    dialog = (ROOT / "src" / "ucd" / "ui" / "installation_designer_dialog.py").read_text(encoding="utf-8")
    assert 'phase_spacing_active = arrangement in {"FLAT", "VERTICAL"}' in dialog
    assert 'duct_active = bool(section and str(section.installation_type).upper() == THERMAL_INSTALL_DUCT_BANK)' in dialog
    assert "def _update_circuit_phase_spacing_cell" in dialog
    assert 'if arrangement == "TREFOIL":' in dialog
    assert "item.setFlags(item.flags() & ~Qt.ItemIsEditable)" in dialog
    assert "faz merkez mesafesi otomatik olarak gerçek kablo dış çapına eşittir" in dialog
