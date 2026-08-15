from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from importlib.resources import files
import json
from math import ceil, pi, sqrt
from typing import Any

from ucd.calculations.cable_physical_parameters import material_alpha_20_per_c

from ucd.models.project import (
    CABLE_SOURCE_CALCULATED,
    CABLE_SOURCE_STANDARD_DERIVED,
    CABLE_SOURCE_USER_ASSUMPTION,
    CABLE_STATUS_CONDITIONAL,
    CableCatalogRecord,
    CableData,
    CableLayerData,
    CableLibraryData,
    CableParameterSource,
)


PROFILE_RESOURCE = "generic_cable_profiles.json"
DIAMETER_RELATIVE_TOLERANCE = 0.05
DIAMETER_ABSOLUTE_TOLERANCE_MM = 2.0
MASS_RELATIVE_TOLERANCE = 0.10
MASS_ABSOLUTE_TOLERANCE_KG_KM = 50.0


def load_generic_profile_data() -> dict[str, Any]:
    resource = files("ucd.resources").joinpath(PROFILE_RESOURCE)
    return json.loads(resource.read_text(encoding="utf-8"))




def thermal_resistivity_for_material(material: str) -> float | None:
    """Resolve known cable-layer thermal resistivity from the central profile.

    Conductive metallic layers intentionally return ``None`` because their
    radial thermal contribution is not represented by the insulating-material
    rho table. Unknown materials remain untouched and must carry explicit
    provenance.
    """
    data = load_generic_profile_data()
    aliases = {
        "XLPE": "XLPE",
        "SEMICONDUCTIVE XLPE": "SEMICON_XLPE",
        "SEMICON XLPE": "SEMICON_XLPE",
        "WATER BLOCKING TAPE": "WATER_TAPE",
        "WATER-BLOCKING TAPE": "WATER_TAPE",
        "PVC": "PVC",
        "PE": "PE",
        "POLYETHYLENE": "PE",
    }
    key = aliases.get(str(material or "").strip().upper())
    if not key:
        return None
    return float(data["materials"][key]["thermal_resistivity_km_w"])

def profile_id_for_voltage(voltage_class: str) -> str:
    text = str(voltage_class or "").upper().replace(" ", "")
    if "12/20" in text or "12.7/22" in text or "(24)" in text:
        return "MV24"
    if "20.3/35" in text or "20.8/36" in text or "40.5" in text:
        return "MV40K5"
    return "HV170"


def _material_key(material: str) -> str:
    text = str(material or "").strip().upper()
    if text in {"AL", "ALUMINIUM", "ALUMINUM"}:
        return "AL"
    if text in {"CU", "COPPER"}:
        return "CU"
    return text


def _round_up(value: float, increment: float) -> float:
    step = max(float(increment), 1e-9)
    return ceil(float(value) / step - 1e-12) * step


def conductor_envelope_diameter_mm(area_mm2: float, fill_factor: float) -> float:
    if area_mm2 <= 0:
        raise ValueError("İletken kesiti sıfırdan büyük olmalıdır.")
    fill = min(1.0, max(0.50, float(fill_factor)))
    return sqrt(4.0 * float(area_mm2) / (pi * fill))


def outer_sheath_thickness_mm(under_sheath_diameter_mm: float, profile: dict[str, Any]) -> float:
    formula = dict(profile.get("outer_sheath_formula", {}))
    coefficient = float(formula.get("coefficient", 0.035))
    intercept = float(formula.get("intercept_mm", 1.0))
    minimum = float(formula.get("minimum_mm", 3.0))
    rounding = float(formula.get("rounding_mm", 0.1))
    nominal = max(minimum, coefficient * float(under_sheath_diameter_mm) + intercept)
    return _round_up(nominal, rounding)


def generic_parameter_sources(voltage_class: str = "87/150 (170) kV") -> list[CableParameterSource]:
    profile_data = load_generic_profile_data()
    profile_id = profile_id_for_voltage(voltage_class)
    voltage_profile = profile_data["voltage_profiles"][profile_id]
    voltage_source = str(voltage_profile["standard_source_id"])
    voltage_standard = str(voltage_profile["standard"])
    return [
        CableParameterSource(
            "SRC-STD-IEC60228",
            CABLE_SOURCE_STANDARD_DERIVED,
            "IEC 60228 — Conductors of insulated cables",
            "profile reference",
            notes=(
                "Nominal kesit, iletken malzemesi ve direnç sınıfı için normatif kaynak sınıfı. "
                "Lisanslı standart tablosu paket içinde yeniden yayımlanmaz."
            ),
        ),
        CableParameterSource(
            "SRC-STD-IEC60287-2-1",
            CABLE_SOURCE_STANDARD_DERIVED,
            "IEC 60287-2-1 — Thermal resistance",
            "material profile",
            notes=(
                "XLPE/PE/PVC ısıl özdirençleri merkezi malzeme profilinden çözülür; "
                "kablo kaydına serbest elle yazılmaz."
            ),
        ),
        CableParameterSource(
            voltage_source,
            CABLE_SOURCE_STANDARD_DERIVED,
            f"{voltage_standard} — voltage construction profile",
            "profile reference",
            notes=(
                "Gerilim sınıfı yapı profilinin normatif kaynak kimliği. Sayısal tablo değerleri "
                "lisanslı kopyadan son doğrulamaya kadar CONDITIONAL tutulur."
            ),
        ),
        CableParameterSource(
            "SRC-ASSUME-PHASE2-CONSTRUCTION",
            CABLE_SOURCE_USER_ASSUMPTION,
            "DiTuS FAZ 2 jenerik konstrüksiyon varsayımları",
            "0.16.9.4.34",
            notes=(
                "Yarı iletken ve bant kalınlıkları, sıkıştırma/doluluk, tel yerleşimi ve YG metalik "
                "sheath ayrıntıları üretici verisi değildir."
            ),
        ),
        CableParameterSource(
            "SRC-CALC-PARAMETRIC-GENERATOR",
            CABLE_SOURCE_CALCULATED,
            "DiTuS parametrik kablo katman üreteci",
            "0.16.9.4.34",
            notes=(
                "Katman çapları, ekran tel geometrisi, dış kılıf kalınlığı, hesaplanan dış çap ve "
                "kütle bu üreteç tarafından deterministik olarak oluşturulur."
            ),
        ),
    ]


def _screen_wire_geometry(area_mm2: float) -> tuple[int, float]:
    target_wire_d = 1.0
    count = max(1, int(round(float(area_mm2) / (pi * target_wire_d**2 / 4.0))))
    wire_d = sqrt(4.0 * float(area_mm2) / (pi * count))
    return count, wire_d


def build_parametric_layers(
    conductor_material: str = "Cu",
    conductor_area_mm2: float = 1200.0,
    *,
    voltage_class: str = "87/150 (170) kV",
    screen_area_mm2: float | None = None,
    screen_profile: str = "",
    stranding_type: str = "",
) -> list[CableLayerData]:
    data = load_generic_profile_data()
    profile_id = profile_id_for_voltage(voltage_class)
    profile = data["voltage_profiles"][profile_id]
    materials = data["materials"]
    material_key = _material_key(conductor_material)
    if material_key not in {"AL", "CU"}:
        raise ValueError(f"Desteklenmeyen iletken malzemesi: {conductor_material}")

    area = float(conductor_area_mm2)
    if screen_area_mm2 is None or float(screen_area_mm2) <= 0:
        if profile_id == "MV24":
            screen_area_mm2 = 25.0 if area <= 240.0 else 35.0
        elif profile_id == "MV40K5":
            screen_area_mm2 = 25.0 if area <= 240.0 else (35.0 if area <= 400.0 else 50.0)
        else:
            screen_area_mm2 = 150.0
    screen_area = float(screen_area_mm2)

    conductor_d = conductor_envelope_diameter_mm(area, float(profile["conductor_fill_factor"]))
    inner_semicon_outer = conductor_d + 2.0 * float(profile["inner_semicon_thickness_mm"])
    insulation_outer = inner_semicon_outer + 2.0 * float(profile["insulation_thickness_mm"])
    outer_semicon_outer = insulation_outer + 2.0 * float(profile["outer_semicon_thickness_mm"])
    bedding_outer = outer_semicon_outer + 2.0 * float(profile["tape_bedding_thickness_mm"])

    is_hv_sheath = profile_id == "HV170" or str(screen_profile).upper().startswith("HV-")
    if is_hv_sheath:
        # Equivalent continuous metallic sheath annulus preserving the selected
        # metal area; exact sheath construction remains an explicit assumption.
        screen_outer = sqrt(bedding_outer**2 + 4.0 * screen_area / pi)
        wire_count = 0
        wire_d = 0.0
        screen_type = "METALLIC_SHEATH"
        screen_name = "Jenerik metalik sheath — HV-BOND-01"
    else:
        wire_count, wire_d = _screen_wire_geometry(screen_area)
        screen_outer = bedding_outer + 2.0 * wire_d
        screen_type = "METALLIC_SCREEN"
        screen_name = "Bakır tel ekran"

    sheath_material_key = str(profile["outer_sheath_material"]).upper()
    sheath_thickness = outer_sheath_thickness_mm(screen_outer, profile)
    overall = screen_outer + 2.0 * sheath_thickness

    calc_source = "SRC-CALC-PARAMETRIC-GENERATOR"
    assume_source = "SRC-ASSUME-PHASE2-CONSTRUCTION"
    rho_source = "SRC-STD-IEC60287-2-1"
    voltage_source = str(profile["standard_source_id"])

    return [
        CableLayerData(
            "L01", "İletken", "CONDUCTOR", 0.0, conductor_d,
            materials[material_key]["label"], conductor_area_mm2=area,
            source_id=calc_source,
            notes=(
                f"Nominal metal kesiti IEC 60228 sınıfı; fiziksel zarf çapı "
                f"fill_factor={float(profile['conductor_fill_factor']):.3f} varsayımıyla CALC."
            ),
        ),
        CableLayerData(
            "L02", "İç yarı iletken", "CONDUCTOR_SCREEN", conductor_d, inner_semicon_outer,
            materials["SEMICON_XLPE"]["label"],
            float(materials["SEMICON_XLPE"]["thermal_resistivity_km_w"]),
            source_id=assume_source,
            notes=f"Kalınlık ASSUME; ısıl özdirenç {rho_source} profilinden.",
        ),
        CableLayerData(
            "L03", "XLPE izolasyon", "INSULATION", inner_semicon_outer, insulation_outer,
            materials["XLPE"]["label"], float(materials["XLPE"]["thermal_resistivity_km_w"]),
            2.3, 0.001, source_id=voltage_source,
            notes=(
                f"Gerilim profili {profile_id}; tablo durumu {profile['table_status']}; "
                f"ısıl özdirenç {rho_source} profilinden."
            ),
        ),
        CableLayerData(
            "L04", "Dış yarı iletken", "INSULATION_SCREEN", insulation_outer, outer_semicon_outer,
            materials["SEMICON_XLPE"]["label"],
            float(materials["SEMICON_XLPE"]["thermal_resistivity_km_w"]),
            source_id=assume_source,
            notes=f"Kalınlık ASSUME; ısıl özdirenç {rho_source} profilinden.",
        ),
        CableLayerData(
            "L05", "Bantlar / bedding", "WATER_BLOCKING", outer_semicon_outer, bedding_outer,
            materials["WATER_TAPE"]["label"],
            float(materials["WATER_TAPE"]["thermal_resistivity_km_w"]),
            source_id=assume_source,
            notes="Bant/bedding kalınlığı ve eşdeğer malzeme ASSUME.",
        ),
        CableLayerData(
            "L06", screen_name, screen_type, bedding_outer, screen_outer,
            "Cu", conductor_area_mm2=screen_area, wire_count=wire_count,
            wire_diameter_mm=wire_d, source_id=assume_source,
            notes=(
                f"Ekran/sheath profili {screen_profile or ('HV-BOND-01' if is_hv_sheath else 'CWS')}; "
                "toplam metal kesiti tohum girdisi, geometri CALC."
            ),
        ),
        CableLayerData(
            "L07", "Dış kılıf", "OUTER_SHEATH", screen_outer, overall,
            materials[sheath_material_key]["label"],
            float(materials[sheath_material_key]["thermal_resistivity_km_w"]),
            source_id=calc_source,
            notes=(
                f"Kalınlık {sheath_thickness:.3f} mm; dış çap girdisinden kalan doldurulmadı. "
                f"Malzeme ısıl özdirenci {rho_source} profilinden."
            ),
        ),
    ]


def estimate_cable_mass_kg_km(cable: CableData) -> float:
    data = load_generic_profile_data()
    materials = data["materials"]
    aliases = {
        "AL": "AL", "ALUMINIUM": "AL", "ALUMINUM": "AL",
        "CU": "CU", "COPPER": "CU",
        "XLPE": "XLPE", "SEMICONDUCTIVE XLPE": "SEMICON_XLPE",
        "WATER BLOCKING TAPE": "WATER_TAPE", "PVC": "PVC", "PE": "PE",
    }
    total = 0.0
    for layer in cable.layers:
        material_key = aliases.get(str(layer.material or "").strip().upper())
        if material_key not in materials:
            continue
        density = float(materials[material_key]["density_g_cm3"])
        layer_type = str(layer.layer_type or "").upper()
        if layer_type == "CONDUCTOR" and layer.conductor_area_mm2 > 0:
            area = float(layer.conductor_area_mm2)
        elif layer_type in {"METALLIC_SCREEN", "WIRE_SCREEN", "METALLIC_SHEATH"} and layer.conductor_area_mm2 > 0:
            area = float(layer.conductor_area_mm2)
        else:
            area = pi * (float(layer.outer_diameter_mm) ** 2 - float(layer.inner_diameter_mm) ** 2) / 4.0
        total += max(0.0, area) * density
    return total


def evaluate_catalog_validation_gates(record: CableCatalogRecord, cable: CableData) -> dict[str, Any]:
    calculated_diameter = float(cable.overall_diameter_mm)
    calculated_mass = estimate_cable_mass_kg_km(cable)
    published_diameter = record.catalog_dimensions.get("overall_diameter_mm")
    published_mass = record.catalog_dimensions.get("net_weight_kg_km")
    if published_mass is None:
        published_mass = record.catalog_dimensions.get("weight_kg_km")

    gates: dict[str, Any] = {
        "calculated_overall_diameter_mm": round(calculated_diameter, 6),
        "calculated_mass_kg_km": round(calculated_mass, 6),
        "diameter_gate": {"status": "NOT_APPLICABLE"},
        "mass_gate": {"status": "NOT_APPLICABLE"},
    }
    failures: list[str] = []

    if isinstance(published_diameter, (int, float)) and float(published_diameter) > 0:
        published = float(published_diameter)
        absolute = abs(calculated_diameter - published)
        relative = absolute / published
        tolerance = max(DIAMETER_ABSOLUTE_TOLERANCE_MM, DIAMETER_RELATIVE_TOLERANCE * published)
        status = "PASS" if absolute <= tolerance + 1e-12 else "FAIL"
        gates["diameter_gate"] = {
            "status": status,
            "published_mm": published,
            "calculated_mm": round(calculated_diameter, 6),
            "absolute_deviation_mm": round(absolute, 6),
            "relative_deviation_percent": round(relative * 100.0, 6),
            "tolerance_mm": round(tolerance, 6),
        }
        if status == "FAIL":
            failures.append(
                f"DIAMETER_GATE: hesaplanan {calculated_diameter:.3f} mm, yayımlanmış {published:.3f} mm; "
                f"sapma {absolute:.3f} mm (%{relative*100:.2f})."
            )

    if isinstance(published_mass, (int, float)) and float(published_mass) > 0:
        published = float(published_mass)
        absolute = abs(calculated_mass - published)
        relative = absolute / published
        tolerance = max(MASS_ABSOLUTE_TOLERANCE_KG_KM, MASS_RELATIVE_TOLERANCE * published)
        status = "PASS" if absolute <= tolerance + 1e-12 else "FAIL"
        gates["mass_gate"] = {
            "status": status,
            "published_kg_km": published,
            "calculated_kg_km": round(calculated_mass, 6),
            "absolute_deviation_kg_km": round(absolute, 6),
            "relative_deviation_percent": round(relative * 100.0, 6),
            "tolerance_kg_km": round(tolerance, 6),
        }
        if status == "FAIL":
            failures.append(
                f"MASS_GATE: hesaplanan {calculated_mass:.1f} kg/km, yayımlanmış {published:.1f} kg/km; "
                f"sapma {absolute:.1f} kg/km (%{relative*100:.2f})."
            )

    gates["status"] = "FAIL" if failures else (
        "PASS" if any(gates[key]["status"] == "PASS" for key in ("diameter_gate", "mass_gate"))
        else "NOT_APPLICABLE"
    )
    gates["failures"] = failures
    return gates


def build_generic_cable(
    *,
    record_id: str,
    profile_id: str,
    material: str,
    area_mm2: float,
    screen_area_mm2: float,
    screen_profile: str,
    stranding: str,
) -> CableData:
    data = load_generic_profile_data()
    profile = data["voltage_profiles"][profile_id]
    material_key = _material_key(material)
    layers = build_parametric_layers(
        material,
        area_mm2,
        voltage_class=str(profile["voltage_class"]),
        screen_area_mm2=screen_area_mm2,
        screen_profile=screen_profile,
        stranding_type=stranding,
    )
    cable = CableData(
        cable_id=record_id,
        manufacturer="JENERİK",
        series="Standart-Türevli Koşullu Şablon",
        model=f"{material} {area_mm2:g}/{screen_area_mm2:g} mm² {profile['voltage_class']}",
        voltage_class=str(profile["voltage_class"]),
        applicable_standard=str(profile["standard"]),
        catalog_record_id=record_id,
        data_status=CABLE_STATUS_CONDITIONAL,
        name=f"Jenerik {material} {area_mm2:g}/{screen_area_mm2:g} mm²",
        voltage_kv=float(profile["system_voltage_kv"]),
        conductor_material=str(data["materials"][material_key]["label"]),
        conductor_area_mm2=float(area_mm2),
        temperature_coefficient_20_per_c=material_alpha_20_per_c(material),
        conductor_stranding_type=stranding,
        conductor_segment_count=6 if stranding.upper() == "MILLIKEN" else 1,
        sheath_material="Cu",
        sheath_cross_section_mm2=float(screen_area_mm2),
        sheath_temperature_coefficient_20_per_c=material_alpha_20_per_c("Cu"),
        insulation="XLPE",
        layers=layers,
        parameter_sources=generic_parameter_sources(str(profile["voltage_class"])),
        validation_notes=[
            "Jenerik tohum şablonudur; üretici katalog ürünü değildir.",
            "Yarı iletken, bant, sıkıştırma ve metalik ekran/sheath ayrıntıları ASSUME sınıfındadır.",
            f"Standart tablo durumu: {profile['table_status']}.",
        ],
    )
    from ucd.calculations.cable_library import synchronize_cable_from_layers, update_cable_validation_state

    synchronize_cable_from_layers(cable)
    update_cable_validation_state(cable)
    cable.data_status = CABLE_STATUS_CONDITIONAL
    return cable


def build_generic_template_library() -> CableLibraryData:
    data = load_generic_profile_data()
    records: list[CableCatalogRecord] = []
    source_by_id: dict[str, CableParameterSource] = {}
    for spec in data["templates"]:
        cable = build_generic_cable(**spec)
        for source in cable.parameter_sources:
            source_by_id[source.source_id] = deepcopy(source)
        record = CableCatalogRecord(
            record_id=str(spec["record_id"]),
            manufacturer="JENERİK",
            series="Standart-Türevli Koşullu Şablon",
            model=cable.model,
            voltage_class=cable.voltage_class,
            conductor_material=cable.conductor_material,
            conductor_area_mm2=cable.conductor_area_mm2,
            construction_type=cable.construction_type,
            standard=cable.applicable_standard,
            status=CABLE_STATUS_CONDITIONAL,
            cable_snapshot=asdict(cable),
            source_ids=[source.source_id for source in cable.parameter_sources],
            tags=["GENERIC_TEMPLATE", "NO_MANUFACTURER_DATA", "STANDARD_DERIVED", "CONDITIONAL"],
            notes=(
                "Üretici ürünü değildir. Parametrik üreteç tohumu ve regresyon/ön tasarım kaydıdır; "
                "üretici katalog/çizim/test verisiyle doğrulanmadan nihai tasarımda kullanılamaz."
            ),
            source_quality="GENERIC_CONDITIONAL",
            reference_conditions={
                "generator": "DITUS_PHASE2_PARAMETRIC",
                "validation_gates": evaluate_catalog_validation_gates(
                    CableCatalogRecord(
                        record_id=str(spec["record_id"]), manufacturer="JENERİK", series="", model="",
                        voltage_class=cable.voltage_class, conductor_material=cable.conductor_material,
                        conductor_area_mm2=cable.conductor_area_mm2,
                    ),
                    cable,
                ),
            },
        )
        records.append(record)
    return CableLibraryData(
        records=records,
        sources=sorted(source_by_id.values(), key=lambda item: item.source_id),
        selected_record_id=records[0].record_id if records else "",
        package_name="DiTuS jenerik kablo şablonları",
        package_revision="0.16.9.4.34",
        package_source="BUILTIN_GENERIC_TEMPLATES",
        builtin_catalogs_loaded=True,
    )
