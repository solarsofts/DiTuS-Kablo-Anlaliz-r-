from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ucd.calculations.cable_library import merge_catalog_library, normalize_catalog_library
from ucd.calculations.cable_template_generator import (
    build_generic_cable,
    estimate_cable_mass_kg_km,
)
from ucd.models.project import (
    CABLE_SOURCE_CATALOG,
    CABLE_STATUS_CONDITIONAL,
    CableCatalogRecord,
    CableLibraryData,
    CableParameterSource,
)


def _record(
    *,
    record_id: str,
    manufacturer: str,
    material: str,
    rdc20: float,
    ampacity_trefoil: float,
    ampacity_flat: float,
    inductance_trefoil: float,
    inductance_flat: float,
    diameter_factor: float,
    mass_factor: float,
) -> tuple[CableCatalogRecord, CableParameterSource]:
    cable = build_generic_cable(
        record_id=record_id,
        profile_id="MV40K5",
        material=material,
        area_mm2=400.0,
        screen_area_mm2=35.0,
        screen_profile="CWS",
        stranding="COMPACT_ROUND",
    )
    cable.manufacturer = manufacturer
    cable.series = "Sentetik OG Aday Serisi"
    cable.model = f"Sentetik {material} 1x400/35"
    cable.name = f"{manufacturer} sentetik aday kablosu"
    cable.catalog_record_id = record_id
    cable.data_status = CABLE_STATUS_CONDITIONAL
    cable.dc_resistance_20_ohm_km = rdc20
    cable.validation_notes.append(
        "Tamamen sentetik katalog adayıdır; gerçek üretici veya ürünle ilişkili değildir."
    )
    source_id = f"SRC-{record_id}"
    source = CableParameterSource(
        source_id=source_id,
        source_type=CABLE_SOURCE_CATALOG,
        document_title="DiTuS sentetik katalog karşılaştırma veri seti",
        document_revision="FAZ 2",
        page_reference=f"Sentetik satır {manufacturer[-1]}",
        verified=False,
        notes="Regresyon ve arayüz gösterimi içindir; kamuya açık üretici verisi değildir.",
    )
    cable.parameter_sources.append(deepcopy(source))
    calculated_mass = estimate_cable_mass_kg_km(cable)
    record = CableCatalogRecord(
        record_id=record_id,
        manufacturer=manufacturer,
        series=cable.series,
        model=cable.model,
        voltage_class=cable.voltage_class,
        conductor_material=cable.conductor_material,
        conductor_area_mm2=cable.conductor_area_mm2,
        construction_type=cable.construction_type,
        standard="SYNTHETIC_DEMO_PROFILE",
        status=CABLE_STATUS_CONDITIONAL,
        cable_snapshot=asdict(cable),
        source_ids=[source_id],
        tags=["REAL_CATALOG", "SYNTHETIC_DATA", "NO_REAL_MANUFACTURER"],
        notes=(
            "Tamamen sentetik Üretici A/B/C karşılaştırma kaydıdır; gerçek katalog, ürün veya "
            "ticari uygunluk iddiası değildir."
        ),
        catalog_dimensions={
            "overall_diameter_mm": round(cable.overall_diameter_mm * diameter_factor, 3),
            "net_weight_kg_km": round(calculated_mass * mass_factor, 1),
            "delivery_length_m": 1000.0,
        },
        catalog_electrical={
            "conductor_rdc20_ohm_km": rdc20,
            "inductance_trefoil_mh_km": inductance_trefoil,
            "inductance_flat_mh_km": inductance_flat,
            "capacitance_uf_km": round(cable.capacitance_uf_km, 6),
            "ampacity_ground_trefoil_a": ampacity_trefoil,
            "ampacity_ground_flat_a": ampacity_flat,
        },
        reference_conditions={
            "soil_temperature_c": 20.0,
            "burial_depth_m": 0.70,
            "soil_thermal_resistivity_km_w": 1.0,
            "load_factor": 1.0,
            "cables_per_phase": 1,
            "arrangement": "TREFOIL",
            "installation_method": "DIRECT_BURIED",
            "arrangement_note": "Tamamen sentetik karşılaştırma koşulu; düzeltme faktörü içermez.",
            "correction_factors": [],
        },
        source_quality="SYNTHETIC_DEMO",
        source_page=f"Sentetik satır {manufacturer[-1]}",
    )
    return record, source


def build_synthetic_catalog_library() -> CableLibraryData:
    specs = [
        dict(
            record_id="SYN-MFR-A-MV40K5-AL400-35", manufacturer="Üretici A", material="Al",
            rdc20=0.0778, ampacity_trefoil=545.0, ampacity_flat=558.0,
            inductance_trefoil=0.40, inductance_flat=0.46,
            diameter_factor=1.020, mass_factor=1.050,
        ),
        dict(
            record_id="SYN-MFR-B-MV40K5-AL400-35", manufacturer="Üretici B", material="Al",
            rdc20=0.0754, ampacity_trefoil=571.0, ampacity_flat=584.0,
            inductance_trefoil=0.39, inductance_flat=0.45,
            diameter_factor=0.990, mass_factor=0.970,
        ),
        dict(
            record_id="SYN-MFR-C-MV40K5-CU400-35", manufacturer="Üretici C", material="Cu",
            rdc20=0.0470, ampacity_trefoil=680.0, ampacity_flat=695.0,
            inductance_trefoil=0.38, inductance_flat=0.44,
            diameter_factor=1.010, mass_factor=1.020,
        ),
    ]
    records = []
    sources = []
    for spec in specs:
        record, source = _record(**spec)
        records.append(record)
        sources.append(source)
    library = CableLibraryData(
        records=records,
        sources=sources,
        package_name="DiTuS sentetik Üretici A/B/C katalog adayları",
        package_revision="0.16.9.4.27",
        package_source="GENERATED_SYNTHETIC_DATA",
    )
    return normalize_catalog_library(library)


def merge_synthetic_catalogs(target: CableLibraryData, *, replace: bool = True) -> tuple[int, int]:
    return merge_catalog_library(target, build_synthetic_catalog_library(), replace=replace)
