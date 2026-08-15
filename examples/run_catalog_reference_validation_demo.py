from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.catalog_reference_validation import validate_catalog_reference_rating  # noqa: E402
from ucd.calculations.cable_selection import reference_ampacity_details  # noqa: E402
from ucd.models.project import ProjectData, RouteSection  # noqa: E402
from synthetic_catalog_factory import build_synthetic_catalog_library  # noqa: E402


def main() -> int:
    record = deepcopy(build_synthetic_catalog_library().records[0])
    record.reference_conditions["correction_factors"] = [
        {
            "factor_id": "SYN-TEMP-25",
            "parameter": "soil_temperature_c",
            "reference_value": 20.0,
            "target_value": 25.0,
            "factor": 0.96,
            "source_type": "SYNTHETIC_DEMO",
            "source_reference": "Sentetik FAZ 6.8 demo faktörü; normatif tablo değildir.",
        },
        {
            "factor_id": "SYN-TEMP-30",
            "parameter": "soil_temperature_c",
            "reference_value": 20.0,
            "target_value": 30.0,
            "factor": 0.90,
            "source_type": "SYNTHETIC_DEMO",
            "source_reference": "Sentetik FAZ 6.8 demo faktörü; normatif tablo değildir.",
        },
        {
            "factor_id": "SYN-DEPTH-1",
            "parameter": "burial_depth_m",
            "reference_value": 0.7,
            "target_value": 1.0,
            "factor": 0.97,
            "source_type": "SYNTHETIC_DEMO",
            "source_reference": "Sentetik FAZ 6.8 demo faktörü; normatif tablo değildir.",
        },
        {
            "factor_id": "SYN-RHO-12",
            "parameter": "soil_thermal_resistivity_km_w",
            "reference_value": 1.0,
            "target_value": 1.2,
            "factor": 0.94,
            "source_type": "SYNTHETIC_DEMO",
            "source_reference": "Sentetik FAZ 6.8 demo faktörü; normatif tablo değildir.",
        },
    ]
    project = ProjectData()
    project.design_basis.installation_profile = "DIRECT_BURIED_TREFOIL"
    project.route_sections = [
        RouteSection(
            "DEMO-R1", 100.0, burial_depth_m=1.0,
            soil_thermal_resistivity_km_w=1.2, ambient_temperature_c=25.0,
            resolved_arrangement="TREFOIL", thermal_region_id="TR-DEMO-1",
        ),
        RouteSection(
            "DEMO-R2", 100.0, burial_depth_m=1.0,
            soil_thermal_resistivity_km_w=1.2, ambient_temperature_c=30.0,
            resolved_arrangement="TREFOIL", thermal_region_id="TR-DEMO-2",
        ),
    ]
    ampacity, _label, key = reference_ampacity_details(record, project.design_basis.installation_profile)
    result = validate_catalog_reference_rating(
        record,
        project,
        reference_ampacity_per_cable_a=ampacity,
        ampacity_key=key,
        target_parallel_cables_per_phase=1,
    )
    payload = {
        "format": "DITUS_CATALOG_REFERENCE_VALIDATION_DEMO",
        "version": "0.16.9.4.27",
        "notice": "Tamamen sentetik düzeltme faktörleri; normatif IEC tablo verisi değildir.",
        "result": asdict(result),
    }
    target = ROOT / "examples" / "catalog_reference_validation_demo.latest.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)
    print(result.status, result.governing_region_id, result.governing_adjusted_ampacity_a)
    return 0 if result.status == "NORMALIZED_CONDITIONAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
