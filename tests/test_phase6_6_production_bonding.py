from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ucd.calculations.bonding import BondingInputError, sheath_resistance_ohm_km
from ucd.calculations.multiconductor_global_network import solve_global_multiconductor_network
from ucd.calculations.production_bonding import solve_production_bonding_study
from ucd.calculations.operating_scenarios import apply_operating_scenario, resolve_operating_scenarios
from ucd.models.project import ProjectData

ROOT = Path(__file__).resolve().parents[1]


def _synthetic() -> ProjectData:
    return ProjectData.from_dict(json.loads((ROOT / "examples/synthetic_20km_applied.ucd.json").read_text(encoding="utf-8")))


def test_phase6_6_bonding_authority_uses_design_normal_and_per_circuit_n1_vectors() -> None:
    study = solve_production_bonding_study(_synthetic(), maximum_iterations=6)
    by_id = {row.scenario_id: row for row in study.scenarios}
    assert {"NORMAL", "DESIGN", "N_MINUS_ONE_C1_OUT", "N_MINUS_ONE_C2_OUT"} <= set(by_id)
    assert by_id["N_MINUS_ONE_C1_OUT"].deenergized_circuit_ids == ("C1",)
    assert by_id["N_MINUS_ONE_C2_OUT"].deenergized_circuit_ids == ("C2",)
    assert study.authority == "PRODUCTION_GLOBAL_N_CORE_N_SHEATH"
    assert study.legacy_role == "DIAGNOSTIC_ONLY"


def test_parallel_circuit_changes_sheath_solution_via_same_global_network() -> None:
    project = _synthetic()
    scenarios = {item.scenario_id: item for item in resolve_operating_scenarios(project)}
    design = solve_global_multiconductor_network(apply_operating_scenario(project, scenarios["DESIGN"]), production_mode=True)
    c1out = solve_global_multiconductor_network(apply_operating_scenario(project, scenarios["N_MINUS_ONE_C1_OUT"]), production_mode=True)
    assert design.maximum_sheath_current_a != pytest.approx(c1out.maximum_sheath_current_a, abs=1e-9)
    assert design.maximum_sheath_to_earth_voltage_v != pytest.approx(c1out.maximum_sheath_to_earth_voltage_v, abs=1e-9)


def test_legacy_sheath_resistance_accepts_temperature_below_20c() -> None:
    project = ProjectData()
    project.cable.sheath_operating_temperature_c = 5.0
    r20, r5 = sheath_resistance_ohm_km(project.cable)
    assert r5 > 0.0
    assert r5 < r20


def test_sheath_temperature_correction_fails_closed_if_resistance_nonpositive() -> None:
    project = ProjectData()
    project.cable.sheath_operating_temperature_c = -273.0
    project.cable.sheath_temperature_coefficient_20_per_c = 0.01
    with pytest.raises(BondingInputError, match="sıfır/negatif direnç"):
        sheath_resistance_ohm_km(project.cable)
