from __future__ import annotations

import pytest

from ucd.calculations.engine_precheck import PRECHECK_BLOCKED, evaluate_engine_precheck
from ucd.calculations.iec60287 import CalculationInputError, solve_section
from ucd.calculations.model_applicability import (
    BLOCKED,
    REFERENCE_ONLY,
    SUPPORTED,
    evaluate_cable_model_applicability,
)
from ucd.calculations.multiconductor_global_network import (
    MulticonductorGlobalInputError,
    solve_global_multiconductor_network,
)
from ucd.models.project import CableLayerData, ProjectData


def test_default_single_core_unarmoured_is_supported() -> None:
    project = ProjectData()
    scope = evaluate_cable_model_applicability(project.cable)
    assert scope.status == SUPPORTED
    assert scope.production_physics_allowed is True
    assert scope.reference_workflow_allowed is True


def test_multicore_is_reference_only_not_silently_solved() -> None:
    project = ProjectData()
    project.cable.conductors_per_cable = 3
    project.cable.construction_type = "THREE_CORE_XLPE"
    scope = evaluate_cable_model_applicability(project.cable)
    assert scope.status == REFERENCE_ONLY
    assert scope.production_physics_allowed is False
    assert scope.reference_workflow_allowed is True
    assert any("T1" in reason and "G" in reason for reason in scope.reasons)

    precheck = evaluate_engine_precheck(project, "iec60287")
    assert precheck.status == PRECHECK_BLOCKED
    gate = next(item for item in precheck.items if item.item_id == "production_model_scope")
    assert gate.missing

    with pytest.raises(CalculationInputError, match="MODEL_APPLICABILITY_REFERENCE_ONLY"):
        solve_section(project.cable, project.route_sections[0])


def test_armour_layer_is_reference_only_even_when_lambda2_zero() -> None:
    project = ProjectData()
    project.cable.armour_loss_factor = 0.0
    project.cable.layers.append(CableLayerData(
        layer_id="ARM-1", name="Armour", layer_type="ARMOUR", material="STEEL",
        inner_diameter_mm=95.0, outer_diameter_mm=100.0,
    ))
    scope = evaluate_cable_model_applicability(project.cable)
    assert scope.status == REFERENCE_ONLY
    assert any("Zırhlı" in reason for reason in scope.reasons)

    with pytest.raises(MulticonductorGlobalInputError, match="REFERENCE_ONLY"):
        solve_global_multiconductor_network(project, production_mode=True)


def test_nonpositive_conductor_count_is_fully_blocked() -> None:
    project = ProjectData()
    project.cable.conductors_per_cable = 0
    scope = evaluate_cable_model_applicability(project.cable)
    assert scope.status == BLOCKED
    assert not scope.production_physics_allowed
    assert not scope.reference_workflow_allowed


def test_reference_only_does_not_block_report_or_procurement_precheck_by_scope() -> None:
    project = ProjectData()
    project.cable.conductors_per_cable = 3
    for engine_id in ("report", "procurement"):
        result = evaluate_engine_precheck(project, engine_id)
        assert all(item.item_id != "production_model_scope" for item in result.items)
