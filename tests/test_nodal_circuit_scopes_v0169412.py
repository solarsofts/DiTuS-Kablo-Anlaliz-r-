from __future__ import annotations

from pathlib import Path

from ucd.calculations.installation import generate_standard_cross_section
from ucd.calculations.nodal_thermal import solve_nodal_region, solve_nodal_route
from ucd.calculations.thermal_route import solve_thermal_route
from ucd.models.project import ProjectData


ROOT = Path(__file__).resolve().parents[1]


def _two_circuit_project() -> ProjectData:
    project = ProjectData()
    section = generate_standard_cross_section(
        cross_section_id="ICS-2C-THERMAL",
        name="İki devre ortak kanal",
        arrangement="TREFOIL",
        circuit_count=2,
        parallel_cables_per_phase=1,
        phase_orders=["ABC", "ABC"],
        circuit_load_currents_a=[800.0, 800.0],
        phase_spacing_m=0.105,
        circuit_spacing_m=0.45,
        burial_depth_m=1.20,
        outer_diameter_m=0.105,
    )
    section.region_ids = ["TR-01"]
    section.channel_geometry.trench_width_m = 1.40
    project.installation_design.cross_sections = [section]
    project.installation_design.active_cross_section_id = section.cross_section_id
    project.design_basis.active_circuit_count = 1
    # Keep regression fast without changing the physical scope behaviour.
    project.thermal_design.regions[0].overrides.update({
        "nodal_base_step_m": 0.30,
        "nodal_refined_step_m": 0.08,
    })
    return project


def test_route_exposes_combined_and_per_circuit_thermal_scopes() -> None:
    project = _two_circuit_project()
    study = solve_nodal_route(project)
    scopes = {
        item.solution_scope_id: item
        for item in study.scopes_for_scenario(study.active_scenario_id)
    }

    assert {
        "SCENARIO_COMBINED",
        "ALL_CIRCUITS_COMBINED",
        "ISOLATED::C1",
        "ISOLATED::C2",
    }.issubset(scopes)
    for scope in scopes.values():
        region = scope.regions[0]
        assert len(region.cables) == 6
        assert region.present_circuit_count == 2

    all_combined = scopes["ALL_CIRCUITS_COMBINED"].regions[0]
    isolated_c1 = scopes["ISOLATED::C1"].regions[0]
    assert all_combined.active_circuit_count == 2
    assert isolated_c1.active_circuit_count == 1
    assert all_combined.maximum_conductor_temperature_c > isolated_c1.maximum_conductor_temperature_c

    c2_passive = [item for item in isolated_c1.cables if item.circuit_index == 2]
    assert c2_passive
    assert all(item.current_a == 0.0 and item.total_loss_w_m == 0.0 for item in c2_passive)


def test_scenario_scope_keeps_nonenergized_circuit_as_passive_thermal_body() -> None:
    project = _two_circuit_project()
    iec = solve_thermal_route(project).active.regions[0].iec
    result = solve_nodal_region(
        project,
        "TR-01",
        800.0,
        1,
        0.05,
        iec,
        calculate_ampacity=False,
        energized_circuit_ids=("C1",),
        solution_scope_id="ISOLATED::C1",
        solution_scope_name="Yalnız C1 enerjili",
    )

    assert result.present_circuit_count == 2
    assert result.active_circuit_count == 1
    assert len(result.cables) == 6
    assert {item.circuit_index for item in result.cables} == {1, 2}
    assert all(item.current_a == 0.0 for item in result.cables if item.circuit_index == 2)
    assert any("pasif ısıl cisim" in item for item in result.warnings)


def test_empty_duct_slots_are_preserved_in_nodal_material_map() -> None:
    project = ProjectData()
    section = generate_standard_cross_section(
        cross_section_id="ICS-DUCT-EMPTY",
        name="Boş slotlu duct bank",
        arrangement="DUCT_BANK",
        circuit_count=1,
        parallel_cables_per_phase=1,
        duct_rows=2,
        duct_columns=3,
        circuit_load_currents_a=[600.0],
        burial_depth_m=1.35,
        phase_spacing_m=0.22,
        outer_diameter_m=0.10,
    )
    section.region_ids = ["TR-01"]
    section.channel_geometry.trench_width_m = 1.60
    project.installation_design.cross_sections = [section]
    project.installation_design.active_cross_section_id = section.cross_section_id
    project.thermal_design.regions[0].overrides.update({
        "nodal_base_step_m": 0.25,
        "nodal_refined_step_m": 0.06,
    })

    occupied = {item.duct_slot_id for item in section.physical_cables}
    empty_slot = next(item for item in section.duct_slots if item.slot_id not in occupied)
    iec = solve_thermal_route(project).active.regions[0].iec
    result = solve_nodal_region(
        project, "TR-01", 600.0, 1, 0.05, iec, calculate_ampacity=False
    )

    x_centres = [
        (result.x_edges_m[index] + result.x_edges_m[index + 1]) / 2.0
        for index in range(len(result.x_edges_m) - 1)
    ]
    y_centres = [
        (result.depth_edges_m[index] + result.depth_edges_m[index + 1]) / 2.0
        for index in range(len(result.depth_edges_m) - 1)
    ]
    ix = min(range(len(x_centres)), key=lambda index: abs(x_centres[index] - empty_slot.x_m))
    iy = min(range(len(y_centres)), key=lambda index: abs(y_centres[index] - empty_slot.depth_m))
    assert result.material_ids[iy][ix] == "MAT-AIR-01"
    assert any("kanal katmanları" in item for item in result.trace)


def test_ui_contract_exposes_scope_selector_and_channel_geometry_overlays() -> None:
    main_window = (ROOT / "src" / "ucd" / "ui" / "main_window.py").read_text(encoding="utf-8")
    graphics = (ROOT / "src" / "ucd" / "ui" / "graphics_views.py").read_text(encoding="utf-8")

    assert "Çözüm kapsamı" in main_window
    assert "Kanalın tüm devreleri birlikte" in main_window
    assert "Yalnız Cx enerjili" in main_window
    assert "duct_slots" in main_window
    assert "Kanal / katman / duct geometrisi" in main_window
    assert "trench_side_slope_h_to_v" in graphics
    assert "Duct bank / grout fiziksel sınırı" in graphics
    assert "Yataklama / kum zarfı üst sınırı" in graphics
