from __future__ import annotations

from copy import deepcopy
from math import isclose, log, pi

from ucd.calculations.cable_physical_parameters import (
    geometric_capacitance_uf_km,
    resolve_construction_coefficients,
    run_project_physical_parameter_study,
    solve_cable_physical_parameters,
)
from ucd.models.project import CableData, ProjectData, RouteSection


def test_iec_skin_proximity_reference_example() -> None:
    cable = CableData(
        conductor_stranding_type="SOLID",
        conductor_shape="ROUND",
        conductor_area_mm2=630.0,
        conductor_diameter_mm=30.3,
        dc_resistance_20_ohm_km=0.0283,
        temperature_coefficient_20_per_c=0.00393,
        skin_effect_coefficient_ks=1.0,
        proximity_effect_coefficient_kp=1.0,
    )
    section = RouteSection("Reference", 1.0, phase_spacing_m=0.500)
    result = solve_cable_physical_parameters(cable, section, target_temperature_c=90.0)

    assert result.supported_for_ac_resistance
    assert isclose(result.xs, 1.8661201029, rel_tol=1e-9)
    assert isclose(result.skin_effect_factor_ys, 0.0601241268, rel_tol=1e-8)
    assert isclose(result.proximity_effect_factor_yp, 0.0007894742385, rel_tol=1e-9)
    assert isclose(result.physical_ac_resistance_ohm_km, 0.0382834174, rel_tol=1e-8)


def test_milliken_standard_coefficients_resolve_for_supported_round_constructions() -> None:
    cases = [
        ("Al", "", "", (0.25, 0.15)),
        ("Cu", "FLUID_PAPER_PPL", "FLUID", (0.435, 0.37)),
        ("Cu", "INSULATED_WIRES", "EXTRUDED", (0.35, 0.20)),
        ("Cu", "BARE_UNIDIRECTIONAL", "EXTRUDED", (0.62, 0.37)),
        ("Cu", "BARE_BIDIRECTIONAL", "EXTRUDED", (0.80, 0.37)),
    ]
    for material, profile, insulation, expected in cases:
        cable = CableData(
            conductor_material=material,
            conductor_stranding_type="MILLIKEN",
            milliken_wire_profile=profile,
            conductor_insulation_system=insulation,
        )
        coefficients = resolve_construction_coefficients(cable)
        assert coefficients.supported, (material, profile, insulation)
        assert coefficients.source == "IEC_60287_1_1_TABLE_2"
        assert (coefficients.ks, coefficients.kp) == expected


def test_cu_milliken_missing_profile_fails_closed() -> None:
    cable = CableData(
        conductor_material="Cu",
        conductor_stranding_type="MILLIKEN",
        conductor_insulation_system="EXTRUDED",
    )
    coefficients = resolve_construction_coefficients(cable)
    assert not coefficients.supported
    assert coefficients.source == "MILLIKEN_PROFILE_REQUIRED"


def test_explicit_user_pair_overrides_milliken_resolver() -> None:
    cable = CableData(
        conductor_material="Cu",
        conductor_stranding_type="MILLIKEN",
        milliken_wire_profile="INSULATED_WIRES",
        skin_effect_coefficient_ks=0.36,
        proximity_effect_coefficient_kp=0.21,
    )
    coefficients = resolve_construction_coefficients(cable)
    assert coefficients.supported
    assert coefficients.source == "EXPLICIT_TRACEABLE_INPUT"
    assert (coefficients.ks, coefficients.kp) == (0.36, 0.21)


def test_unity_construction_coefficients_remain_standard_resolver_data() -> None:
    """ks = kp = 1 katsayı çifti fizik formülündeki standart konstrüksiyon girdisidir."""

    cable = CableData(conductor_material="Cu", conductor_stranding_type="SOLID")
    coefficients = resolve_construction_coefficients(cable)
    assert coefficients.supported
    assert coefficients.source == "IEC_60287_1_1_TABLE_2"
    assert (coefficients.ks, coefficients.kp) == (1.0, 1.0)


def test_geometric_capacitance_uses_main_insulation_layer() -> None:
    cable = ProjectData().cable
    insulation = next(layer for layer in cable.layers if layer.layer_type == "INSULATION")
    expected = (
        2.0 * pi * 8.8541878128e-12 * insulation.relative_permittivity
        / log(insulation.outer_diameter_mm / insulation.inner_diameter_mm)
        * 1.0e9
    )
    capacitance, trace = geometric_capacitance_uf_km(cable)
    assert isclose(capacitance, expected, rel_tol=1e-12)
    assert isclose(cable.capacitance_uf_km, expected, rel_tol=1e-12)
    assert "XLPE izolasyon" in trace


def test_shadow_study_does_not_mutate_locked_solver_scalars() -> None:
    project = ProjectData()
    project.cable.conductor_stranding_type = "SOLID"
    before = {
        "rdc": project.cable.dc_resistance_20_ohm_km,
        "ys": project.cable.skin_effect_factor,
        "yp": project.cable.proximity_effect_factor,
        "capacitance": project.cable.capacitance_uf_km,
        "sheath_rdc": project.cable.sheath_dc_resistance_20_ohm_km,
        "t1": project.cable.thermal_resistance_t1_km_w,
        "t2": project.cable.thermal_resistance_t2_km_w,
        "t3": project.cable.thermal_resistance_t3_km_w,
    }
    run_project_physical_parameter_study(project)
    after = {
        "rdc": project.cable.dc_resistance_20_ohm_km,
        "ys": project.cable.skin_effect_factor,
        "yp": project.cable.proximity_effect_factor,
        "capacitance": project.cable.capacitance_uf_km,
        "sheath_rdc": project.cable.sheath_dc_resistance_20_ohm_km,
        "t1": project.cable.thermal_resistance_t1_km_w,
        "t2": project.cable.thermal_resistance_t2_km_w,
        "t3": project.cable.thermal_resistance_t3_km_w,
    }
    assert before == after
    assert project.physical_parameter_study.last_result


def test_physical_parameter_study_round_trip() -> None:
    project = ProjectData()
    project.cable.conductor_stranding_type = "SOLID"
    result = run_project_physical_parameter_study(project)
    payload = deepcopy(project.to_dict())
    loaded = ProjectData.from_dict(payload)

    assert loaded.schema_version == "0.16.4"
    assert loaded.physical_parameter_study.model_revision == "0.16.4"
    assert loaded.physical_parameter_study.last_result["calculated_at"] == result.calculated_at
    assert loaded.cable.conductor_shape == "ROUND"
    assert loaded.cable.skin_effect_coefficient_ks == 0.0
