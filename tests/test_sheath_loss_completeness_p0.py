from __future__ import annotations

from copy import deepcopy

import pytest

from ucd.calculations.sheath_loss_completeness import (
    AUTHORITY_BLOCKED,
    AUTHORITY_FULL,
    SOURCE_EXTERNAL,
    SOURCE_IEC_CALCULATED,
    SOURCE_IEC_NOTE3,
    SOURCE_IEC_SOLID,
    _base_terms,
    resolve_sheath_loss_completeness,
)
from ucd.models.project import BONDING_CROSS, BONDING_SOLID_BOTH_END, ProjectData


def test_small_m_keeps_lambda0_and_only_drops_delta_terms() -> None:
    l0, d1, d2 = _base_terms(0.05, 0.25, "TREFOIL")
    assert l0 > 0.0
    assert d1 == pytest.approx(0.0)
    assert d2 == pytest.approx(0.0)


def test_default_single_circuit_trefoil_calculates_iec_eddy_factor() -> None:
    project = ProjectData()
    project.bonding.scheme = BONDING_CROSS
    result = resolve_sheath_loss_completeness(project, project.installation_design.cross_sections[0])
    assert result.authority == AUTHORITY_FULL
    assert result.eddy_source == SOURCE_IEC_CALCULATED
    assert len(result.factors_by_physical_cable) == 3
    assert all(value > 0.0 for _, value in result.factors_by_physical_cable)


def test_note3_requires_explicit_equalizing_or_thin_sheet_evidence() -> None:
    project = ProjectData()
    screen = next(layer for layer in project.cable.layers if layer.layer_type == "METALLIC_SHEATH")
    screen.layer_type = "METALLIC_SCREEN"
    screen.wire_count = 40
    screen.notes = "Copper wire screen with equalizing strip"
    result = resolve_sheath_loss_completeness(project, project.installation_design.cross_sections[0])
    assert result.authority == AUTHORITY_FULL
    assert result.eddy_source == SOURCE_IEC_NOTE3
    assert all(value == 0.0 for _, value in result.factors_by_physical_cable)


def test_wire_screen_without_note3_detail_is_not_silently_assumed_negligible() -> None:
    project = ProjectData()
    screen = next(layer for layer in project.cable.layers if layer.layer_type == "METALLIC_SHEATH")
    screen.layer_type = "METALLIC_SCREEN"
    screen.wire_count = 40
    screen.notes = "Copper wire screen"
    result = resolve_sheath_loss_completeness(project, project.installation_design.cross_sections[0])
    assert result.authority == AUTHORITY_BLOCKED
    assert "LAMBDA1_EDDY_CLOSED_FORM_CUSTOM_OR_INCOMPLETE" in result.reason_codes


def test_solid_both_end_non_milliken_does_not_require_eddy_term() -> None:
    project = ProjectData()
    project.bonding.scheme = BONDING_SOLID_BOTH_END
    project.cable.conductor_stranding_type = "ROUND_COMPACTED"
    result = resolve_sheath_loss_completeness(project, project.installation_design.cross_sections[0])
    assert result.authority == AUTHORITY_FULL
    assert result.eddy_source == SOURCE_IEC_SOLID
    assert all(value == 0.0 for _, value in result.factors_by_physical_cable)


def test_multi_circuit_closed_form_is_fail_closed_without_external_value() -> None:
    project = ProjectData()
    base = project.installation_design.cross_sections[0]
    extra = deepcopy(base.physical_cables)
    for item in extra:
        item.physical_cable_id = item.physical_cable_id.replace("C1", "C2")
        item.circuit_id = "C2"
        item.x_m += 0.8
    base.physical_cables.extend(extra)
    result = resolve_sheath_loss_completeness(project, base)
    assert result.authority == AUTHORITY_BLOCKED
    assert result.reason_codes == ("LAMBDA1_EDDY_CLOSED_FORM_OUT_OF_SCOPE_MULTI_CIRCUIT",)


def test_external_factor_restores_authority_and_stale_frequency_blocks() -> None:
    project = ProjectData()
    base = project.installation_design.cross_sections[0]
    extra = deepcopy(base.physical_cables)
    for item in extra:
        item.physical_cable_id = item.physical_cable_id.replace("C1", "C2")
        item.circuit_id = "C2"
        item.x_m += 0.8
    base.physical_cables.extend(extra)
    c = project.cable
    c.sheath_eddy_external_factor = 0.0123
    c.sheath_eddy_external_source_type = "USER_STANDARD_CALCULATION"
    c.sheath_eddy_external_reference = "CALC-001"
    c.sheath_eddy_external_frequency_hz = c.frequency_hz
    c.sheath_eddy_external_sheath_temperature_c = c.sheath_operating_temperature_c
    c.sheath_eddy_external_d_mm = c.sheath_mean_diameter_mm
    first_group = [x for x in base.physical_cables if x.circuit_id == "C1"]
    distances = sorted(((first_group[i].x_m-first_group[j].x_m)**2 + (first_group[i].depth_m-first_group[j].depth_m)**2)**0.5 for i,j in ((0,1),(1,2),(2,0)))
    c.sheath_eddy_external_s_mm = 0.5 * (distances[0] + distances[1]) * 1000.0
    c.sheath_eddy_external_formation_assumption = base.arrangement_label
    ok = resolve_sheath_loss_completeness(project, base)
    assert ok.authority == AUTHORITY_FULL
    assert ok.eddy_source == SOURCE_EXTERNAL
    assert ok.external_factor == pytest.approx(0.0123)
    c.sheath_eddy_external_frequency_hz = 60.0 if c.frequency_hz != 60.0 else 50.0
    stale = resolve_sheath_loss_completeness(project, base)
    assert stale.authority == AUTHORITY_BLOCKED
    assert "STALE_EXTERNAL_LAMBDA1_EDDY_FREQUENCY" in stale.reason_codes


def test_external_fields_round_trip() -> None:
    project = ProjectData()
    c = project.cable
    c.sheath_eddy_external_factor = 0.011
    c.sheath_eddy_external_source_type = "USER_STANDARD_CALCULATION"
    c.sheath_eddy_external_reference = "REF-X"
    c.sheath_eddy_external_frequency_hz = 50.0
    c.sheath_eddy_external_sheath_temperature_c = 62.0
    c.sheath_eddy_external_d_mm = 86.0
    c.sheath_eddy_external_s_mm = 110.0
    c.sheath_eddy_external_formation_assumption = "CUSTOM VERIFIED"
    loaded = ProjectData.from_dict(project.to_dict())
    assert loaded.cable.sheath_eddy_external_factor == pytest.approx(0.011)
    assert loaded.cable.sheath_eddy_external_reference == "REF-X"
    assert loaded.cable.sheath_eddy_external_formation_assumption == "CUSTOM VERIFIED"
