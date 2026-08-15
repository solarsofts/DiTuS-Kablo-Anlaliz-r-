from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from ucd.calculations.multiconductor_global_network import solve_global_multiconductor_network
from ucd.calculations.operating_scenarios import resolve_operating_scenarios
from ucd.calculations.production_electrothermal import (
    ProductionElectroThermalInputError,
    solve_production_coupled_ampacity,
    solve_production_electrothermal_study,
    solve_production_operating_scenario,
)
from ucd.models.project import ProjectData


ROOT = Path(__file__).resolve().parents[1]


def _synthetic() -> ProjectData:
    return ProjectData.from_dict(json.loads((ROOT / "examples/synthetic_20km_applied.ucd.json").read_text(encoding="utf-8")))


def test_scenarios_are_circuit_vectors_and_n1_outages_are_not_aliased() -> None:
    project = _synthetic()
    scenarios = {item.scenario_id: item for item in resolve_operating_scenarios(project)}
    assert {"NORMAL", "DESIGN", "N_MINUS_ONE_C1_OUT", "N_MINUS_ONE_C2_OUT"} <= set(scenarios)
    c1_out = {item.circuit_id: item for item in scenarios["N_MINUS_ONE_C1_OUT"].circuit_states}
    c2_out = {item.circuit_id: item for item in scenarios["N_MINUS_ONE_C2_OUT"].circuit_states}
    assert not c1_out["C1"].energized and c1_out["C1"].phase_current_a == 0.0
    assert c1_out["C2"].energized and c1_out["C2"].phase_current_a > 0.0
    assert not c2_out["C2"].energized and c2_out["C2"].phase_current_a == 0.0
    assert scenarios["N_MINUS_ONE_C1_OUT"].fingerprint != scenarios["N_MINUS_ONE_C2_OUT"].fingerprint


def test_deenergized_circuit_remains_in_geometry_but_has_zero_losses() -> None:
    project = _synthetic()
    scenario = next(item for item in resolve_operating_scenarios(project) if item.scenario_id == "N_MINUS_ONE_C1_OUT")
    solved = solve_production_operating_scenario(project, scenario)
    assert solved.converged
    first_region = solved.regions[0]
    c1 = [item for item in first_region.cables if item.circuit_id == "C1"]
    c2 = [item for item in first_region.cables if item.circuit_id == "C2"]
    assert len(c1) == len(c2) == 3
    assert all(abs(item.current_a) < 1e-6 for item in c1)
    assert all(item.conductor_loss_w_m == pytest.approx(0.0, abs=1e-12) for item in c1)
    assert all(item.sheath_loss_w_m == pytest.approx(0.0, abs=1e-12) for item in c1)
    assert all(item.dielectric_loss_w_m == pytest.approx(0.0, abs=1e-12) for item in c1)
    assert all(abs(item.current_a) > 100.0 for item in c2)


def test_load_factor_does_not_scale_steady_state_current_target() -> None:
    project = ProjectData()
    for section in project.installation_design.cross_sections:
        for circuit in section.circuits:
            circuit.load_current_a = 321.0
            circuit.load_factor = 0.10
    result = solve_global_multiconductor_network(project, production_mode=True)
    phase_groups = [item for item in result.group_results if not item.group_id.startswith("OVERRIDE:")]
    assert phase_groups
    assert all(abs(item.target_current_a) == pytest.approx(321.0, abs=1e-6) for item in phase_groups)


def test_physical_current_override_is_a_global_constraint() -> None:
    project = ProjectData()
    physical_id = project.installation_design.cross_sections[0].physical_cables[0].physical_cable_id
    for section in project.installation_design.cross_sections:
        matching = next(item for item in section.physical_cables if item.physical_cable_id == physical_id)
        matching.current_override_a = 123.0
    result = solve_global_multiconductor_network(project, production_mode=True)
    cable = next(item for item in result.core_results if item.physical_cable_id == physical_id)
    assert abs(cable.core_current_a) == pytest.approx(123.0, abs=1e-6)
    assert any(item.group_id.startswith("OVERRIDE:") for item in result.group_results)


def test_legacy_global_lambda_does_not_change_physical_production_result() -> None:
    project_a = _synthetic()
    project_b = deepcopy(project_a)
    project_a.cable.sheath_loss_factor = 0.0
    project_b.cable.sheath_loss_factor = 0.90
    scenario_a = next(item for item in resolve_operating_scenarios(project_a) if item.scenario_id == "NORMAL")
    scenario_b = next(item for item in resolve_operating_scenarios(project_b) if item.scenario_id == "NORMAL")
    result_a = solve_production_operating_scenario(project_a, scenario_a)
    result_b = solve_production_operating_scenario(project_b, scenario_b)
    assert result_a.converged and result_b.converged
    assert result_a.maximum_conductor_temperature_c == pytest.approx(result_b.maximum_conductor_temperature_c, abs=1e-8)
    assert result_a.loss_vector_fingerprint == result_b.loss_vector_fingerprint


def test_loss_vector_matrix_product_is_exposed_per_region() -> None:
    project = _synthetic()
    result = solve_production_electrothermal_study(project).active
    assert result.regions
    for region in result.regions:
        assert len(region.loss_vector_w_m) == len(region.external_temperature_rise_vector_c) == len(region.cables)
        assert all(value >= 0.0 for value in region.loss_vector_w_m)
        assert any(value > 0.0 for value in region.external_temperature_rise_vector_c)
    assert result.loss_vector_fingerprint.startswith("LOSS-")


def test_target_circuit_ampacity_declares_background_currents() -> None:
    project = _synthetic()
    scenario = next(item for item in resolve_operating_scenarios(project) if item.scenario_id == "N_MINUS_ONE_C1_OUT")
    with pytest.raises(ProductionElectroThermalInputError, match="sheath-loss completeness"):
        solve_production_coupled_ampacity(
            project,
            scenario,
            scale_mode="TARGET_CIRCUIT_SCALE",
            target_circuit_ids=("C2",),
            maximum_iterations=5,
            current_tolerance_a=25.0,
            temperature_tolerance_c=2.0,
        )


def test_main_window_production_path_is_not_lambda_mutation() -> None:
    text = (ROOT / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    assert "solve_production_electrothermal_study" in text
    assert "λ1 proje kablosuna yazılmadı" in text
    assert "self.project.cable.sheath_loss_factor = result.lambda1" not in text


def test_zero_current_energized_circuit_keeps_dielectric_loss_and_lambda_is_not_applicable() -> None:
    project = _synthetic()
    for section in project.installation_design.cross_sections:
        for circuit in section.circuits:
            circuit.load_current_a = 0.0
    project.design_basis.normal_current_per_active_circuit_a = 0.0
    project.design_basis.design_current_per_circuit_a = 0.0
    project.design_basis.n1_current_per_circuit_a = 0.0
    project.cable.design_current_a = 0.0
    scenario = next(item for item in resolve_operating_scenarios(project) if item.scenario_id == "DESIGN")
    solved = solve_production_operating_scenario(project, scenario)
    assert solved.converged
    assert solved.global_lambda1 is None
    cables = solved.regions[0].cables
    assert all(abs(item.current_a) < 1e-8 for item in cables)
    assert all(item.conductor_loss_w_m == pytest.approx(0.0, abs=1e-12) for item in cables)
    assert all(item.sheath_loss_w_m == pytest.approx(0.0, abs=1e-12) for item in cables)
    assert all(item.dielectric_loss_w_m > 0.0 for item in cables)
    assert all(item.lambda1 is None for item in cables)


def test_asymmetric_geometry_keeps_circuit_out_scenarios_distinct() -> None:
    project = _synthetic()
    study = solve_production_electrothermal_study(project)
    by_id = {item.scenario.scenario_id: item for item in study.scenarios}
    c1_out = by_id["N_MINUS_ONE_C1_OUT"]
    c2_out = by_id["N_MINUS_ONE_C2_OUT"]
    assert c1_out.loss_vector_fingerprint != c2_out.loss_vector_fingerprint
    assert c1_out.maximum_conductor_temperature_c != pytest.approx(
        c2_out.maximum_conductor_temperature_c, abs=1e-6
    )


def test_analytic_and_nodal_validation_use_same_frozen_loss_vector() -> None:
    from ucd.calculations.production_electrothermal import validate_production_thermal_methods

    project = _synthetic()
    scenario = next(item for item in resolve_operating_scenarios(project) if item.scenario_id == "NORMAL")
    solved = solve_production_operating_scenario(project, scenario)
    comparison = validate_production_thermal_methods(project, solved)
    assert comparison.same_loss_vector
    assert comparison.loss_vector_fingerprint == solved.loss_vector_fingerprint
    assert comparison.nodal_energy_balance_error_percent <= 0.5
    assert comparison.nodal_maximum_linear_residual <= 1e-7
    assert comparison.validation_status == "PASS"


def test_report_bundle_renders_production_scenario_table() -> None:
    from ucd.calculations.reporting import (
        MODULE_IEC60287,
        CalculationResultsBundle,
        ReportConfiguration,
        build_project_report,
    )

    project = _synthetic()
    production = solve_production_electrothermal_study(project)
    report = build_project_report(
        project,
        ReportConfiguration(selected_modules=(MODULE_IEC60287,)),
        CalculationResultsBundle(production_electrothermal_result=production),
    )
    section = next(item for item in report.sections if item.section_id == MODULE_IEC60287)
    table = next(item for item in section.tables if "üretim elektro-termal" in item.title.lower())
    assert len(table.rows) == len(production.scenarios)
    assert any(row[0] == "DESIGN" for row in table.rows)
