from __future__ import annotations

from copy import deepcopy
from math import isclose

import pytest

from ucd.calculations.cable_physical_parameters import (
    PhysicalParameterInputError,
    resolve_ac_resistance_at_temperature,
    resolve_construction_coefficients,
)
from ucd.calculations.iec60287 import solve_section
from ucd.models.project import CableData, RouteSection


def _al_compact() -> CableData:
    return CableData(
        conductor_material="Al",
        conductor_area_mm2=400.0,
        conductor_diameter_mm=24.0,
        conductor_stranding_type="COMPACT_ROUND",
        conductor_shape="ROUND",
        conductor_insulation_system="EXTRUDED",
        dc_resistance_20_ohm_km=0.0778,
        frequency_hz=50.0,
        skin_effect_factor=0.025,
        proximity_effect_factor=0.015,
        design_current_a=300.0,
        max_temperature_c=90.0,
    )


def test_compact_round_alias_resolves_construction_coefficients() -> None:
    """Desteklenen klasik konstrüksiyon katsayısı standard resolver'ından gelir."""

    result = resolve_construction_coefficients(_al_compact())
    assert result.supported
    assert result.ks == 1.0
    assert result.kp == 0.8
    assert result.source == "IEC_60287_1_1_TABLE_2"


def test_physical_rac_uses_iec_ks_kp_not_legacy_ys_yp() -> None:
    cable = _al_compact()
    result = resolve_ac_resistance_at_temperature(cable, 90.0, phase_spacing_m=0.105)
    assert not result.used_legacy_fallback
    assert result.ks == 1.0 and result.kp == 0.8
    assert result.ys > 0.0 and result.yp > 0.0
    legacy = result.rdc_temperature_ohm_km * (1.0 + cable.skin_effect_factor + cable.proximity_effect_factor)
    assert not isclose(result.ac_resistance_ohm_km, legacy, rel_tol=1e-6)
    assert any("IEC_60287_CONSTRUCTION_RESOLVER" in line for line in result.trace)


def test_proximity_factor_responds_to_actual_phase_spacing() -> None:
    cable = _al_compact()
    close = resolve_ac_resistance_at_temperature(cable, 90.0, phase_spacing_m=0.075)
    far = resolve_ac_resistance_at_temperature(cable, 90.0, phase_spacing_m=0.300)
    assert isclose(close.ys, far.ys, rel_tol=1e-12)
    assert close.yp > far.yp > 0.0
    assert close.ac_resistance_ohm_km > far.ac_resistance_ohm_km


def test_user_supplied_milliken_pair_materially_changes_skin_effect() -> None:
    """Milliken katsayısı artık kullanıcı girdisidir; girildiğinde fizik aynen çalışır."""

    cable = CableData(
        conductor_material="Cu",
        conductor_area_mm2=1200.0,
        conductor_diameter_mm=40.0,
        conductor_stranding_type="MILLIKEN",
        milliken_wire_profile="BARE_BIDIRECTIONAL",
        skin_effect_coefficient_ks=0.80,
        proximity_effect_coefficient_kp=0.37,
        dc_resistance_20_ohm_km=0.0151,
        frequency_hz=50.0,
    )
    result = resolve_ac_resistance_at_temperature(cable, 90.0, phase_spacing_m=0.105)
    assert result.ks == 0.80
    assert result.kp == 0.37
    assert result.ys > 0.10
    assert result.ac_resistance_ohm_km > result.rdc_temperature_ohm_km * 1.10


def test_physical_rac_remains_valid_below_20_c() -> None:
    cable = _al_compact()
    cold = resolve_ac_resistance_at_temperature(cable, 5.0, phase_spacing_m=0.105)
    warm = resolve_ac_resistance_at_temperature(cable, 20.0, phase_spacing_m=0.105)
    assert cold.ac_resistance_ohm_km > 0.0
    assert cold.ac_resistance_ohm_km < warm.ac_resistance_ohm_km


def test_missing_cu_milliken_profile_is_explicit_fallback_or_strict_error() -> None:
    cable = CableData(
        conductor_material="Cu",
        conductor_stranding_type="MILLIKEN",
        conductor_insulation_system="EXTRUDED",
        milliken_wire_profile="UNKNOWN",
        dc_resistance_20_ohm_km=0.02,
        conductor_diameter_mm=35.0,
    )
    fallback = resolve_ac_resistance_at_temperature(cable, 90.0, phase_spacing_m=0.120)
    assert fallback.used_legacy_fallback
    assert any("MILLIKEN_PROFILE_REQUIRED" in line for line in fallback.trace)
    assert any("LEGACY_YS_YP_FALLBACK" in line for line in fallback.trace)
    with pytest.raises(PhysicalParameterInputError, match="MILLIKEN_PROFILE_REQUIRED"):
        resolve_ac_resistance_at_temperature(
            cable, 90.0, phase_spacing_m=0.120, allow_legacy_fallback=False
        )


def test_iec_section_result_is_independent_of_legacy_ys_yp_when_construction_resolves() -> None:
    cable = _al_compact()
    section = RouteSection(
        "IEC physical Rac",
        1.0,
        ambient_temperature_c=20.0,
        burial_depth_m=1.0,
        phase_spacing_m=0.105,
        soil_thermal_resistivity_km_w=1.0,
    )
    first = solve_section(cable, section)
    altered = deepcopy(cable)
    altered.skin_effect_factor = 0.35
    altered.proximity_effect_factor = 0.25
    second = solve_section(altered, section)
    assert isclose(first.ac_resistance_ohm_km, second.ac_resistance_ohm_km, rel_tol=1e-12)
    assert isclose(first.ampacity_a, second.ampacity_a, rel_tol=1e-12)
    assert isclose(first.conductor_temperature_at_design_c, second.conductor_temperature_at_design_c, rel_tol=1e-10)
    assert any("ks/kp=1.000000/0.800000" in line for line in first.thermal_trace)


def test_design_temperature_satisfies_nonlinear_rac_fixed_point() -> None:
    cable = _al_compact()
    cable.design_current_a = 450.0
    section = RouteSection(
        "Nonlinear Rac",
        1.0,
        ambient_temperature_c=15.0,
        burial_depth_m=1.0,
        phase_spacing_m=0.105,
        soil_thermal_resistivity_km_w=1.0,
    )
    result = solve_section(cable, section)
    assert result.ac_resistance_at_design_ohm_km > 0.0
    assert result.conductor_temperature_at_design_c > section.ambient_temperature_c
    assert result.conductor_temperature_at_design_c < 400.0
