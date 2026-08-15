from __future__ import annotations

from copy import deepcopy

import pytest

from ucd.calculations.installation import generate_standard_cross_section
from ucd.calculations.multiconductor_bonding_network import (
    CORE_SHARING_MODE,
    MulticonductorBondingInputError,
    solve_multiconductor_bonding_network,
)
from ucd.models.project import (
    InstallationDesignData,
    ProjectData,
    RouteSection,
    default_bonding_system,
)


def _two_circuit_project() -> ProjectData:
    project = ProjectData()
    section = generate_standard_cross_section(
        cross_section_id="ICS-NET",
        name="İki devre iki paralel bonding ağı",
        arrangement="FLAT",
        circuit_count=2,
        parallel_cables_per_phase=2,
        phase_orders=["ABC", "CBA"],
        circuit_load_currents_a=[900.0, 600.0],
        phase_spacing_m=0.25,
        circuit_spacing_m=1.60,
        parallel_group_spacing_m=0.80,
        burial_depth_m=1.25,
        outer_diameter_m=0.105,
        region_ids=["TR-NET"],
    )
    project.installation_design = InstallationDesignData(
        active_cross_section_id=section.cross_section_id,
        cross_sections=[section],
        solver_coupling_mode="DESIGN_ONLY",
        model_revision="0.16.4",
    )
    project.route_sections = [
        RouteSection("R-NET", 300.0, thermal_region_id="TR-NET"),
    ]
    project.bonding = default_bonding_system(300.0)
    return project


def test_default_network_solves_three_minor_sections_by_two_methods() -> None:
    result = solve_multiconductor_bonding_network(ProjectData())
    assert result.core_sharing_mode == CORE_SHARING_MODE
    assert result.methods_agree
    assert len(result.section_results) == 3
    assert len(result.sheath_order) == 3
    assert result.cim.equation_residual < 1e-10
    assert result.nv.equation_residual < 1e-9
    assert result.maximum_method_current_difference_a < 1e-8
    assert result.maximum_sheath_current_a > 0.0
    assert result.maximum_sheath_to_earth_voltage_v > 0.0
    assert result.maximum_sheath_to_sheath_voltage_v > 0.0
    assert result.lambda1 > 0.0
    assert result.final_design_ready is False


def test_route_regions_select_distinct_physical_cross_sections() -> None:
    project = ProjectData()
    result = solve_multiconductor_bonding_network(project)
    used = {block.cross_section_id for block in result.matrix_blocks}
    assert {"ICS-01", "ICS-02", "ICS-03"}.issubset(used)
    final = result.section_results[-1]
    assert final.route_cross_sections == ("ICS-01", "ICS-02", "ICS-03")


def test_two_circuit_two_parallel_builds_separate_sheath_paths() -> None:
    result = solve_multiconductor_bonding_network(_two_circuit_project())
    assert result.methods_agree
    assert len(result.sheath_order) == 12
    assert len(result.section_results) == 3
    assert all(len(item.sheath_results) == 12 for item in result.section_results)
    cross = [item for item in result.accessory_branches if item.branch_type == "CROSS_LINK"]
    assert len(cross) == 24  # 12 physical sheaths at each of two link boxes
    ids = {item.branch_id for item in cross}
    assert "LINK:J1:C1:A:P1>C1:B:P1" in ids
    assert "LINK:J2:C2:C:P2>C2:A:P2" in ids
    assert result.maximum_sheath_current_a > 0.0
    assert result.total_sheath_metal_loss_w > 0.0


def test_link_box_mapping_preserves_circuit_and_parallel_identity() -> None:
    result = solve_multiconductor_bonding_network(_two_circuit_project())
    for item in result.accessory_branches:
        if item.branch_type != "CROSS_LINK":
            continue
        body = item.branch_id.split("LINK:", 1)[1]
        _joint, mapping = body.split(":", 1)
        source, target = mapping.split(">", 1)
        sc, _sp, spi = source.split(":")
        tc, _tp, tpi = target.split(":")
        assert sc == tc
        assert spi == tpi


def test_optional_gcc_runs_through_minor_section_network() -> None:
    project = _two_circuit_project()
    project.bonding.gcc_enabled = True
    result = solve_multiconductor_bonding_network(project)
    assert result.methods_agree
    assert result.maximum_gcc_current_a > 0.0
    assert result.total_gcc_metal_loss_w >= 0.0
    assert any(item.branch_type == "GCC_LINK" for item in result.accessory_branches)


def test_shadow_network_does_not_mutate_project_or_lambda1() -> None:
    project = _two_circuit_project()
    before = deepcopy(project.to_dict())
    lambda_before = project.cable.sheath_loss_factor
    result = solve_multiconductor_bonding_network(project)
    assert result.lambda1 > 0.0
    assert project.cable.sheath_loss_factor == lambda_before
    assert project.to_dict() == before


def test_route_key_change_is_rejected_instead_of_silent_remapping() -> None:
    project = ProjectData()
    # The final route resolves to ICS-03. Remove one active physical cable there.
    project.installation_design.cross_sections[2].physical_cables[-1].active = False
    with pytest.raises(MulticonductorBondingInputError, match="fiziksel kablo anahtarları değişiyor"):
        solve_multiconductor_bonding_network(project)


def test_network_ui_contract_is_additive_and_shadow_only() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    dialog = (root / "src/ucd/ui/multiconductor_em_dialog.py").read_text(encoding="utf-8")
    main = (root / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    assert "N-İletken Bonding Ağını Çalıştır" in dialog
    assert "SHADOW_COMPARE" in dialog
    assert "Genel N-İletken EM Gölge Çözümü" in main
    assert "self.act_bonding" in main


def test_single_circuit_geometry_projected_input_matches_locked_primitive_network() -> None:
    from ucd.calculations.installation_coupling import project_with_synchronized_installation_geometry
    from ucd.calculations.primitive_cim import solve_primitive_network

    # The physical TREFOIL is now touching (OD pitch), while the untouched
    # legacy scalar default is 0.15 m. Compare both kernels only after the
    # central adapter has supplied the same geometry-dependent input.
    project = project_with_synchronized_installation_geometry(ProjectData())
    new = solve_multiconductor_bonding_network(project)
    legacy = solve_primitive_network(project.cable, project.bonding, project.route_sections)
    assert new.maximum_sheath_current_a == pytest.approx(legacy.maximum_sheath_current_a, rel=1e-10, abs=1e-10)
    assert new.maximum_sheath_to_earth_voltage_v == pytest.approx(legacy.maximum_sheath_voltage_v, rel=1e-10, abs=1e-10)
    assert new.total_sheath_metal_loss_w == pytest.approx(legacy.total_sheath_metal_loss_w, rel=1e-10, abs=1e-10)
    for new_section, old_section in zip(new.section_results, legacy.section_results):
        assert new_section.maximum_sheath_current_a == pytest.approx(old_section.max_sheath_current_a, rel=1e-10, abs=1e-10)
        assert new_section.maximum_sheath_to_earth_voltage_v == pytest.approx(old_section.max_sheath_voltage_v, rel=1e-10, abs=1e-10)
