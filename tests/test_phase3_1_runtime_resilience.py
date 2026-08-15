from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ucd.calculations.bonding import sheath_resistance_ohm_km
from ucd.calculations.calculation_policy import (
    bootstrap_calculation_policy,
    find_parameter_record,
    resolve_project_alpha_20_per_c,
)
from ucd.calculations.iec60287 import (
    CalculationInputError,
    ac_resistance_at_temperature_ohm_km,
    solve_project,
    solve_section,
)
from ucd.calculations.thermal_route import (
    ThermalRouteInputError,
    _scenario_currents,
    materialize_route_sections,
    materialize_route_sections_partial,
    solve_thermal_route,
)
from ucd.models.project import (
    CALC_METHOD_MANUAL_OVERRIDE,
    CALC_STATUS_VERIFIED,
    CableData,
    ParameterProvenanceRecord,
    ProjectData,
    RouteSection,
)

ROOT = Path(__file__).resolve().parents[1]


def _cold_section(ambient: float = 5.0) -> RouteSection:
    return RouteSection(
        "Soğuk bölüm", 100.0, ambient_temperature_c=ambient,
        external_thermal_resistance_t4_km_w=0.85,
    )


def test_sub_20_temperature_resistance_is_valid_and_traced_not_warned() -> None:
    cable = CableData(design_current_a=1.0, conductor_material="Cu")
    result = solve_section(cable, _cold_section(5.0))
    assert result.conductor_temperature_at_design_c < 20.0
    assert result.ac_resistance_at_design_ohm_km < result.dc_resistance_20_ohm_km * (
        1.0 + cable.skin_effect_factor + cable.proximity_effect_factor
    )
    assert any("Rdc20" in line and "düzeltildi" in line for line in result.thermal_trace)
    assert not any("düzeltildi" in note for note in result.notes)


def test_negative_ambient_and_zero_current_are_valid_iec_working_points() -> None:
    cable = CableData(design_current_a=0.0, conductor_material="Al", temperature_coefficient_20_per_c=0.00393)
    result = solve_section(cable, _cold_section(-5.0))
    assert result.design_current_a == 0.0
    assert result.conductor_loss_at_design_w_m == pytest.approx(0.0)
    assert result.conductor_temperature_at_design_c >= -5.0
    assert any("MATERIAL_DEFAULT_AL" in line for line in result.thermal_trace)
    r20, rac = ac_resistance_at_temperature_ohm_km(cable, -5.0)
    assert r20 > 0 and rac > 0


def test_only_mathematical_or_physical_invalidity_remains_hard_error() -> None:
    cable = CableData()
    with pytest.raises(CalculationInputError):
        ac_resistance_at_temperature_ohm_km(cable, -274.0)


def test_strict_and_partial_materialization_share_the_same_classification() -> None:
    project = ProjectData()
    project.thermal_design.templates[1].manual_t4_km_w = 0.0
    project.thermal_design.regions[1].overrides["manual_t4_km_w"] = 0.0
    partial = materialize_route_sections_partial(project.thermal_design, project.cable)
    assert partial.classification.errors_for_region("TR-02")
    assert partial.sections
    with pytest.raises(ThermalRouteInputError):
        materialize_route_sections(project.thermal_design, project.cable)
    route = solve_thermal_route(project)
    assert route.active.completion_status == "PARTIAL"
    assert any(not outcome.success and outcome.region_id == "TR-02" for outcome in route.active.region_outcomes)


def test_partial_scenario_has_no_official_ampacity_and_retains_bounds() -> None:
    project = ProjectData()
    project.thermal_design.templates[1].manual_t4_km_w = 0.0
    project.thermal_design.regions[1].overrides["manual_t4_km_w"] = 0.0
    result = solve_thermal_route(project).active
    assert result.completion_status == "PARTIAL"
    assert result.route_ampacity_a is None
    assert result.maximum_conductor_temperature_c is None
    assert result.ampacity_upper_bound_a is not None
    assert result.temperature_lower_bound_c is not None
    assert result.suitability_status in {"INDETERMINATE", "UYGUN_DEGIL"}


def test_partial_can_be_definitely_unsuitable_by_monotonic_upper_bound() -> None:
    baseline_project = ProjectData()
    baseline = solve_thermal_route(baseline_project).active
    assert baseline.route_ampacity_a is not None

    project = ProjectData()
    target = baseline.route_ampacity_a + 25.0
    project.design_basis.normal_current_per_active_circuit_a = target
    project.design_basis.n1_current_per_circuit_a = target
    project.design_basis.design_current_per_circuit_a = target
    project.thermal_design.templates[1].manual_t4_km_w = 0.0
    project.thermal_design.regions[1].overrides["manual_t4_km_w"] = 0.0
    result = solve_thermal_route(project).active
    assert result.completion_status == "PARTIAL"
    assert result.suitability_status == "UYGUN_DEGIL"
    assert result.status == "HESAP EKSİK — UYGUN DEĞİL"
    assert result.ampacity_upper_bound_a is not None
    assert result.ampacity_upper_bound_a < result.design_current_per_cable_a


def test_all_cells_physical_rejection_is_failed_and_unsuitable() -> None:
    project = ProjectData()
    project.cable.max_temperature_c = 25.0
    for template in project.thermal_design.templates:
        template.ambient_temperature_c = 25.0
    result = solve_thermal_route(project).active
    assert result.completion_status == "FAILED"
    assert result.suitability_status == "UYGUN_DEGIL"
    assert result.route_ampacity_a is None
    assert all(not outcome.success for outcome in result.region_outcomes)


def test_project_global_cable_error_remains_fail_fast() -> None:
    project = ProjectData()
    project.cable.frequency_hz = 0.0
    with pytest.raises(ThermalRouteInputError, match="Proje-geneli"):
        solve_thermal_route(project)


def test_unexpected_programming_error_is_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    import ucd.calculations.thermal_route as route_module

    def explode(*_args, **_kwargs):
        raise RuntimeError("programming defect")

    monkeypatch.setattr(route_module, "solve_section", explode)
    with pytest.raises(RuntimeError, match="programming defect"):
        solve_thermal_route(ProjectData())


def test_legacy_solve_project_preserves_successes_and_section_errors() -> None:
    cable = CableData(design_current_a=10.0)
    sections = [
        _cold_section(5.0),
        RouteSection("Geçersiz", 10.0, ambient_temperature_c=90.0),
    ]
    result = solve_project(cable, sections)
    assert len(result) == 1
    assert result.completion_status == "PARTIAL"
    assert result.outcomes[0].success
    assert not result.outcomes[1].success


def test_zero_scenarios_deduplicate_to_one_design_with_alias_trace() -> None:
    project = ProjectData()
    project.cable.design_current_a = 0.0
    project.design_basis.normal_current_per_active_circuit_a = 0.0
    project.design_basis.normal_total_current_a = 0.0
    project.design_basis.n1_current_per_circuit_a = 0.0
    project.design_basis.design_current_per_circuit_a = 0.0
    scenarios = _scenario_currents(project)
    assert len(scenarios) == 1
    assert scenarios[0].scenario_id == "DESIGN"
    assert set(scenarios[0].equivalent_scenario_ids) == {"NORMAL", "N_MINUS_ONE", "DESIGN"}
    result = solve_thermal_route(project).active
    assert result.design_current_per_cable_a == 0.0
    assert set(result.equivalent_scenario_ids) == {"NORMAL", "N_MINUS_ONE", "DESIGN"}


def test_al_legacy_alpha_is_migrated_to_material_default_only_for_auto_sources() -> None:
    project = ProjectData()
    project.cable.conductor_material = "Al"
    project.cable.temperature_coefficient_20_per_c = 0.00393
    project.calculation_policy.parameter_records.append(ParameterProvenanceRecord(
        record_id="PAR-CABLE-TEMPERATURE-COEFFICIENT-20-PER-C",
        parameter_path="cable.temperature_coefficient_20_per_c",
        label="alpha",
        value_snapshot=0.00393,
        method="CERTIFIED_INPUT",
        status="VERIFIED",
        source_type="PROJECT_CABLE_SNAPSHOT",
        source_reference="SNAP-LEGACY",
    ))
    bootstrap_calculation_policy(project)
    record = find_parameter_record(project, "cable.temperature_coefficient_20_per_c")
    assert project.cable.temperature_coefficient_20_per_c == pytest.approx(0.00403)
    assert record is not None
    assert record.source_type == "MATERIAL_DEFAULT"
    assert record.method == "PHYSICAL_AUTO"


def test_manual_alpha_override_is_preserved_even_when_equal_to_legacy_default() -> None:
    project = ProjectData()
    project.cable.conductor_material = "Al"
    project.cable.temperature_coefficient_20_per_c = 0.00393
    project.calculation_policy.parameter_records.append(ParameterProvenanceRecord(
        record_id="PAR-CABLE-TEMPERATURE-COEFFICIENT-20-PER-C",
        parameter_path="cable.temperature_coefficient_20_per_c",
        label="alpha",
        value_snapshot=0.00393,
        method=CALC_METHOD_MANUAL_OVERRIDE,
        status=CALC_STATUS_VERIFIED,
        source_type="SITE_TEST",
        source_reference="Alaşımlı Al test raporu",
    ))
    bootstrap_calculation_policy(project)
    resolution = resolve_project_alpha_20_per_c(project, "cable.temperature_coefficient_20_per_c")
    assert project.cable.temperature_coefficient_20_per_c == pytest.approx(0.00393)
    assert resolution.value_per_c == pytest.approx(0.00393)
    assert resolution.explicit_override
    record = find_parameter_record(project, "cable.temperature_coefficient_20_per_c")
    assert record is not None and record.method == CALC_METHOD_MANUAL_OVERRIDE


def test_pb_sheath_uses_shared_material_resolver() -> None:
    cable = CableData(
        sheath_material="Pb",
        sheath_cross_section_mm2=120.0,
        sheath_dc_resistance_20_ohm_km=0.0,
        sheath_temperature_coefficient_20_per_c=0.00393,
        sheath_operating_temperature_c=70.0,
    )
    r20, rtheta = sheath_resistance_ohm_km(cable)
    assert r20 > 0.0
    assert rtheta > r20


def test_all_legacy_status_literal_comparisons_were_reviewed() -> None:
    source_root = ROOT / "src"
    offenders = []
    for path in source_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if 'status == "UYGUN"' in text or 'status != "UYGUN"' in text:
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_preprocessor_uses_partial_materialization_entry_point() -> None:
    # FAZ 7.2 moved calculation orchestration out of MainWindow.  The headless
    # application layer must use the project materialization wrapper, whose
    # contract delegates to partial route materialization and preserves valid
    # sections when another region is not analytically solvable.
    source = (ROOT / "src/ucd/calculations/application_orchestration.py").read_text(encoding="utf-8")
    runtime = (ROOT / "src/ucd/calculations/project_geometry_runtime.py").read_text(encoding="utf-8")
    assert "materialize_project_route_sections(" in source
    assert "materialize_route_sections_partial(" in runtime
