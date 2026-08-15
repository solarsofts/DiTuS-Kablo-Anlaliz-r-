from __future__ import annotations

from copy import deepcopy

import pytest

from ucd.calculations.iec60287 import CalculationInputError, solve_section
from ucd.calculations.multiconductor_thermal import solve_multiconductor_thermal
from ucd.calculations.production_electrothermal import solve_production_electrothermal_study
from ucd.calculations.soil_dryout import SoilDryoutInputError, material_dryout_profile
from ucd.models.project import ProjectData, RouteSection, ThermalMaterialData


def _dryout_material(material: ThermalMaterialData, *, critical: float = 45.0, dry_rho: float = 2.5) -> None:
    material.critical_dryout_temperature_c = critical
    material.dry_state_thermal_resistivity_km_w = dry_rho
    material.data_state = "TESTED"
    material.source_reference = "Synthetic dryout regression"


def test_dryout_material_requires_complete_pair_and_higher_dry_rho() -> None:
    material = ThermalMaterialData("M", "soil", thermal_resistivity_km_w=1.0)
    material.critical_dryout_temperature_c = 45.0
    with pytest.raises(SoilDryoutInputError):
        material_dryout_profile(material)
    material.dry_state_thermal_resistivity_km_w = 0.8
    with pytest.raises(SoilDryoutInputError):
        material_dryout_profile(material)
    material.dry_state_thermal_resistivity_km_w = 2.0
    resolved = material_dryout_profile(material)
    assert resolved is not None
    assert resolved.resistivity_ratio == pytest.approx(2.0)


def test_simple_isolated_iec_two_zone_dryout_reduces_ampacity() -> None:
    project = ProjectData()
    cable = deepcopy(project.cable)
    cable.arrangement = "Single"
    cable.design_current_a = 300.0
    wet = RouteSection(
        "wet", 100.0, burial_depth_m=1.0, soil_thermal_resistivity_km_w=1.0,
        phase_spacing_m=0.2, ambient_temperature_c=25.0,
    )
    dry = deepcopy(wet)
    dry.name = "dry"
    dry.soil_critical_dryout_temperature_c = 35.0
    dry.soil_dry_state_thermal_resistivity_km_w = 2.5
    dry.soil_dryout_data_state = "TESTED"
    wet_result = solve_section(cable, wet)
    dry_result = solve_section(cable, dry)
    assert dry_result.ampacity_a < wet_result.ampacity_a
    assert any("iki-bölge kuruma" in line.lower() for line in dry_result.thermal_trace)


def test_analytical_dryout_rejects_multi_cable_mutual_geometry() -> None:
    project = ProjectData()
    cable = deepcopy(project.cable)
    cable.arrangement = "Trefoil"
    section = RouteSection(
        "dry-trefoil", 100.0, burial_depth_m=1.0, soil_thermal_resistivity_km_w=1.0,
        phase_spacing_m=0.2, ambient_temperature_c=25.0,
        soil_critical_dryout_temperature_c=45.0,
        soil_dry_state_thermal_resistivity_km_w=2.5,
    )
    with pytest.raises(CalculationInputError, match="ANALYTIC_DRYOUT_REQUIRES_NODAL"):
        solve_section(cable, section)


def test_nodal_critical_isotherm_dryout_increases_temperature_and_marks_cells() -> None:
    wet = ProjectData()
    dry = deepcopy(wet)
    native_id = dry.thermal_design.templates[0].native_soil_material_id
    native = next(item for item in dry.thermal_design.materials if item.material_id == native_id)
    _dryout_material(native, critical=30.0, dry_rho=max(2.5, native.thermal_resistivity_km_w * 2.0))
    wet_result = solve_multiconductor_thermal(wet, mesh_scale=2.8, max_iterations=20, tolerance_c=0.08)
    dry_result = solve_multiconductor_thermal(dry, mesh_scale=2.8, max_iterations=20, tolerance_c=0.08)
    dry_regions = [item for item in dry_result.regions if item.dryout_enabled]
    assert dry_regions
    assert any(item.dryout_cell_count > 0 for item in dry_regions)
    assert all(item.dryout_converged for item in dry_regions)
    assert dry_result.maximum_nodal_conductor_temperature_c > wet_result.maximum_nodal_conductor_temperature_c


def test_groundwater_cells_are_not_marked_dry() -> None:
    project = ProjectData()
    native_id = project.thermal_design.templates[0].native_soil_material_id
    native = next(item for item in project.thermal_design.materials if item.material_id == native_id)
    _dryout_material(native, critical=30.0, dry_rho=max(2.5, native.thermal_resistivity_km_w * 2.0))
    for template in project.thermal_design.templates:
        template.groundwater_depth_m = 0.05
    result = solve_multiconductor_thermal(project, mesh_scale=3.0, max_iterations=15, tolerance_c=0.1)
    regions = [item for item in result.regions if item.dryout_enabled]
    assert regions
    assert all(item.dryout_cell_count == 0 for item in regions)


def test_production_auto_switches_to_nodal_when_dryout_data_exist() -> None:
    project = ProjectData()
    native_id = project.thermal_design.templates[0].native_soil_material_id
    native = next(item for item in project.thermal_design.materials if item.material_id == native_id)
    _dryout_material(native, critical=30.0, dry_rho=max(2.5, native.thermal_resistivity_km_w * 2.0))
    study = solve_production_electrothermal_study(project, maximum_iterations=5)
    assert study.scenarios
    assert all(item.coupled_result is None or item.coupled_result.thermal_method == "NODAL" for item in study.scenarios)
    assert all(any("dryout_materials=" in line for line in item.trace) for item in study.scenarios)
