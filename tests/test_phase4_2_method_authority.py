from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

from ucd.calculations.nodal_thermal import check_mesh_convergence, solve_nodal_route
from ucd.calculations.thermal_method_validation import (
    BASIS_ANALYTIC_PREVIEW,
    BASIS_HYBRID_BINDING,
    BASIS_METHOD_DISAGREEMENT,
    BASIS_NODAL_QUALITY_PENDING,
    VALIDATION_FAIL,
    VALIDATION_NOT_RUN,
    VALIDATION_PASS,
    cache_thermal_method_authority,
    cached_thermal_method_authority,
    evaluate_thermal_method_authority,
)
from ucd.models.project import ProjectData

ROOT = Path(__file__).resolve().parents[1]


def _project() -> ProjectData:
    project = ProjectData()
    project.cable.design_current_a = 800.0
    project.design_basis.design_current_per_circuit_a = 800.0
    return project


def _mesh_pass() -> SimpleNamespace:
    return SimpleNamespace(
        passed=True,
        ampacity_difference_percent=0.2,
        difference_c=0.2,
    )


def _align_nodal_with_analytic(study):
    analytic = {x.scenario_id: x for x in study.iec_route_result.scenarios}
    scenarios = []
    for scenario in study.scenarios:
        a_scenario = analytic[scenario.scenario_id]
        a_regions = {x.region_id: x for x in a_scenario.regions}
        regions = []
        for region in scenario.regions:
            a_region = a_regions.get(region.region_id)
            if a_region is None:
                regions.append(region)
            else:
                regions.append(replace(
                    region,
                    ampacity_per_cable_a=a_region.iec.ampacity_a,
                    maximum_conductor_temperature_c=a_region.iec.conductor_temperature_at_design_c,
                    status=a_region.iec.status,
                ))
        critical = min(regions, key=lambda x: x.ampacity_per_cable_a)
        scenarios.append(replace(
            scenario,
            regions=tuple(regions),
            critical_region_id=critical.region_id,
            critical_region_name=critical.region_name,
            route_ampacity_per_cable_a=critical.ampacity_per_cable_a,
            maximum_conductor_temperature_c=max(x.maximum_conductor_temperature_c for x in regions),
        ))
    return replace(study, scenarios=tuple(scenarios), method_validation=None)


def test_nodal_run_without_mesh_is_not_binding() -> None:
    study = solve_nodal_route(_project())
    assert study.method_validation.validation_status == VALIDATION_NOT_RUN
    assert study.method_validation.calculation_basis == "NODAL_QUALITY_PENDING"
    assert study.method_validation.active.official_ampacity_a is None


def test_qualified_matching_nodal_validates_analytic_and_manual_hybrid() -> None:
    project = _project()
    study = _align_nodal_with_analytic(solve_nodal_route(project))
    mesh = {
        (scenario.scenario_id, region.region_id): _mesh_pass()
        for scenario in study.scenarios
        for region in scenario.regions
        if region.region_id == "TR-01"
    }
    result = evaluate_thermal_method_authority(project, study, mesh_checks=mesh)
    assert result.validation_status == VALIDATION_PASS
    assert result.calculation_basis == BASIS_HYBRID_BINDING
    assert result.active.official_ampacity_a is not None


def test_qualified_optimistic_difference_becomes_method_disagreement() -> None:
    project = _project()
    study = _align_nodal_with_analytic(solve_nodal_route(project))
    scenarios = []
    for scenario in study.scenarios:
        regions = []
        for region in scenario.regions:
            if region.region_id == "TR-01":
                regions.append(replace(
                    region,
                    ampacity_per_cable_a=region.ampacity_per_cable_a * 0.90,
                    maximum_conductor_temperature_c=region.maximum_conductor_temperature_c + 8.0,
                ))
            else:
                regions.append(region)
        critical = min(regions, key=lambda x: x.ampacity_per_cable_a)
        scenarios.append(replace(
            scenario,
            regions=tuple(regions),
            critical_region_id=critical.region_id,
            critical_region_name=critical.region_name,
            route_ampacity_per_cable_a=critical.ampacity_per_cable_a,
            maximum_conductor_temperature_c=max(x.maximum_conductor_temperature_c for x in regions),
        ))
    study = replace(study, scenarios=tuple(scenarios))
    mesh = {
        (scenario.scenario_id, "TR-01"): _mesh_pass()
        for scenario in study.scenarios
    }
    result = evaluate_thermal_method_authority(project, study, mesh_checks=mesh)
    assert result.validation_status == "PASS"
    assert result.calculation_basis == "HYBRID_BINDING"
    assert result.active.official_ampacity_a is not None


def test_nonreducible_slab_runs_nodal_but_waits_for_quality_gate() -> None:
    project = ProjectData.from_dict(json.loads(
        (ROOT / "examples" / "synthetic_20km_line.ucd.json").read_text()
    ))
    project.installation_design.cross_sections[0].channel_geometry.cover_slab_enabled = True
    study = solve_nodal_route(project)
    assert study.iec_route_result.active.completion_status == "COMPLETE"
    tr1 = next(x for x in study.method_validation.active.region_comparisons if x.region_id == "TR-01")
    assert tr1.calculation_basis == BASIS_NODAL_QUALITY_PENDING
    assert tr1.analytic_ampacity_a is not None
    assert tr1.nodal_ampacity_a is not None
    assert tr1.result_authority == "ENGINEERING_APPROXIMATION"
    assert tr1.authoritative_method == "NODAL"


def test_validation_cache_uses_existing_engine_run_and_geometry_fingerprint() -> None:
    project = _project()
    study = solve_nodal_route(project)
    cache_thermal_method_authority(project, study.method_validation)
    assert cached_thermal_method_authority(project) is not None
    project.installation_design.cross_sections[0].physical_cables[0].x_m += 0.001
    assert cached_thermal_method_authority(project) is None


def test_mesh_convergence_contains_ampacity_and_temperature_gates() -> None:
    project = _project()
    study = solve_nodal_route(project)
    analytic = study.iec_route_result.active.regions[0]
    nodal = study.active.regions[0]
    check = check_mesh_convergence(
        project,
        nodal.region_id,
        nodal.design_current_per_cable_a,
        nodal.active_circuit_count,
        nodal.regional_lambda1,
        analytic.iec,
        tolerance_percent=1.0,
    )
    assert check.refined_ampacity_a > 0.0
    assert abs(check.ampacity_difference_percent) <= 1.0
    assert check.difference_c <= 1.0
    assert check.passed
