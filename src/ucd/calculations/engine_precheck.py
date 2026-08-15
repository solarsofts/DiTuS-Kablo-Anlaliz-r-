from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable

from ucd.calculations.model_applicability import evaluate_cable_model_applicability
from ucd.models.project import (
    BONDING_CROSS,
    CABLE_SOURCE_USER_ASSUMPTION,
    ProjectData,
)

GATE_HARD = "HARD"
GATE_SOFT = "SOFT"

CHECK_OK = "OK"
CHECK_MISSING = "MISSING"
CHECK_ASSUMPTION = "ASSUMPTION"

PRECHECK_BLOCKED = "BLOCKED"
PRECHECK_CONDITIONAL = "CONDITIONAL"
PRECHECK_READY = "READY"

MATURITY_SCREENING = "SCREENING"
MATURITY_CONDITIONAL = "CONDITIONAL"
MATURITY_VERIFIED = "VERIFIED"


@dataclass(frozen=True)
class EngineMethodProfile:
    engine_id: str
    display_name: str
    standard_basis: str
    stage_id: str
    workspace_key: str
    model_limit: str = ""


@dataclass(frozen=True)
class EnginePrecheckItem:
    item_id: str
    label: str
    gate: str
    status: str
    detail: str = ""
    owner_stage_id: str = ""
    owner_label: str = ""

    @property
    def missing(self) -> bool:
        return self.status == CHECK_MISSING

    @property
    def assumption(self) -> bool:
        return self.status == CHECK_ASSUMPTION


@dataclass
class EnginePrecheckResult:
    engine_id: str
    method: EngineMethodProfile
    items: list[EnginePrecheckItem] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def hard_missing(self) -> list[EnginePrecheckItem]:
        return [item for item in self.items if item.gate == GATE_HARD and item.missing]

    @property
    def soft_missing(self) -> list[EnginePrecheckItem]:
        return [item for item in self.items if item.gate == GATE_SOFT and item.missing]

    @property
    def assumed_items(self) -> list[EnginePrecheckItem]:
        return [item for item in self.items if item.assumption]

    @property
    def can_run(self) -> bool:
        return not self.hard_missing

    @property
    def status(self) -> str:
        if self.hard_missing:
            return PRECHECK_BLOCKED
        if self.soft_missing or self.assumed_items or self.assumptions:
            return PRECHECK_CONDITIONAL
        return PRECHECK_READY

    @property
    def maturity(self) -> str:
        if self.hard_missing:
            return MATURITY_SCREENING
        if self.soft_missing or self.assumed_items or self.assumptions:
            return MATURITY_CONDITIONAL
        return MATURITY_VERIFIED

    @property
    def primary_owner_stage_id(self) -> str:
        missing = self.hard_missing or self.soft_missing
        return missing[0].owner_stage_id if missing else self.method.stage_id

    def summary(self) -> str:
        if self.status == PRECHECK_BLOCKED:
            return f"Bloke · {len(self.hard_missing)} zorunlu girdi eksik"
        if self.status == PRECHECK_CONDITIONAL:
            count = len(self.soft_missing) + len(self.assumed_items) + len(self.assumptions)
            return f"Koşullu · {count} eksik/varsayım"
        return "Hazır · doğrulanmış girdiler"

    def to_dict(self) -> dict:
        return {
            "engine_id": self.engine_id,
            "method": asdict(self.method),
            "status": self.status,
            "maturity": self.maturity,
            "can_run": self.can_run,
            "items": [asdict(item) for item in self.items],
            "assumptions": list(self.assumptions),
            "notes": list(self.notes),
        }


_BASE_METHODS: dict[str, EngineMethodProfile] = {
    "precheck": EngineMethodProfile(
        "precheck", "DiTuS İlk Elektriksel Ön Eleme",
        "Katalog/kullanıcı girdili dengeli üç faz ön eleme", "precheck", "first_design",
        "Katalog akım kapasitesi nihai IEC 60287/2D güzergâh doğrulaması değildir.",
    ),
    "iec60287": EngineMethodProfile(
        "iec60287", "IEC 60287 Bölgesel Kararlı Durum",
        "IEC 60287 iş akışı; bölgesel T1–T4 ve kayıp bileşenleri", "steady_thermal", "thermal_route",
        "Normatif standardın metni/formülleri kopyalanmaz; uygulama bağımsız sayısal implementasyondur.",
    ),
    "thermal_route": EngineMethodProfile(
        "thermal_route", "IEC 60287 Termal Güzergâh Çözümü",
        "Chainage bazlı bölgesel IEC 60287", "steady_thermal", "thermal_route",
    ),
    "nodal": EngineMethodProfile(
        "nodal", "2D Hücre-Merkezli Sonlu Hacim Termal Çözümü",
        "Kararlı durum çok-malzemeli 2D nodal/FVM", "steady_thermal", "thermal_review",
        "Eksenel ısı akışı yoktur; kesit geçişleri ve HDD giriş/çıkışı yerel 3D gerektirir.",
    ),
    "fault_epr": EngineMethodProfile(
        "fault_epr", "CIGRE TB 797 / IEEE 575 Arıza-EPR Ağı",
        "Power-frequency primitive ağ; IEEE 575 Annex E sınıflandırma yönelimi", "fault_epr", "fault",
        "Dağıtılmış dokunma/adım gerilimi ve tam saha topraklama ağı henüz kapsam dışıdır.",
    ),
    "svl": EngineMethodProfile(
        "svl", "IEEE 575 / CIGRE TB 797 SVL Ön Koordinasyonu",
        "MCOV, TOV, residual, lead düşümü ve enerji ön kontrolü", "svl", "svl",
        "Tam frekans-bağımlı EMT ve doğrusal olmayan MOV zaman alanı enerjisi değildir.",
    ),
    "transient": EngineMethodProfile(
        "transient", "IEC 60853 İş Akışlı Geçici/Çevrimsel Termal",
        "2D transient FVM; cyclic ve emergency rating", "transient", "transient",
        "IEC 60853-3 kısmi toprak kuruması/yeniden nemlenme henüz uygulanmamıştır.",
    ),
    "iteration": EngineMethodProfile(
        "iteration", "DiTuS Birleşik Tasarım İterasyonu",
        "Kablo → bonding → IEC 60287/2D → arıza/EPR → SVL → IEC 60853", "iteration", "first_design",
    ),
    "report": EngineMethodProfile(
        "report", "DiTuS Hesap ve Proje Raporlama Motoru",
        "Seçilebilir modüller, izlenebilir girdi/sonuç ve proje imzası", "deliverables", "deliverables",
    ),
    "procurement": EngineMethodProfile(
        "procurement", "DiTuS BOQ/BOM/RFQ Motoru",
        "Proje nesnelerinden izlenebilir metraj ve tedarik çıktısı", "deliverables", "deliverables",
    ),
}


def engine_method_profile(project: ProjectData, engine_id: str) -> EngineMethodProfile:
    if engine_id != "bonding":
        return _BASE_METHODS.get(
            engine_id,
            EngineMethodProfile(engine_id, engine_id, "DiTuS hesap motoru", "system_load", "first_design"),
        )
    mode = (project.bonding.solver_mode or "PRIMITIVE_CIM").upper()
    names = {
        "PRIMITIVE_CIM": (
            "CIGRE TB 797 Yönelimli Primitive CIM",
            "Primitive core–metalik kılıf–GCC ağı; CIM/MNA ana çözüm, Node-Voltage bağımsız kontrol",
        ),
        "NODE_VOLTAGE": (
            "Node-Voltage Bağımsız Doğrulama",
            "CIGRE TB 797 yönelimli primitive ağın düğüm-gerilimi çözümü",
        ),
        "COUPLED_LOOP_MATRIX": (
            "Bağlı Loop Matrix Karşılaştırması",
            "IEEE 575 cross-bonding loop yaklaşımı; regresyon/karşılaştırma katmanı",
        ),
        "INDEPENDENT_LOOP_PREVIEW": (
            "Basit Loop Ön İncelemesi",
            "Ön mühendislik/legacy karşılaştırma; nihai ağ çözümü değildir",
        ),
    }
    display, basis = names.get(mode, names["PRIMITIVE_CIM"])
    return EngineMethodProfile(
        "bonding", display, basis, "bonding", "bonding",
        f"Toprak dönüş modeli: {project.bonding.earth_return_model or 'SIMPLIFIED_CARSON'}. "
        "Tam Pollaczek/Wedepohl–Wilcox/Ametani henüz uygulanmamıştır.",
    )


def _item(
    items: list[EnginePrecheckItem],
    item_id: str,
    label: str,
    gate: str,
    ok: bool,
    *,
    detail: str = "",
    owner: str = "",
    owner_label: str = "",
    assumption: bool = False,
) -> None:
    status = CHECK_ASSUMPTION if ok and assumption else (CHECK_OK if ok else CHECK_MISSING)
    items.append(EnginePrecheckItem(item_id, label, gate, status, detail, owner, owner_label))


def _has_verified_cable_source(project: ProjectData) -> bool:
    return any(source.verified for source in project.cable.parameter_sources)


def _has_traceable_grounding_source(project: ProjectData) -> bool:
    keywords = ("ground", "earth", "toprak", "earthing")
    for record in project.source_audit.records:
        key = f"{record.parameter_key} {record.context} {record.notes}".lower()
        if any(word in key for word in keywords) and (record.status or "").upper() not in {"", "ASSUMPTION", "PRELIMINARY"}:
            return True
    return False


def _metallic_screen_layer(project: ProjectData):
    return next(
        (
            layer for layer in project.cable.layers
            if (layer.layer_type or "").upper() in {"METALLIC_SCREEN", "METALLIC_SHEATH", "WIRE_SCREEN"}
        ),
        None,
    )


def _has_current_run(project: ProjectData, engine_ids: Iterable[str]) -> bool:
    # Local import prevents a module-level dependency cycle while ensuring that
    # a completed run is accepted only when its exact input signature is still current.
    from ucd.calculations.project_workflow import engine_input_signature

    for engine_id in engine_ids:
        raw = project.workflow.engine_runs.get(engine_id, {})
        if not isinstance(raw, dict):
            continue
        if str(raw.get("status", "")).upper() not in {"COMPLETE", "CONDITIONAL"}:
            continue
        stored = str(raw.get("input_signature", "") or "")
        if stored and stored == engine_input_signature(project, engine_id):
            return True
    return False


def evaluate_engine_precheck(project: ProjectData, engine_id: str) -> EnginePrecheckResult:
    method = engine_method_profile(project, engine_id)
    result = EnginePrecheckResult(engine_id, method)
    items = result.items
    cable = project.cable
    applicability = evaluate_cable_model_applicability(cable)
    basis = project.design_basis
    thermal = project.thermal_design
    bonding = project.bonding

    def system_common() -> None:
        _item(items, "system_voltage", "Sistem gerilimi", GATE_HARD, cable.voltage_kv > 0 or basis.system_voltage_kv > 0,
              owner="system_load", owner_label="Sistem/Yük")
        _item(items, "frequency", "Frekans", GATE_HARD, cable.frequency_hz > 0 or basis.frequency_hz > 0,
              owner="system_load", owner_label="Sistem/Yük")
        _item(items, "design_current", "Tasarım akımı", GATE_HARD, cable.design_current_a > 0 or basis.design_current_per_circuit_a > 0,
              owner="system_load", owner_label="Sistem/Yük")

    def production_model_scope() -> None:
        _item(
            items, "production_model_scope", "Üretim fizik motoru kablo kapsamı", GATE_HARD,
            applicability.production_physics_allowed,
            detail=(applicability.summary + (" " + " ".join(applicability.reasons) if applicability.reasons else "")),
            owner="cable", owner_label="Kablo Model Kapsamı",
        )

    def cable_common() -> None:
        _item(items, "conductor_area", "İletken kesiti", GATE_HARD, cable.conductor_area_mm2 > 0,
              owner="cable", owner_label="Kablo Editörü")
        _item(items, "overall_diameter", "Kablo dış çapı", GATE_HARD, cable.overall_diameter_mm > 0,
              owner="cable", owner_label="Kablo Editörü")
        _item(items, "cable_snapshot", "Projeye atanmış kablo", GATE_SOFT, bool(cable.snapshot_hash),
              detail="Proje kablo kaydı yoksa katalog/manuel kablo değişiklikleri geçmiş hesabı etkileyebilir.",
              owner="cable", owner_label="Kablo Editörü")
        _item(items, "verified_cable_source", "Üretici doğrulanmış kablo kaynağı", GATE_SOFT,
              _has_verified_cable_source(project),
              detail="Katalog veya kullanıcı varsayımıyla hesap yapılabilir; nihai tasarım için üretici verisi gerekir.",
              owner="cable", owner_label="Kablo Kaynakları")

    if engine_id == "precheck":
        system_common()
        _item(items, "route", "Pozitif uzunluklu güzergâh", GATE_HARD,
              bool(project.route_sections) and all(section.length_m > 0 for section in project.route_sections),
              owner="route", owner_label="Güzergâh")
        has_candidate = cable.conductor_area_mm2 > 0 or bool(basis.candidates)
        _item(items, "candidate", "Kablo adayı veya kesit tercihi", GATE_SOFT, has_candidate,
              detail="Aday yoksa ilk iterasyon jenerik adayları üretir.",
              owner="cable", owner_label="Kablo Adayları")
        _item(items, "cable_snapshot", "Projeye atanmış kablo", GATE_SOFT, bool(cable.snapshot_hash),
              owner="cable", owner_label="Kablo Editörü")
        has_catalog_impedance = cable.dc_resistance_20_ohm_km > 0
        _item(items, "catalog_rl", "Katalog/hesap R-L ön eleme verisi", GATE_SOFT, has_catalog_impedance,
              owner="cable", owner_label="Kablo Kaynakları")

    elif engine_id in {"iec60287", "thermal_route"}:
        system_common()
        production_model_scope()
        cable_common()
        _item(items, "thermal_regions", "Chainage bazlı termal bölge", GATE_HARD, bool(thermal.regions),
              owner="installation", owner_label="Termal Güzergâh")
        _item(items, "thermal_templates", "Termal kesit şablonu", GATE_HARD, bool(thermal.templates),
              owner="installation", owner_label="Termal Kesit")
        has_internal = bool(cable.layers) or all(
            value > 0 for value in (
                cable.thermal_resistance_t1_km_w,
                cable.thermal_resistance_t2_km_w,
                cable.thermal_resistance_t3_km_w,
            )
        )
        _item(items, "internal_thermal", "Kablo iç termal modeli (katman veya T1–T3)", GATE_HARD, has_internal,
              owner="cable", owner_label="Kablo Parametrik Kesiti")
        reliable_materials = bool(thermal.materials) and all(
            (material.reliability or "").upper() not in {"", "LOW"} for material in thermal.materials
        )
        _item(items, "thermal_material_quality", "Doğrulanmış termal malzeme özellikleri", GATE_SOFT,
              reliable_materials,
              detail="Düşük güvenli/ön kabul malzemelerle sonuç koşullu kalır.",
              owner="installation", owner_label="Termal Malzeme Kütüphanesi")
        _item(items, "bonding_losses", "Güncel metalik kılıf/bonding kayıpları", GATE_SOFT,
              _has_current_run(project, ("bonding",)),
              detail="Bonding sonucu yoksa proje λ1/ön kabulü kullanılır ve termal sonuç koşullu olur.",
              owner="bonding", owner_label="Bonding")

    elif engine_id == "nodal":
        system_common()
        production_model_scope()
        cable_common()
        _item(items, "thermal_regions", "Chainage bazlı termal bölge", GATE_HARD, bool(thermal.regions),
              owner="installation", owner_label="Termal Güzergâh")
        _item(items, "thermal_templates", "2D çözüm etkin kesit şablonu", GATE_HARD,
              bool(thermal.templates) and any(template.nodal_enabled for template in thermal.templates),
              owner="installation", owner_label="Termal Kesit")
        _item(items, "thermal_materials", "2D malzeme kütüphanesi", GATE_HARD, bool(thermal.materials),
              owner="installation", owner_label="Termal Malzeme Kütüphanesi")
        full_layers = bool(cable.layers) and any(
            (layer.layer_type or "").upper() == "INSULATION" and layer.outer_diameter_mm > layer.inner_diameter_mm
            for layer in cable.layers
        )
        _item(items, "full_layers", "Gerçek/izlenebilir kablo katman geometrisi", GATE_SOFT, full_layers,
              detail="Eksikse eşdeğer kablo iç modeliyle ön 2D çözüm yapılır.",
              owner="cable", owner_label="Kablo Parametrik Kesiti")
        low_quality = any((m.reliability or "").upper() == "LOW" for m in thermal.materials)
        _item(items, "material_reliability", "Termal malzeme güven seviyesi", GATE_SOFT, not low_quality,
              detail="LOW güvenli malzemeler koşullu ön modeldir.",
              owner="installation", owner_label="Termal Malzeme Kütüphanesi")
        _item(items, "bonding_losses", "Güncel bonding/λ1 kaybı", GATE_SOFT,
              _has_current_run(project, ("bonding",)),
              owner="bonding", owner_label="Bonding")

    elif engine_id == "bonding":
        system_common()
        production_model_scope()
        _item(items, "minor_sections", "Minor/major section sınırları", GATE_HARD,
              bool(bonding.minor_sections) and all(section.length_m > 0 for section in bonding.minor_sections),
              owner="bonding", owner_label="Bonding Ağı")
        _item(items, "nodes", "Joint/terminasyon düğümleri", GATE_HARD, bool(bonding.nodes),
              owner="bonding", owner_label="Joint/Termination")
        connection_ok = bonding.scheme != BONDING_CROSS or bool(bonding.connections)
        _item(items, "connections", "Cross-bonding bağlantı grafiği", GATE_HARD, connection_ok,
              owner="bonding", owner_label="Bonding Ağı")
        screen_path = (
            cable.sheath_mean_diameter_mm > 0
            and (cable.sheath_dc_resistance_20_ohm_km > 0 or cable.sheath_cross_section_mm2 > 0)
        )
        _item(items, "screen_electrical", "Metalik ekran direnci/kesiti ve etkin çapı", GATE_HARD, screen_path,
              detail="Üretici Rdc + etkin çap veya toplam kesit + etkin çap gerekir.",
              owner="cable", owner_label="Kablo Metalik Ekran")
        screen_layer = _metallic_screen_layer(project)
        wire_geometry = bool(
            screen_layer and screen_layer.wire_count > 0 and screen_layer.wire_diameter_mm > 0
        )
        _item(items, "screen_wire_geometry", "Ekran tel adedi ve tel çapı", GATE_SOFT, wire_geometry,
              detail="Toplam ekran kesitiyle ön hesap mümkündür; tel geometrisi uydurulmaz.",
              owner="cable", owner_label="Kablo Metalik Ekran")
        _item(items, "screen_source", "Üretici doğrulanmış ekran/kılıf verisi", GATE_SOFT,
              _has_verified_cable_source(project), owner="cable", owner_label="Kablo Kaynakları")
        grounded = any(node.grounded and node.earth_resistance_ohm > 0 for node in bonding.nodes)
        _item(items, "grounding", "Terminasyon/link box topraklama değerleri", GATE_SOFT, grounded,
              detail="Varsayımsal topraklama ile sonuç koşullu kalır.",
              owner="bonding", owner_label="Bonding/Topraklama")
        if (bonding.earth_return_model or "").upper() == "SIMPLIFIED_CARSON":
            result.assumptions.append("Toprak dönüşü SIMPLIFIED_CARSON ile modellenir.")
        if cable.sheath_dc_resistance_20_ohm_km <= 0 and cable.sheath_cross_section_mm2 > 0:
            result.assumptions.append("Metalik ekran direnci toplam kesit ve malzemeden türetilir.")

    elif engine_id == "fault_epr":
        system_common()
        production_model_scope()
        enabled = [scenario for scenario in project.fault_study.scenarios if scenario.enabled]
        _item(items, "fault_scenarios", "Etkin arıza senaryosu", GATE_HARD, bool(enabled),
              owner="fault_epr", owner_label="Arıza Senaryoları")
        _item(items, "fault_current", "Pozitif arıza akımı", GATE_HARD,
              bool(enabled) and all(scenario.fault_current_a > 0 for scenario in enabled),
              owner="fault_epr", owner_label="Arıza Senaryoları")
        _item(items, "clearing_time", "Koruma temizleme süresi", GATE_HARD,
              bool(enabled) and all(scenario.duration_s > 0 for scenario in enabled),
              owner="fault_epr", owner_label="Arıza Senaryoları")
        _item(items, "bonding_network", "Bonding/joint/toprak ağı", GATE_HARD,
              bool(bonding.nodes) and bool(bonding.minor_sections),
              owner="bonding", owner_label="Bonding Ağı")
        _item(items, "screen_thermal", "Metalik ekran kesiti veya doğrulanmış direnci", GATE_HARD,
              cable.sheath_cross_section_mm2 > 0 or cable.sheath_dc_resistance_20_ohm_km > 0,
              owner="cable", owner_label="Kablo Metalik Ekran")
        grounded = any(node.grounded and node.earth_resistance_ohm > 0 for node in bonding.nodes)
        _item(items, "grounding", "Topraklama direnci/EPR dönüş yolu", GATE_HARD, grounded,
              owner="bonding", owner_label="Bonding/Topraklama")
        _item(items, "measured_grounding", "Ölçülmüş veya tasarımca doğrulanmış topraklama", GATE_SOFT,
              grounded and _has_traceable_grounding_source(project),
              detail="Kaynak doğrulaması olmayan topraklama verisiyle EPR sonucu koşulludur.",
              owner="bonding", owner_label="Bonding/Topraklama")

    elif engine_id == "svl":
        production_model_scope()
        _item(items, "svl_candidates", "SVL adayları", GATE_HARD, bool(project.svl.candidates),
              owner="svl", owner_label="SVL Editörü")
        _item(items, "fault_tov", "Arıza TOV görevi", GATE_HARD, project.svl.fault_tov_rms_v > 0,
              owner="fault_epr", owner_label="Arıza/EPR")
        _item(items, "fault_duration", "TOV süresi", GATE_HARD, project.svl.fault_tov_duration_s > 0,
              owner="fault_epr", owner_label="Arıza/EPR")
        _item(items, "insulation_levels", "Joint/dış kılıf yalıtım seviyeleri", GATE_HARD,
              project.svl.joint_interrupt_impulse_withstand_peak_v > 0
              and project.svl.jacket_impulse_withstand_peak_v > 0,
              owner="svl", owner_label="SVL/Yalıtım Koordinasyonu")
        _item(items, "current_bonding", "Güncel bonding gerilimleri", GATE_SOFT,
              _has_current_run(project, ("bonding",)), owner="bonding", owner_label="Bonding")
        _item(items, "current_fault", "Güncel arıza/EPR sonucu", GATE_SOFT,
              _has_current_run(project, ("fault_epr",)), owner="fault_epr", owner_label="Arıza/EPR")
        real_candidates = all(
            (candidate.source or "").upper() not in {"", "ILLUSTRATIVE_TEST_DATA"}
            for candidate in project.svl.candidates
        )
        _item(items, "manufacturer_svl", "Üretici doğrulanmış SVL V-I/TOV/enerji verisi", GATE_SOFT,
              real_candidates, owner="svl", owner_label="SVL Adayları")

    elif engine_id == "transient":
        system_common()
        production_model_scope()
        _item(items, "load_profiles", "Yük-zaman profili", GATE_HARD,
              bool(project.transient_study.profiles)
              and any(len(profile.points) >= 2 for profile in project.transient_study.profiles),
              owner="transient", owner_label="IEC 60853 Yük Profili")
        _item(items, "thermal_base", "Kararlı durum termal taban", GATE_HARD,
              bool(thermal.regions) and bool(thermal.templates),
              owner="installation", owner_label="Termal Güzergâh")
        capacities = [
            project.transient_study.cable_outer_heat_capacity_mj_m3k,
            project.transient_study.default_soil_heat_capacity_mj_m3k,
            project.transient_study.default_backfill_heat_capacity_mj_m3k,
        ]
        _item(items, "heat_capacity", "Pozitif hacimsel ısı kapasiteleri", GATE_HARD,
              all(value > 0 for value in capacities),
              owner="transient", owner_label="IEC 60853 Ayarları")
        _item(items, "steady_result", "Güncel IEC 60287/2D kararlı durum sonucu", GATE_SOFT,
              _has_current_run(project, ("nodal", "thermal_route", "iec60287")),
              owner="steady_thermal", owner_label="IEC 60287 ve 2D Termal")
        reliable_capacity = all(
            material.volumetric_heat_capacity_mj_m3k > 0
            and (material.reliability or "").upper() not in {"", "LOW"}
            for material in thermal.materials
        ) if thermal.materials else False
        _item(items, "verified_capacity", "Doğrulanmış malzeme ısı kapasiteleri", GATE_SOFT,
              reliable_capacity, owner="installation", owner_label="Termal Malzeme Kütüphanesi")
        result.assumptions.append("IEC 60853-3 toprak kuruması/yeniden nemlenme modeli henüz etkin değildir.")

    elif engine_id == "iteration":
        system_common()
        production_model_scope()
        cable_common()
        _item(items, "route", "Güzergâh ve termal bölgeler", GATE_HARD,
              bool(project.route_sections) and bool(thermal.regions),
              owner="route", owner_label="Güzergâh")
        for child, label, owner in (
            ("bonding", "Bonding çözümü", "bonding"),
            ("thermal_route", "IEC 60287/termal çözümü", "steady_thermal"),
            ("fault_epr", "Arıza/EPR çözümü", "fault_epr"),
            ("svl", "SVL koordinasyonu", "svl"),
            ("transient", "IEC 60853 çözümü", "transient"),
        ):
            _item(items, f"child_{child}", label, GATE_SOFT, _has_current_run(project, (child,)),
                  owner=owner, owner_label=label)

    elif engine_id in {"report", "procurement"}:
        _item(items, "project_identity", "Proje kimliği ve revizyon", GATE_HARD,
              bool(project.project_name and project.project_code),
              owner="system_load", owner_label="Proje Bilgileri")
        _item(items, "route", "Güzergâh/metraj kaynağı", GATE_HARD, bool(project.route_sections),
              owner="route", owner_label="Güzergâh")
        cable_common()
        if engine_id == "report":
            _item(items, "calculation_results", "En az bir güncel hesap sonucu", GATE_SOFT,
                  any(_has_current_run(project, (key,)) for key in (
                      "precheck", "iec60287", "nodal", "bonding", "fault_epr", "svl", "transient"
                  )), owner="precheck", owner_label="Hesap Modülleri")
        else:
            _item(items, "cable_assignment", "Aktif güzergâh-kablo ataması", GATE_SOFT,
                  any(assignment.active for assignment in project.cable_application.assignments),
                  owner="cable", owner_label="Kablo Uygulama")

    else:
        result.notes.append("Bu motor için ayrıntılı veri kapısı henüz tanımlı değildir.")

    if method.model_limit:
        result.notes.append(method.model_limit)
    return result
