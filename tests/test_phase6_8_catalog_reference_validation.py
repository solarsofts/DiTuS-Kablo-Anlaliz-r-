from __future__ import annotations

from copy import deepcopy

from ucd.calculations.catalog_reference_validation import validate_catalog_reference_rating
from ucd.calculations.cable_selection import reference_ampacity_details
from ucd.models.project import ProjectData, RouteSection

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
from synthetic_catalog_factory import build_synthetic_catalog_library  # noqa: E402


def _record():
    record = deepcopy(build_synthetic_catalog_library().records[0])
    record.reference_conditions.update({
        "soil_temperature_c": 20.0,
        "burial_depth_m": 0.70,
        "soil_thermal_resistivity_km_w": 1.0,
        "load_factor": 1.0,
        "cables_per_phase": 1,
        "installation_method": "DIRECT_BURIED",
        "correction_factors": [],
    })
    return record


def _project(*sections: RouteSection) -> ProjectData:
    project = ProjectData()
    project.design_basis.installation_profile = "DIRECT_BURIED_TREFOIL"
    project.route_sections = list(sections) or [
        RouteSection(
            "R1", 100.0, burial_depth_m=0.70,
            soil_thermal_resistivity_km_w=1.0, ambient_temperature_c=20.0,
            resolved_arrangement="TREFOIL",
        )
    ]
    return project


def _rating(record):
    value, _label, key = reference_ampacity_details(record, "DIRECT_BURIED_TREFOIL")
    return value, key


def test_exact_reference_conditions_normalize_with_unity_without_table() -> None:
    record = _record()
    value, key = _rating(record)
    result = validate_catalog_reference_rating(
        record, _project(), reference_ampacity_per_cable_a=value,
        ampacity_key=key, target_parallel_cables_per_phase=1,
    )
    assert result.status == "NORMALIZED_SOURCE_VERIFIED"
    assert result.governing_adjusted_ampacity_a == value
    assert result.source_verified
    assert result.regions[0].combined_factor == 1.0


def test_parallel_count_is_not_bare_multiplication_without_grouping_factor() -> None:
    record = _record()
    value, key = _rating(record)
    result = validate_catalog_reference_rating(
        record, _project(), reference_ampacity_per_cable_a=value,
        ampacity_key=key, target_parallel_cables_per_phase=2,
    )
    assert result.arithmetic_total_ampacity_a == 2 * value
    assert result.governing_adjusted_ampacity_a is None
    assert result.status == "REFERENCE_ONLY_INCOMPLETE"
    assert "grouping_parallel" in result.regions[0].missing_parameters


def test_source_verified_grouping_factor_normalizes_parallel_rating() -> None:
    record = _record()
    record.reference_conditions["correction_factors"] = [{
        "factor_id": "GROUP-2",
        "parameter": "grouping_parallel",
        "reference_value": 1,
        "target_value": 2,
        "factor": 0.92,
        "source_type": "LICENSED_STANDARD_USER_ENTRY",
        "source_reference": "Licensed table row entered by user",
    }]
    value, key = _rating(record)
    result = validate_catalog_reference_rating(
        record, _project(), reference_ampacity_per_cable_a=value,
        ampacity_key=key, target_parallel_cables_per_phase=2,
    )
    assert result.status == "NORMALIZED_SOURCE_VERIFIED"
    assert result.source_verified
    assert abs(result.governing_adjusted_ampacity_a - value * 2 * 0.92) < 1e-9


def test_route_regions_use_explicit_factors_and_governing_minimum() -> None:
    record = _record()
    record.reference_conditions["correction_factors"] = [
        {
            "factor_id": "TEMP-25", "parameter": "soil_temperature_c",
            "reference_value": 20.0, "target_value": 25.0, "factor": 0.96,
            "source_type": "USER_VERIFIED", "source_reference": "User licensed source A",
        },
        {
            "factor_id": "TEMP-30", "parameter": "soil_temperature_c",
            "reference_value": 20.0, "target_value": 30.0, "factor": 0.90,
            "source_type": "USER_VERIFIED", "source_reference": "User licensed source A",
        },
        {
            "factor_id": "DEPTH-1", "parameter": "burial_depth_m",
            "reference_value": 0.70, "target_value": 1.0, "factor": 0.97,
            "source_type": "USER_VERIFIED", "source_reference": "User licensed source B",
        },
        {
            "factor_id": "RHO-12", "parameter": "soil_thermal_resistivity_km_w",
            "reference_value": 1.0, "target_value": 1.2, "factor": 0.94,
            "source_type": "USER_VERIFIED", "source_reference": "User licensed source C",
        },
    ]
    project = _project(
        RouteSection("R1", 100.0, burial_depth_m=1.0, soil_thermal_resistivity_km_w=1.2,
                     ambient_temperature_c=25.0, resolved_arrangement="TREFOIL", thermal_region_id="TR1"),
        RouteSection("R2", 100.0, burial_depth_m=1.0, soil_thermal_resistivity_km_w=1.2,
                     ambient_temperature_c=30.0, resolved_arrangement="TREFOIL", thermal_region_id="TR2"),
    )
    value, key = _rating(record)
    result = validate_catalog_reference_rating(
        record, project, reference_ampacity_per_cable_a=value,
        ampacity_key=key, target_parallel_cables_per_phase=1,
    )
    assert result.status == "NORMALIZED_SOURCE_VERIFIED"
    expected_r1 = value * 0.96 * 0.97 * 0.94
    expected_r2 = value * 0.90 * 0.97 * 0.94
    assert abs(result.regions[0].adjusted_total_ampacity_a - expected_r1) < 1e-9
    assert abs(result.regions[1].adjusted_total_ampacity_a - expected_r2) < 1e-9
    assert abs(result.governing_adjusted_ampacity_a - expected_r2) < 1e-9
    assert result.governing_region_id == "TR2"


def test_assumption_factor_is_calculable_but_not_source_verified() -> None:
    record = _record()
    record.reference_conditions["correction_factors"] = [{
        "factor_id": "TEMP-25",
        "parameter": "soil_temperature_c",
        "reference_value": 20.0,
        "target_value": 25.0,
        "factor": 0.96,
        "source_type": "ENGINEERING_ASSUMPTION",
        "source_reference": "",
    }]
    project = _project(RouteSection(
        "R1", 100.0, burial_depth_m=0.70, soil_thermal_resistivity_km_w=1.0,
        ambient_temperature_c=25.0, resolved_arrangement="TREFOIL",
    ))
    value, key = _rating(record)
    result = validate_catalog_reference_rating(
        record, project, reference_ampacity_per_cable_a=value,
        ampacity_key=key, target_parallel_cables_per_phase=1,
    )
    assert result.status == "NORMALIZED_CONDITIONAL"
    assert not result.source_verified
    assert result.governing_adjusted_ampacity_a is not None


def test_nonunity_catalog_load_factor_requires_iec60853_not_scalar_factor() -> None:
    record = _record()
    record.reference_conditions["load_factor"] = 0.75
    value, key = _rating(record)
    result = validate_catalog_reference_rating(
        record, _project(), reference_ampacity_per_cable_a=value,
        ampacity_key=key, target_parallel_cables_per_phase=1,
    )
    assert result.status == "CYCLIC_REFERENCE_REQUIRES_IEC60853"
    assert result.governing_adjusted_ampacity_a is None
    assert "steady_state_load_factor" in result.regions[0].missing_parameters


def test_physical_model_comparison_is_directional_not_acceptance_tolerance() -> None:
    record = _record()
    value, key = _rating(record)
    result = validate_catalog_reference_rating(
        record, _project(), reference_ampacity_per_cable_a=value,
        ampacity_key=key, target_parallel_cables_per_phase=1,
        physical_model_ampacity_a=value - 25.0,
    )
    assert result.physical_comparison_status == "PHYSICAL_MODEL_LOWER"
    assert result.physical_minus_catalog_a == -25.0
    assert result.physical_minus_catalog_percent < 0
