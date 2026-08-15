from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ucd.calculations.catalog_comparison import compare_catalog_candidates, write_catalog_comparison_report
from ucd.models.project import ProjectData
from synthetic_catalog_factory import merge_synthetic_catalogs


def signature(result) -> dict:
    return {
        "project_code": result.project_code,
        "system_voltage_kv": result.system_voltage_kv,
        "design_current_a": round(result.design_current_a, 6),
        "candidates": [
            {
                "rank": item.rank,
                "manufacturer": item.manufacturer,
                "model": item.model,
                "material": item.conductor_material,
                "parallel": item.parallel_cables_per_phase,
                "reference_ampacity_arithmetic_a": round(item.combined_reference_ampacity_a, 6),
                "reference_ampacity_normalized_a": (
                    None if item.adjusted_reference_ampacity_a is None else round(item.adjusted_reference_ampacity_a, 6)
                ),
                "reference_validation_status": item.reference_validation_status,
                "normalized_margin_a": (
                    None if item.normalized_design_margin_a is None else round(item.normalized_design_margin_a, 6)
                ),
                "screening_status": item.screening_status,
                "voltage_drop_percent": None if item.voltage_drop_percent is None else round(item.voltage_drop_percent, 9),
                "completion": item.completion_status,
                "gates": item.iteration_gate_status,
                "verification": item.verification_status,
                "catalog_present": item.catalog_scalar_count,
                "catalog_missing": item.catalog_scalar_missing_count,
            }
            for item in result.candidates
        ],
    }


def main() -> int:
    examples = ROOT / "examples"
    source = examples / "synthetic_20km_line.ucd.json"
    project = ProjectData.from_dict(json.loads(source.read_text(encoding="utf-8")))
    merge_synthetic_catalogs(project.cable_library)
    result = compare_catalog_candidates(project)
    write_catalog_comparison_report(result, examples, "catalog_comparison_report.latest")
    current = signature(result)
    result_path = examples / "catalog_comparison_signature.latest.json"
    result_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    expected_path = examples / "catalog_comparison_expected_v0.16.9.4.27.json"
    if expected_path.exists():
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        if current != expected:
            print("FAIL: catalog comparison regression signature changed")
            print(json.dumps(current, ensure_ascii=False, indent=2))
            return 1
    print("PASS: 3 sentetik Üretici A/B/C adayı 20 km hat için karşılaştırıldı; nihai onay verilmedi.")
    for item in result.candidates:
        print(
            f"{item.rank}. {item.manufacturer} {item.model} | {item.conductor_material} | "
            f"ΔV={item.voltage_drop_percent if item.voltage_drop_percent is not None else 'N/A'} | "
            f"{item.verification_status}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
