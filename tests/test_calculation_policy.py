from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ucd.calculations.calculation_policy import (
    audit_calculation_policy,
    bootstrap_calculation_policy,
    find_parameter_record,
    register_physical_calculation,
)
from ucd.models.project import (
    CALC_METHOD_LEGACY_COEFFICIENT,
    CALC_METHOD_PHYSICAL_AUTO,
    CALC_STATUS_CALCULATED,
    ProjectData,
)

ROOT = Path(__file__).resolve().parents[1]


def _locked_scalar_snapshot(project: ProjectData) -> dict[str, float | str | int]:
    cable = project.cable
    basis = project.design_basis
    return {
        "dc_resistance_20_ohm_km": cable.dc_resistance_20_ohm_km,
        "skin_effect_factor": cable.skin_effect_factor,
        "proximity_effect_factor": cable.proximity_effect_factor,
        "capacitance_uf_km": cable.capacitance_uf_km,
        "dielectric_loss_tan_delta": cable.dielectric_loss_tan_delta,
        "sheath_loss_factor": cable.sheath_loss_factor,
        "armour_loss_factor": cable.armour_loss_factor,
        "thermal_resistance_t1_km_w": cable.thermal_resistance_t1_km_w,
        "thermal_resistance_t2_km_w": cable.thermal_resistance_t2_km_w,
        "thermal_resistance_t3_km_w": cable.thermal_resistance_t3_km_w,
        "burial_depth_m": basis.burial_depth_m,
        "phase_spacing_m": basis.phase_spacing_m,
        "circuit_spacing_m": basis.circuit_spacing_m,
        "soil_thermal_resistivity_km_w": basis.soil_thermal_resistivity_km_w,
    }


def test_bootstrap_is_additive_and_numerically_neutral() -> None:
    project = ProjectData()
    before = deepcopy(_locked_scalar_snapshot(project))
    policy = bootstrap_calculation_policy(project)
    after = _locked_scalar_snapshot(project)
    assert before == after
    assert policy.policy_revision == "0.16.4"
    assert len(policy.parameter_records) >= 18


def test_legacy_loss_and_ac_coefficients_are_explicitly_preliminary() -> None:
    project = ProjectData()
    bootstrap_calculation_policy(project)
    for path in (
        "cable.skin_effect_factor",
        "cable.proximity_effect_factor",
        "cable.sheath_loss_factor",
        "cable.armour_loss_factor",
    ):
        record = find_parameter_record(project, path)
        assert record is not None
        assert record.method == CALC_METHOD_LEGACY_COEFFICIENT
        assert record.status == "PRELIMINARY_ONLY"


def test_physical_lambda1_registration_tracks_existing_result_without_rewriting_it() -> None:
    project = ProjectData()
    project.cable.sheath_loss_factor = 0.012345
    register_physical_calculation(
        project,
        "cable.sheath_loss_factor",
        source_reference="Bonding/CIM test solution",
        standard_reference="IEC 60287-1-3; IEEE 575; CIGRE TB 797",
        validity_scope="Test bonding system",
    )
    record = find_parameter_record(project, "cable.sheath_loss_factor")
    assert project.cable.sheath_loss_factor == 0.012345
    assert record is not None
    assert record.value_snapshot == 0.012345
    assert record.method == CALC_METHOD_PHYSICAL_AUTO
    assert record.status == CALC_STATUS_CALCULATED


def test_policy_round_trip_and_v0163_migration() -> None:
    legacy = ProjectData.from_dict({
        "schema_version": "0.16.3",
        "project_name": "Locked v0.16.3 input",
        "cable": {"skin_effect_factor": 0.031, "sheath_loss_factor": 0.044},
    })
    assert legacy.schema_version == "0.16.4"
    bootstrap_calculation_policy(legacy)
    payload = legacy.to_dict()
    loaded = ProjectData.from_dict(payload)
    assert loaded.schema_version == "0.16.4"
    assert loaded.cable.skin_effect_factor == 0.031
    assert loaded.cable.sheath_loss_factor == 0.044
    assert len(loaded.calculation_policy.parameter_records) >= 18


def test_audit_detects_value_change_without_source_refresh() -> None:
    project = ProjectData()
    bootstrap_calculation_policy(project)
    project.cable.capacitance_uf_km = 0.25
    audit = audit_calculation_policy(project)
    assert any(
        issue.code == "VALUE_CHANGED_WITHOUT_PROVENANCE"
        and issue.parameter_path == "cable.capacitance_uf_km"
        for issue in audit.issues
    )
    assert audit.final_design_blocked


def test_ui_exposes_parameter_provenance_without_editing_engineering_value() -> None:
    main_source = (ROOT / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    dialog_source = (ROOT / "src/ucd/ui/parameter_provenance_dialog.py").read_text(encoding="utf-8")
    assert "Hesap Parametreleri ve Kaynakları…" in main_source
    assert "ParameterProvenanceDialog" in main_source
    assert "Bu ekran sayısal değerleri değiştirmez" in dialog_source
    assert "register_parameter_provenance" in dialog_source
