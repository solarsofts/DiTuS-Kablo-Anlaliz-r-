from __future__ import annotations

import math

from ucd.calculations.iec60287 import CalculationInputError, dc_resistance_20_ohm_km, solve_section
from ucd.models.project import CableData, RouteSection


def test_copper_resistance_from_area() -> None:
    cable = CableData(conductor_material="Cu", conductor_area_mm2=1200.0, dc_resistance_20_ohm_km=0.0)
    assert math.isclose(dc_resistance_20_ohm_km(cable), 0.0143675, rel_tol=1e-8)


def test_rating_and_inverse_temperature_are_consistent() -> None:
    cable = CableData(design_current_a=1000.0)
    section = RouteSection("Test", 100.0, ambient_temperature_c=25.0, external_thermal_resistance_t4_km_w=0.85)
    result = solve_section(cable, section)
    assert result.ampacity_a > 1000.0
    at_rating = CableData(**{**cable.__dict__, "design_current_a": result.ampacity_a})
    result_at_rating = solve_section(at_rating, section)
    assert math.isclose(result_at_rating.conductor_temperature_at_design_c, cable.max_temperature_c, abs_tol=1e-8)


def test_hot_section_is_more_limiting() -> None:
    cable = CableData(design_current_a=900.0)
    cool = solve_section(cable, RouteSection("Cool", 1.0, ambient_temperature_c=20.0, external_thermal_resistance_t4_km_w=0.8))
    hot = solve_section(cable, RouteSection("Hot", 1.0, ambient_temperature_c=35.0, external_thermal_resistance_t4_km_w=1.2))
    assert hot.ampacity_a < cool.ampacity_a


def test_invalid_temperature_margin() -> None:
    cable = CableData(max_temperature_c=25.0)
    section = RouteSection("Invalid", 1.0, ambient_temperature_c=25.0)
    try:
        solve_section(cable, section)
    except CalculationInputError:
        pass
    else:
        raise AssertionError("CalculationInputError expected")
