from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ucd.calculations.electrothermal_coupled import (
    solve_electrothermal_ampacity,
    solve_electrothermal_coupled,
)
from ucd.calculations.shadow_validation import (
    MANDATORY_EXTERNAL_BENCHMARKS,
    PROMOTION_HOLD,
    STATUS_FAIL,
    STATUS_NOT_RUN,
    STATUS_PASS,
    ExternalBenchmarkEvidence,
    run_shadow_validation,
)
from ucd.models.project import ProjectData


@pytest.fixture(scope="module")
def project() -> ProjectData:
    return ProjectData()


@pytest.fixture(scope="module")
def coupled(project: ProjectData):
    return solve_electrothermal_coupled(
        project,
        mesh_scale=3.0,
        maximum_iterations=15,
        temperature_tolerance_c=0.10,
    )


@pytest.fixture(scope="module")
def ampacity(project: ProjectData):
    return solve_electrothermal_ampacity(
        project,
        mesh_scale=3.0,
        maximum_closed_loop_iterations=15,
        maximum_rating_iterations=10,
        temperature_tolerance_c=0.30,
        current_tolerance_a=6.0,
    )


@pytest.fixture(scope="module")
def validation(project: ProjectData, coupled, ampacity):
    return run_shadow_validation(
        project,
        coupled_result=coupled,
        ampacity_result=ampacity,
        run_ampacity=False,
    )


def _gate(result, gate_id: str):
    return next(item for item in result.gates if item.gate_id == gate_id)


def test_default_validation_holds_shadow_but_internal_numerical_gates_pass(validation) -> None:
    assert validation.promotion_recommendation == PROMOTION_HOLD
    for gate_id in (
        "CLOSED_LOOP_CONVERGENCE",
        "EM_DUAL_METHOD_AGREEMENT",
        "EM_EQUATION_RESIDUAL",
        "PHASE_CURRENT_CONSTRAINT",
        "SHEATH_KCL",
        "SHEATH_BRANCH_VOLTAGE",
        "CORE_VOLTAGE_EQUALITY",
        "THERMAL_REGION_CONVERGENCE",
        "THERMAL_ENERGY_BALANCE",
        "THERMAL_LINEAR_RESIDUAL",
        "INSTALLATION_MODEL_VALID",
        "CLOSED_LOOP_AMPACITY",
    ):
        assert _gate(validation, gate_id).status == STATUS_PASS
    assert _gate(validation, "EXTERNAL_PUBLISHED_BENCHMARKS").status == STATUS_NOT_RUN
    assert validation.final_design_ready is False


def test_legacy_physical_comparison_is_reason_coded_not_silent(validation) -> None:
    metrics = {item.metric_id: item for item in validation.metrics}
    assert "AMPACITY_IEC_VS_PHYSICAL" in metrics
    assert "AMPACITY_NODAL_VS_PHYSICAL" in metrics
    assert "LAMBDA1_LEGACY_VS_PHYSICAL" in metrics
    assert "SHEATH_EARTH_VOLTAGE" in metrics
    assert metrics["AMPACITY_IEC_VS_PHYSICAL"].reason_code == "THERMAL_AND_LOSS_MODEL_CHANGED"
    assert metrics["SHEATH_EARTH_VOLTAGE"].reason_code == "OPEN_CIRCUIT_PROFILE_VS_SOLVED_NODE_VOLTAGE"
    assert metrics["AMPACITY_NODAL_VS_PHYSICAL"].legacy_value > 0.0
    assert metrics["AMPACITY_NODAL_VS_PHYSICAL"].physical_value > 0.0


def test_external_benchmark_registry_is_explicit_and_not_embedded(validation) -> None:
    assert len(validation.benchmarks) == len(MANDATORY_EXTERNAL_BENCHMARKS)
    assert all(item.status == STATUS_NOT_RUN for item in validation.benchmarks)
    assert all(item.blocking for item in validation.benchmarks)
    assert all(item.evidence_reference == "" for item in validation.benchmarks)


def test_traceable_external_evidence_closes_only_external_registry(project, coupled, ampacity) -> None:
    evidence = tuple(
        ExternalBenchmarkEvidence(
            benchmark_id=benchmark_id,
            passed=True,
            evidence_reference=f"LAB-VALIDATION/{benchmark_id}/REV-A",
            case_count=2,
            source_hash=f"hash-{index}",
        )
        for index, (benchmark_id, _) in enumerate(MANDATORY_EXTERNAL_BENCHMARKS, start=1)
    )
    result = run_shadow_validation(
        project,
        coupled_result=coupled,
        ampacity_result=ampacity,
        run_ampacity=False,
        external_benchmark_evidence=evidence,
    )
    assert all(item.status == STATUS_PASS for item in result.benchmarks)
    assert _gate(result, "EXTERNAL_PUBLISHED_BENCHMARKS").status == STATUS_PASS
    # Generic project still contains unverified/legacy parameter provenance.
    assert result.final_design_ready is False


def test_dual_method_disagreement_is_a_blocking_failure(project, coupled, ampacity) -> None:
    altered = deepcopy(coupled)
    altered.final_global_em.methods_agree = False
    altered.final_global_em.maximum_method_core_current_difference_a = 0.5
    result = run_shadow_validation(
        project,
        coupled_result=altered,
        ampacity_result=ampacity,
        run_ampacity=False,
    )
    gate = _gate(result, "EM_DUAL_METHOD_AGREEMENT")
    assert gate.status == STATUS_FAIL
    assert gate.blocking


def test_shadow_validation_does_not_mutate_project(project, coupled, ampacity) -> None:
    candidate = deepcopy(project)
    before = deepcopy(candidate.to_dict())
    run_shadow_validation(
        candidate,
        coupled_result=coupled,
        ampacity_result=ampacity,
        run_ampacity=False,
    )
    assert candidate.to_dict() == before


def test_validation_result_serialization_contains_only_audit_payload(validation) -> None:
    payload = validation.to_dict()
    assert payload["mode"] == "SHADOW_VALIDATION"
    assert isinstance(payload["metrics"], list)
    assert isinstance(payload["gates"], list)
    assert payload["summary"]["final_design_ready"] is False


def test_shadow_validation_ui_contract_is_additive() -> None:
    root = Path(__file__).resolve().parents[1]
    dialog = (root / "src/ucd/ui/shadow_validation_dialog.py").read_text(encoding="utf-8")
    window = (root / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    assert "Doğrulama ve Shadow Karşılaştırmayı Çalıştır" in dialog
    assert "Legacy ↔ Fiziksel" in dialog
    assert "IEC/CIGRE Benchmark" in dialog
    assert "Fiziksel Motor Doğrulama ve Shadow Karşılaştırma" in window
    assert "SHADOW_VALIDATION" in dialog
