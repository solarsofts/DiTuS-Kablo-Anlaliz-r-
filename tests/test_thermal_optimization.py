from __future__ import annotations

from copy import deepcopy

from ucd.calculations import (
    apply_thermal_design_alternative,
    evaluate_thermal_design_alternatives,
    solve_nodal_route,
)
from ucd.models.project import ProjectData


def test_thermal_alternatives_are_recalculated_and_ranked() -> None:
    project = ProjectData()
    study = solve_nodal_route(project)
    alternatives = evaluate_thermal_design_alternatives(
        project,
        study,
        study.active_scenario_id,
        study.active.critical_region_id,
        maximum_candidates=3,
    )
    assert len(alternatives) == 3
    assert [item.ampacity_delta_a for item in alternatives] == sorted(
        (item.ampacity_delta_a for item in alternatives), reverse=True
    )
    assert any(item.status == "İYİLEŞME" for item in alternatives)
    assert all(item.ampacity_a > 0 for item in alternatives)


def test_apply_alternative_changes_only_selected_region_overrides() -> None:
    project = ProjectData()
    study = solve_nodal_route(project)
    region_id = study.active.critical_region_id
    alternatives = evaluate_thermal_design_alternatives(
        project, study, study.active_scenario_id, region_id, maximum_candidates=2
    )
    selected = alternatives[0]
    before_other = {
        region.region_id: deepcopy(region.overrides)
        for region in project.thermal_design.regions
        if region.region_id != region_id
    }
    apply_thermal_design_alternative(project, selected)
    target = next(region for region in project.thermal_design.regions if region.region_id == region_id)
    for change in selected.changes:
        assert target.overrides[change.key] == change.new_value
    for other_id, overrides in before_other.items():
        other = next(region for region in project.thermal_design.regions if region.region_id == other_id)
        assert other.overrides == overrides


def test_grout_override_is_an_explicit_template_property() -> None:
    project = ProjectData()
    assert all(hasattr(template, "grout_thermal_resistivity_km_w") for template in project.thermal_design.templates)
