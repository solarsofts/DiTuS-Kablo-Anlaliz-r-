from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import hashlib
import json
from typing import Any, Mapping

from ucd.models.project import ProjectData

STATUS_NOT_STARTED = "NOT_STARTED"
STATUS_MISSING_DATA = "MISSING_DATA"
STATUS_PRELIMINARY = "PRELIMINARY"
STATUS_READY = "READY"
STATUS_RUNNING = "RUNNING"
STATUS_CONDITIONAL = "CONDITIONAL"
STATUS_COMPLETE = "COMPLETE"
STATUS_STALE = "STALE"
STATUS_BLOCKED = "BLOCKED"

WORKFLOW_STATUSES = {
    STATUS_NOT_STARTED,
    STATUS_MISSING_DATA,
    STATUS_PRELIMINARY,
    STATUS_READY,
    STATUS_RUNNING,
    STATUS_CONDITIONAL,
    STATUS_COMPLETE,
    STATUS_STALE,
    STATUS_BLOCKED,
}


@dataclass(frozen=True)
class WorkflowStageSpec:
    stage_id: str
    number: int
    title: str
    short_title: str
    user_inputs: tuple[str, ...]
    engines: tuple[str, ...]
    outputs: tuple[str, ...]
    workspace_key: str
    result_group: str


@dataclass
class WorkflowStageEvaluation:
    stage_id: str
    number: int
    title: str
    short_title: str
    status: str
    user_inputs: list[str] = field(default_factory=list)
    engines: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    next_action: str = ""
    workspace_key: str = ""
    result_group: str = "summary"
    input_readiness: str = "UNKNOWN"
    run_status: str = "NOT_RUN"
    freshness: str = "NOT_APPLICABLE"
    maturity: str = "SCREENING"

    @property
    def is_blocking(self) -> bool:
        return self.status in {STATUS_MISSING_DATA, STATUS_BLOCKED}


@dataclass
class ProjectWorkflowEvaluation:
    stages: list[WorkflowStageEvaluation]
    current_stage_id: str
    recommended_stage_id: str
    recommended_action: str
    overall_status: str
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def stage(self, stage_id: str) -> WorkflowStageEvaluation:
        for item in self.stages:
            if item.stage_id == stage_id:
                return item
        raise KeyError(stage_id)


STAGE_SPECS: tuple[WorkflowStageSpec, ...] = (
    WorkflowStageSpec(
        "system_load", 1, "Proje ve Sistem / Yük", "Sistem",
        (
            "Proje adı, kodu ve revizyonu",
            "Sistem gerilimi ve frekansı",
            "MW, MVA veya A ile yük",
            "Güç faktörü, devre sayısı ve N-1",
            "Topraklama yaklaşımı ve tasarım marjı",
        ),
        ("Yük ve tasarım akımı motoru",),
        ("Normal akım", "N-1 akımı", "Tasarım akımı", "Kablo başına akım"),
        "first_design", "summary",
    ),
    WorkflowStageSpec(
        "route", 2, "Güzergâh ve Bölgelendirme", "Güzergâh",
        (
            "DXF/CAD veya toplam güzergâh uzunluğu",
            "Başlangıç-bitiş ve chainage",
            "Yol, HDD, menhol ve ek odası geçişleri",
            "Bölge sınırları ve veri kaynağı",
        ),
        ("Güzergâh doğrulama", "Chainage ve kapsam denetimi"),
        ("Güzergâh bölümleri", "Geçiş adayları", "Eksik/çakışan bölgeler"),
        "route", "summary",
    ),
    WorkflowStageSpec(
        "installation", 3, "Kurulum ve Termal Kesit", "Kurulum",
        (
            "Kurulum tipi ve kablo dizilimi",
            "Gömme derinliği, faz ve devre aralıkları",
            "Toprak, termal dolgu ve yüzey koşulları",
            "Ölçülmüş / şartname / ön kabul veri durumu",
        ),
        ("Termal kesit doğrulama", "Termal direnç ön işlemi"),
        ("Bölgesel termal kesitler", "T1-T4 girdileri", "Veri güven düzeyi"),
        "thermal_route", "thermal_resistance",
    ),
    WorkflowStageSpec(
        "cable", 4, "Kablo Adayları ve Kablo Tanımı", "Kablo",
        (
            "Gerilim sınıfı, Cu/Al ve kesit",
            "Katalog / manuel / jenerik başlangıç",
            "Kablo/faz sayısı ve metalik ekran kesiti",
            "Katalog kaynağı ve projeye atama",
        ),
        ("Katalog ön eleme", "Parametrik kablo doğrulama"),
        ("Aday listesi", "Projeye atanmış kablo", "Hesap hazırlık matrisi"),
        "cable", "summary",
    ),
    WorkflowStageSpec(
        "precheck", 5, "İlk Elektriksel Ön Eleme", "Ön Eleme",
        (
            "Seçilen yük senaryosu",
            "Aday kablo ve aktif devre sayısı",
            "Ön gerilim düşümü için katalog R/L",
        ),
        ("Yük akımı", "Gerilim düşümü", "Katalog ampacity ön kontrolü", "Faz iletkeni kısa devre ön kontrolü"),
        ("Ön eleme hükmü", "Gerilim düşümü", "Aday karşılaştırması"),
        "first_design", "summary",
    ),
    WorkflowStageSpec(
        "steady_thermal", 6, "IEC 60287 ve 2D Termal", "Termal",
        (
            "Kablo katman geometrisi",
            "Bölgesel kurulum ve ortam koşulları",
            "Toprak/backfill ısıl özdirenci",
            "İzin verilen sıcaklık ve bonding ön kabulü",
        ),
        ("IEC 60287", "2D nodal kararlı durum", "Bölgesel termal optimizasyon"),
        ("Ampacity", "İletken sıcaklığı", "Kritik bölge", "Kayıp bileşenleri"),
        "thermal_review", "steady_thermal",
    ),
    WorkflowStageSpec(
        "bonding", 7, "Joint, Link Box ve Bonding", "Bonding",
        (
            "Joint ve major/minor section sınırları",
            "Bonding tipi ve cross bağlantıları",
            "Link box ve topraklama noktaları",
            "ECC/GCC ve bonding lead bilgileri",
        ),
        ("Bonding loop", "Primitive CIM / Node Voltage"),
        ("Metalik kılıf gerilimi", "Dolaşım akımı", "λ1", "Kritik link box"),
        "bonding", "bonding",
    ),
    WorkflowStageSpec(
        "fault_epr", 8, "Arıza, EPR ve Ekran Dayanımı", "Arıza/EPR",
        (
            "Kaynak Z1/Z0 veya kısa devre seviyesi",
            "Arıza tipleri ve koruma temizleme süreleri",
            "Topraklama dirençleri ve ECC/GCC",
            "Metalik ekran/kılıf termik sınırları",
        ),
        ("3PH / PP / SLG arıza", "EPR ve akım paylaşımı", "Ekran termik kontrolü"),
        ("Arıza akımları", "EPR", "Ekran akımı ve dayanımı", "Interrupt gerilimi"),
        "fault", "fault_epr",
    ),
    WorkflowStageSpec(
        "svl", 9, "SVL ve Yalıtım Koordinasyonu", "SVL",
        (
            "Dış kılıf ve aksesuar yalıtım seviyeleri",
            "TOV süresi ve bonding lead uzunluğu",
            "SVL bağlantı düzeni ve adayları",
        ),
        ("SVL MCOV/TOV/residual", "Enerji ve deşarj ön kontrolü"),
        ("SVL ihtiyacı", "Aday sınıf", "Koruma seviyesi", "Bekleyen kontroller"),
        "svl", "svl",
    ),
    WorkflowStageSpec(
        "transient", 10, "IEC 60853 Geçici / Çevrimsel", "IEC 60853",
        (
            "Yük-zaman profili",
            "Başlangıç koşulu ve ön çevrim",
            "Acil yük süresi",
            "Malzeme hacimsel ısı kapasiteleri",
        ),
        ("IEC 60853 iş akışlı transient", "Cyclic ve emergency rating"),
        ("Sıcaklık-zaman eğrisi", "Cyclic rating", "Emergency rating"),
        "transient", "transient",
    ),
    WorkflowStageSpec(
        "iteration", 11, "Birleşik İterasyon ve Tasarım Kararı", "İterasyon",
        (
            "Optimizasyon değişkenleri ve sınırlar",
            "Normal, N-1 ve acil kabul kriterleri",
            "Koşullu sonuçlar için mühendislik kararları",
        ),
        ("Birleşik tasarım iterasyonu", "Bölgesel alternatif değerlendirmesi"),
        ("İterasyon izi", "Kritik sebep", "Seçilen tasarım", "Nihai kapı durumu"),
        "first_design", "summary",
    ),
    WorkflowStageSpec(
        "deliverables", 12, "Rapor, BOQ/BOM ve RFQ", "Çıktılar",
        (
            "Doküman ve revizyon bilgileri",
            "Rapor modülleri ve çıktı biçimleri",
            "Metraj payları, makara ve yedek varsayımları",
        ),
        ("Raporlama", "BOQ/BOM", "Makara planı", "RFQ"),
        ("Hesap raporu", "Proje raporu", "BOQ/BOM", "Teklif isteme paketi"),
        "deliverables", "summary",
    ),
)


ENGINE_INPUT_COMPONENTS: dict[str, tuple[str, ...]] = {
    "precheck": ("system_load", "route", "cable", "cable_application"),
    "iec60287": ("system_load", "route", "cable", "thermal_design", "installation_design", "bonding"),
    "thermal_route": ("system_load", "route", "cable", "thermal_design", "installation_design", "bonding"),
    "nodal": ("system_load", "route", "cable", "thermal_design", "installation_design", "bonding"),
    "thermal_method_validation": ("system_load", "route", "cable", "thermal_design", "installation_design", "bonding"),
    "bonding": ("route", "cable", "installation_design", "bonding"),
    "fault_epr": ("route", "cable", "installation_design", "bonding", "fault_study"),
    "svl": ("installation_design", "bonding", "fault_study", "svl"),
    "transient": ("system_load", "cable", "thermal_design", "installation_design", "bonding", "transient_study"),
    "iteration": (
        "system_load", "route", "cable", "cable_application", "thermal_design", "installation_design",
        "bonding", "fault_study", "svl", "transient_study",
    ),
    "report": (
        "project_identity", "system_load", "route", "cable", "cable_application",
        "thermal_design", "installation_design", "bonding", "fault_study", "svl", "transient_study",
    ),
    "procurement": (
        "project_identity", "route", "cable", "cable_application", "installation_design", "bonding",
        "svl", "procurement",
    ),
}

_COMPONENT_LABELS = {
    "project_identity": "proje kimliği/revizyonu",
    "system_load": "sistem ve yük girdileri",
    "route": "güzergâh ve bölüm verileri",
    "cable": "projeye atanmış kablo tanımı",
    "cable_application": "kablo atamaları ve kaynak kararları",
    "thermal_design": "termal bölge, kesit veya malzeme verileri",
    "installation_design": "Kablo-Kanal fiziksel x-y ve kanal geometrisi",
    "bonding": "joint/link box/bonding ağı",
    "fault_study": "arıza senaryosu veya topraklama girdileri",
    "svl": "SVL kriterleri veya adayları",
    "transient_study": "yük-zaman profili veya transient ayarları",
    "procurement": "metraj ve tedarik varsayımları",
}

_SUCCESS_RUN_STATUSES = {STATUS_COMPLETE, STATUS_CONDITIONAL}


def _stable_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _input_component_value(project: ProjectData, component: str) -> object:
    if component == "project_identity":
        return {
            "project_name": project.project_name,
            "project_code": project.project_code,
            "description": project.description,
            "standards_profile": project.standards_profile,
        }
    if component == "system_load":
        return {"design_basis": asdict(project.design_basis), "design_current_a": project.cable.design_current_a}
    if component == "route":
        return [asdict(item) for item in project.route_sections]
    if component == "cable":
        return asdict(project.cable)
    if component == "cable_application":
        return asdict(project.cable_application)
    if component == "thermal_design":
        return asdict(project.thermal_design)
    if component == "installation_design":
        return asdict(project.installation_design)
    if component == "bonding":
        return asdict(project.bonding)
    if component == "fault_study":
        return asdict(project.fault_study)
    if component == "svl":
        return asdict(project.svl)
    if component == "transient_study":
        return asdict(project.transient_study)
    if component == "procurement":
        return asdict(project.procurement)
    raise KeyError(component)


def engine_input_components(project: ProjectData, engine_id: str) -> dict[str, str]:
    components = ENGINE_INPUT_COMPONENTS.get(engine_id, ())
    return {name: _stable_hash(_input_component_value(project, name)) for name in components}


def engine_input_signature(project: ProjectData, engine_id: str) -> str:
    return _stable_hash(engine_input_components(project, engine_id))


def record_engine_run(
    project: ProjectData,
    engine_id: str,
    status: str,
    *,
    result_count: int = 0,
    warning_count: int = 0,
    message: str = "",
    conditional_reasons: list[str] | tuple[str, ...] = (),
    precheck: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist one traceable calculation execution without storing result payloads."""

    now = datetime.now().isoformat(timespec="seconds")
    normalized = _normalize_progress(status, default=STATUS_BLOCKED)
    previous = dict(project.workflow.engine_runs.get(engine_id, {}))
    started_at = previous.get("started_at", now) if normalized != STATUS_RUNNING else now
    record: dict[str, Any] = {
        "engine_id": engine_id,
        "status": normalized,
        "started_at": started_at,
        "finished_at": "" if normalized == STATUS_RUNNING else now,
        "input_signature": engine_input_signature(project, engine_id),
        "input_components": engine_input_components(project, engine_id),
        "result_count": int(result_count),
        "warning_count": int(warning_count),
        "message": str(message or ""),
        "conditional_reasons": [str(item) for item in conditional_reasons],
        "stale_reason": "",
        "precheck": dict(precheck) if precheck is not None else dict(previous.get("precheck", {}) or {}),
    }
    project.workflow.engine_runs[engine_id] = record
    return record


def mark_engine_runs_stale(
    project: ProjectData,
    engine_ids: tuple[str, ...] | list[str],
    reason: str,
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    for engine_id in engine_ids:
        previous = project.workflow.engine_runs.get(engine_id)
        if not isinstance(previous, dict):
            continue
        status = _normalize_progress(str(previous.get("status", "")), default=STATUS_NOT_STARTED)
        if status not in {STATUS_COMPLETE, STATUS_CONDITIONAL, STATUS_RUNNING, STATUS_STALE}:
            continue
        previous["status"] = STATUS_STALE
        previous["stale_reason"] = reason
        previous["finished_at"] = previous.get("finished_at") or now


def _run_record_status(project: ProjectData, engine_id: str) -> tuple[str | None, list[str]]:
    raw = project.workflow.engine_runs.get(engine_id)
    if not isinstance(raw, dict):
        return None, []
    status = _normalize_progress(str(raw.get("status", "")), default=STATUS_NOT_STARTED)
    notes: list[str] = []
    if raw.get("finished_at"):
        notes.append(f"Son çalıştırma: {raw['finished_at']}")
    message = str(raw.get("message", "") or "").strip()
    if message:
        notes.append(message)
    previous_components = raw.get("input_components")
    current_components = engine_input_components(project, engine_id)
    inputs_changed = isinstance(previous_components, dict) and previous_components != current_components
    if status in _SUCCESS_RUN_STATUSES and inputs_changed:
        changed = [
            _COMPONENT_LABELS.get(name, name)
            for name in current_components
            if previous_components.get(name) != current_components.get(name)
        ]
        status = STATUS_STALE
        notes.append("Sonuçtan sonra değişen girdiler: " + ", ".join(changed))
    elif status == STATUS_BLOCKED and inputs_changed:
        notes.append("Önceki başarısız çalışma farklı girdilere aitti; motor yeniden çalıştırılabilir.")
        return None, notes
    if status == STATUS_STALE:
        reason = str(raw.get("stale_reason", "") or "").strip()
        if reason:
            notes.append("Güncellik nedeni: " + reason)
    precheck = raw.get("precheck")
    if isinstance(precheck, dict):
        method = precheck.get("method", {})
        if isinstance(method, dict) and method.get("display_name"):
            notes.append("Yöntem: " + str(method.get("display_name")))
        if precheck.get("maturity"):
            notes.append("Sonuç olgunluğu: " + str(precheck.get("maturity")))
        hard_missing = [item for item in precheck.get("items", []) or [] if isinstance(item, dict) and item.get("gate") == "HARD" and item.get("status") == "MISSING"]
        soft_missing = [item for item in precheck.get("items", []) or [] if isinstance(item, dict) and item.get("gate") == "SOFT" and item.get("status") == "MISSING"]
        if hard_missing:
            notes.append("Zorunlu eksikler: " + ", ".join(str(item.get("label", "")) for item in hard_missing))
        if soft_missing:
            notes.append("Önerilen eksikler: " + ", ".join(str(item.get("label", "")) for item in soft_missing))
    for item in raw.get("conditional_reasons", []) or []:
        notes.append(str(item))
    result_count = int(raw.get("result_count", 0) or 0)
    warning_count = int(raw.get("warning_count", 0) or 0)
    if result_count or warning_count:
        notes.append(f"Sonuç: {result_count} kayıt · {warning_count} uyarı")
    return status, list(dict.fromkeys(notes))


def _engine_status(
    project: ProjectData, runtime: Mapping[str, object], engine_id: str
) -> tuple[str | None, list[str]]:
    runtime_status = _runtime_status(runtime, engine_id)
    if runtime_status == STATUS_RUNNING:
        return STATUS_RUNNING, ["Hesap motoru şu anda çalışıyor."]
    record_status, notes = _run_record_status(project, engine_id)
    if record_status is not None:
        return record_status, notes
    if runtime_status == STATUS_COMPLETE:
        return STATUS_COMPLETE, ["Oturumda hesap sonucu mevcut; eski proje formatında çalışma kaydı yok."]
    if runtime_status in {STATUS_CONDITIONAL, STATUS_BLOCKED, STATUS_STALE}:
        return runtime_status, notes
    return None, notes


def _normalize_progress(value: str, *, default: str = STATUS_NOT_STARTED) -> str:
    value = (value or "").strip().upper()
    mapping = {
        "MISSING": STATUS_MISSING_DATA,
        "NOT_RUN": STATUS_NOT_STARTED,
        "NOT_READY": STATUS_BLOCKED,
        "PRELIMINARY": STATUS_PRELIMINARY,
        "READY": STATUS_READY,
        "RUNNING": STATUS_RUNNING,
        "CONDITIONAL": STATUS_CONDITIONAL,
        "CONDITIONAL_READY": STATUS_CONDITIONAL,
        "COMPLETE": STATUS_COMPLETE,
        "TRANSIENT_COMPLETE": STATUS_COMPLETE,
        "PASS": STATUS_COMPLETE,
        "STALE": STATUS_STALE,
        "BLOCKED": STATUS_BLOCKED,
    }
    return mapping.get(value, default)


def _runtime_status(runtime: Mapping[str, object], key: str) -> str | None:
    raw = runtime.get(key)
    if isinstance(raw, str):
        normalized = _normalize_progress(raw, default="")
        return normalized or None
    if raw is True:
        return STATUS_COMPLETE
    if raw is False:
        return None
    return None


def _base_evaluation(spec: WorkflowStageSpec, status: str) -> WorkflowStageEvaluation:
    return WorkflowStageEvaluation(
        stage_id=spec.stage_id,
        number=spec.number,
        title=spec.title,
        short_title=spec.short_title,
        status=status,
        user_inputs=list(spec.user_inputs),
        engines=list(spec.engines),
        outputs=list(spec.outputs),
        workspace_key=spec.workspace_key,
        result_group=spec.result_group,
    )


_STAGE_ENGINE_IDS: dict[str, tuple[str, ...]] = {
    "precheck": ("precheck",),
    "steady_thermal": ("iec60287", "thermal_route", "nodal"),
    "bonding": ("bonding",),
    "fault_epr": ("fault_epr",),
    "svl": ("svl",),
    "transient": ("transient",),
    "iteration": ("iteration",),
    "deliverables": ("report", "procurement"),
}


def _stage_dimensions(project: ProjectData, stage: WorkflowStageEvaluation) -> None:
    """Populate the four user-facing workflow dimensions without changing results."""
    if stage.missing_inputs or stage.blocking_reasons or stage.status in {STATUS_MISSING_DATA, STATUS_BLOCKED}:
        stage.input_readiness = "MISSING"
    elif stage.status in {STATUS_PRELIMINARY, STATUS_CONDITIONAL}:
        stage.input_readiness = "PRELIMINARY"
    else:
        stage.input_readiness = "COMPLETE"

    engine_ids = _STAGE_ENGINE_IDS.get(stage.stage_id, ())
    if not engine_ids:
        stage.run_status = "NOT_APPLICABLE"
        stage.freshness = "NOT_APPLICABLE"
        stage.maturity = "CONDITIONAL" if stage.input_readiness == "PRELIMINARY" else (
            "VERIFIED" if stage.input_readiness == "COMPLETE" else "SCREENING"
        )
        return

    statuses: list[str] = []
    maturities: list[str] = []
    has_stale = False
    for engine_id in engine_ids:
        raw = project.workflow.engine_runs.get(engine_id, {})
        if not isinstance(raw, dict) or not raw:
            continue
        stored_status = _normalize_progress(str(raw.get("status", "")), default=STATUS_NOT_STARTED)
        previous_components = raw.get("input_components")
        current_components = engine_input_components(project, engine_id)
        changed = isinstance(previous_components, dict) and previous_components != current_components
        if stored_status in _SUCCESS_RUN_STATUSES and changed:
            stored_status = STATUS_STALE
        statuses.append(stored_status)
        has_stale |= stored_status == STATUS_STALE
        precheck = raw.get("precheck", {})
        if isinstance(precheck, dict) and precheck.get("maturity"):
            maturities.append(str(precheck.get("maturity")))

    if any(value == STATUS_RUNNING for value in statuses):
        stage.run_status = "RUNNING"
    elif any(value in _SUCCESS_RUN_STATUSES for value in statuses):
        stage.run_status = "SUCCESS"
    elif any(value == STATUS_BLOCKED for value in statuses):
        stage.run_status = "FAILED"
    elif has_stale:
        stage.run_status = "SUCCESS"
    else:
        stage.run_status = "NOT_RUN"

    stage.freshness = "STALE" if has_stale else (
        "CURRENT" if stage.run_status == "SUCCESS" else "NOT_APPLICABLE"
    )
    if "SCREENING" in maturities:
        stage.maturity = "SCREENING"
    elif "CONDITIONAL" in maturities:
        stage.maturity = "CONDITIONAL"
    elif maturities and all(value == "VERIFIED" for value in maturities):
        stage.maturity = "VERIFIED"
    else:
        stage.maturity = "CONDITIONAL" if stage.input_readiness == "PRELIMINARY" else (
            "VERIFIED" if stage.input_readiness == "COMPLETE" and stage.run_status == "SUCCESS" else "SCREENING"
        )


def evaluate_project_workflow(
    project: ProjectData,
    runtime: Mapping[str, object] | None = None,
) -> ProjectWorkflowEvaluation:
    """Evaluate the guided design workflow without mutating the project.

    ``runtime`` may carry UI-session calculation flags such as ``iec60287``,
    ``nodal``, ``bonding``, ``fault_epr``, ``svl`` and ``transient``. Persisted
    project progress remains the fallback so the evaluator is also usable in
    reports, tests and headless project checks.
    """

    runtime = runtime or {}
    progress = project.design_progress
    stages: list[WorkflowStageEvaluation] = []

    # 1 — System/load
    system_status = _runtime_status(runtime, "system_load") or _normalize_progress(progress.system_load)
    s = _base_evaluation(STAGE_SPECS[0], system_status)
    if system_status == STATUS_MISSING_DATA:
        s.missing_inputs.append("Kullanıcı tarafından doğrulanmış sistem/yük girdisi")
    if project.cable.voltage_kv <= 0:
        s.missing_inputs.append("Sistem gerilimi")
    if project.cable.frequency_hz <= 0:
        s.missing_inputs.append("Frekans")
    basis = project.design_basis
    has_load = any(
        value > 0
        for value in (basis.active_power_mw, basis.apparent_power_mva, basis.direct_current_a, project.cable.design_current_a)
    )
    if not has_load:
        s.missing_inputs.append("MW, MVA veya A yük girdisi")
    if s.missing_inputs:
        s.status = STATUS_MISSING_DATA
        s.next_action = "Sistem ve yük girdilerini tamamlayın."
    else:
        if s.status == STATUS_MISSING_DATA:
            s.status = STATUS_READY
        s.next_action = "Güzergâhı ve bölge sınırlarını tanımlayın."
    stages.append(s)

    # 2 — Route
    route_status = _runtime_status(runtime, "route") or _normalize_progress(progress.route, default=STATUS_PRELIMINARY)
    s = _base_evaluation(STAGE_SPECS[1], route_status)
    valid_sections = [item for item in project.route_sections if item.length_m > 0]
    if not valid_sections:
        s.missing_inputs.append("Pozitif uzunluklu güzergâh bölümü")
        s.status = STATUS_MISSING_DATA
    elif any(item.length_m <= 0 for item in project.route_sections):
        s.blocking_reasons.append("Sıfır veya negatif uzunluklu güzergâh bölümü var.")
        s.status = STATUS_BLOCKED
    elif not project.cad_source and basis.route_input_mode != "TOTAL_LENGTH":
        s.notes.append("CAD kaynağı bağlı değil; güzergâh kullanıcı verisiyle çalışıyor.")
    route_approved = project.workflow.stage_notes.get("route_approval") == "APPROVED"
    if valid_sections and not route_approved and s.status not in {STATUS_BLOCKED, STATUS_MISSING_DATA}:
        s.status = STATUS_PRELIMINARY
        s.notes.append("Güzergâh kaynaktan veya ön tasarımdan alınmış; kullanıcı kabulü bekleniyor.")
        s.next_action = "Güzergâh ekranını açın, bölümleri kontrol edin ve Mevcut Güzergâhı Kabul Et komutunu kullanın."
    else:
        s.next_action = "Kurulum tiplerini ve bölgesel termal kesitleri tanımlayın."
    stages.append(s)

    # 3 — Installation / physical cross-sections / thermal sections
    s = _base_evaluation(STAGE_SPECS[2], STATUS_PRELIMINARY)
    thermal = project.thermal_design
    installation = project.installation_design
    if not installation.cross_sections:
        s.missing_inputs.append("En az bir fiziksel kurulum kesiti")
    if not thermal.templates:
        s.missing_inputs.append("En az bir termal kesit şablonu")
    if not thermal.regions:
        s.missing_inputs.append("Chainage bazlı termal bölge")
    if thermal.regions and any(region.end_m <= region.start_m for region in thermal.regions if region.enabled):
        s.blocking_reasons.append("Başlangıç/bitiş chainage değeri geçersiz termal bölge var.")
    from ucd.calculations.installation import validate_installation_design
    installation_issues = validate_installation_design(project)
    installation_errors = [item for item in installation_issues if item.severity == "ERROR"]
    installation_warnings = [item for item in installation_issues if item.severity == "WARNING"]
    if installation_errors:
        s.blocking_reasons.append(
            f"Fiziksel kurulum modelinde {len(installation_errors)} doğrulama hatası var."
        )
    if installation_warnings:
        s.notes.append(f"Fiziksel kurulum modelinde {len(installation_warnings)} uyarı var.")
    if installation.solver_coupling_mode == "PRODUCTION_LINKED":
        s.notes.append(
            "Kablo-Kanal fiziksel kesiti üretim hesaplarına bağlıdır: gerçek x-y destekleyen motorlar koordinatları doğrudan, analitik motorlar izlenebilir eşdeğer geometri girdilerini kullanır."
        )
    else:
        s.notes.append(
            "Fiziksel kesit üretim hesaplarına bağlı değil; geometri değişiklikleri hesap sonuçlarına aktarılmaz."
        )
    low_reliability = [item.name for item in thermal.materials if (item.reliability or "").upper() == "LOW"]
    if low_reliability:
        s.notes.append(f"{len(low_reliability)} termal malzeme düşük güvenli ön kabul durumunda.")
    if s.blocking_reasons:
        s.status = STATUS_BLOCKED
    elif s.missing_inputs:
        s.status = STATUS_MISSING_DATA
    elif thermal.regions:
        s.status = STATUS_CONDITIONAL if (low_reliability or installation_warnings or installation.solver_coupling_mode != "PRODUCTION_LINKED") else STATUS_READY
    s.next_action = "Fiziksel kesiti doğrulayın; ardından proje kablosunu seçip güzergâha atayın."
    stages.append(s)

    # 4 — Cable
    cable_status = _runtime_status(runtime, "cable") or _normalize_progress(progress.cable, default=STATUS_PRELIMINARY)
    s = _base_evaluation(STAGE_SPECS[3], cable_status)
    cable = project.cable
    if cable.conductor_area_mm2 <= 0:
        s.missing_inputs.append("İletken kesiti")
    if cable.voltage_kv <= 0:
        s.missing_inputs.append("Kablo sistem gerilimi")
    if not cable.layers:
        s.missing_inputs.append("Kablo konstrüksiyon katmanları")
    application = project.cable_application
    if not application.applied_snapshot_hash:
        if application.selected_candidate_id:
            s.notes.append(f"Seçili/önerilen aday {application.selected_candidate_id}; projeye henüz atanmadı.")
        else:
            s.notes.append("Projeye henüz kablo atanmadı.")
        if not s.missing_inputs:
            s.status = STATUS_PRELIMINARY
    elif application.application_status.startswith("APPLIED"):
        s.status = STATUS_READY if "FINAL" in application.application_status else STATUS_CONDITIONAL
        s.notes.append("Kablo projeye atanmış; katalog kaydı proje içine kopyalanmıştır.")
    if s.missing_inputs:
        s.status = STATUS_MISSING_DATA
    s.next_action = "Projeye kablo atanmamışsa aday seçin; atanmışsa ilk elektriksel ön eleme hesabını çalıştırın."
    stages.append(s)

    # 5 — Precheck
    precheck_status, precheck_notes = _engine_status(project, runtime, "precheck")
    if precheck_status is None:
        if application.last_iteration_status in {"READY", "CONDITIONAL_READY", "PASS", "COMPLETE"}:
            precheck_status = STATUS_COMPLETE if application.last_iteration_status in {"PASS", "COMPLETE"} else STATUS_CONDITIONAL
        elif project.cable.design_current_a > 0 and cable.conductor_area_mm2 > 0:
            precheck_status = STATUS_READY
        else:
            precheck_status = STATUS_BLOCKED
    s = _base_evaluation(STAGE_SPECS[4], precheck_status)
    s.notes.extend(precheck_notes)
    if project.cable.design_current_a <= 0:
        s.blocking_reasons.append("Tasarım akımı hesaplanmamış.")
    if cable.conductor_area_mm2 <= 0:
        s.blocking_reasons.append("Kablo adayı tanımlanmamış.")
    if s.blocking_reasons:
        s.status = STATUS_BLOCKED
    s.next_action = "IEC 60287 ve 2D termal doğrulamayı çalıştırın."
    stages.append(s)

    # 6 — Steady thermal
    thermal_states = [
        _engine_status(project, runtime, "iec60287"),
        _engine_status(project, runtime, "thermal_route"),
        _engine_status(project, runtime, "nodal"),
    ]
    thermal_statuses = [item[0] for item in thermal_states if item[0] is not None]
    thermal_notes = [note for _status, notes in thermal_states for note in notes]
    if any(item == STATUS_RUNNING for item in thermal_statuses):
        steady_status = STATUS_RUNNING
    elif any(item == STATUS_STALE for item in thermal_statuses):
        steady_status = STATUS_STALE
    elif thermal_statuses and all(item == STATUS_COMPLETE for item in thermal_statuses) and len(thermal_statuses) >= 2:
        steady_status = STATUS_COMPLETE
    elif any(item in {STATUS_COMPLETE, STATUS_CONDITIONAL} for item in thermal_statuses):
        steady_status = STATUS_CONDITIONAL
    elif any(item == STATUS_BLOCKED for item in thermal_statuses):
        steady_status = STATUS_BLOCKED
    else:
        legacy = _normalize_progress(progress.thermal)
        steady_status = legacy if legacy not in {STATUS_NOT_STARTED, STATUS_STALE} else STATUS_READY
    s = _base_evaluation(STAGE_SPECS[5], steady_status)
    s.notes.extend(list(dict.fromkeys(thermal_notes)))
    if not thermal.regions:
        s.blocking_reasons.append("Termal güzergâh bölgesi yok.")
        s.status = STATUS_BLOCKED
    if not cable.layers:
        s.blocking_reasons.append("Kablo katman geometrisi yok.")
        s.status = STATUS_BLOCKED
    if s.status == STATUS_STALE and not s.notes:
        s.notes.append("Termal sonuç mevcut ancak bağlı bir girdi değişmiştir; ayrıntı için Aşama Rehberi'ni açın.")
    s.next_action = "Joint, link box ve bonding ağını tanımlayın."
    stages.append(s)

    # 7 — Bonding
    bonding_engine_status, bonding_notes = _engine_status(project, runtime, "bonding")
    bonding_status = bonding_engine_status
    if bonding_status is None:
        bonding_status = _normalize_progress(progress.bonding)
    s = _base_evaluation(STAGE_SPECS[6], bonding_status)
    s.notes.extend(bonding_notes)
    if not project.bonding.minor_sections:
        s.missing_inputs.append("Bonding minor section")
    if not project.bonding.nodes:
        s.missing_inputs.append("Bonding düğümü / topraklama noktası")
    if s.missing_inputs:
        s.status = STATUS_MISSING_DATA
    elif bonding_engine_status is None and bonding_status in {
        STATUS_NOT_STARTED, STATUS_MISSING_DATA, STATUS_STALE, STATUS_BLOCKED
    }:
        s.status = STATUS_READY
        s.notes.append("Bonding girdileri tanımlı; doğrulanmış çalışma kaydı yok, motor çalıştırılabilir.")
    s.next_action = "Arıza, EPR ve metalik ekran dayanımını doğrulayın."
    stages.append(s)

    # 8 — Fault/EPR
    fault_engine_status, fault_notes = _engine_status(project, runtime, "fault_epr")
    fault_status = fault_engine_status
    if fault_status is None:
        fault_status = _normalize_progress(progress.fault_epr)
    s = _base_evaluation(STAGE_SPECS[7], fault_status)
    s.notes.extend(fault_notes)
    if not project.fault_study.scenarios:
        s.missing_inputs.append("En az bir arıza senaryosu")
    if cable.sheath_cross_section_mm2 <= 0:
        s.missing_inputs.append("Metalik ekran/kılıf kesiti")
    if s.missing_inputs:
        s.status = STATUS_MISSING_DATA
    elif fault_engine_status is None and fault_status in {
        STATUS_NOT_STARTED, STATUS_MISSING_DATA, STATUS_STALE, STATUS_BLOCKED
    }:
        s.status = STATUS_READY
        s.notes.append(
            f"{len(project.fault_study.scenarios)} arıza senaryosu tanımlı; "
            "doğrulanmış çalışma kaydı yok, motor çalıştırılabilir."
        )
    s.next_action = "SVL ihtiyacı ve yalıtım koordinasyonunu değerlendirin."
    stages.append(s)

    # 9 — SVL
    svl_engine_status, svl_notes = _engine_status(project, runtime, "svl")
    svl_status = svl_engine_status
    if svl_status is None:
        svl_status = _normalize_progress(progress.svl)
    s = _base_evaluation(STAGE_SPECS[8], svl_status)
    s.notes.extend(svl_notes)
    if not project.svl.candidates:
        s.missing_inputs.append("SVL adayı veya katalog sınıfı")
    if stages[7].status not in {STATUS_COMPLETE, STATUS_CONDITIONAL}:
        s.blocking_reasons.append("Arıza/EPR sonucu tamamlanmadan SVL sonucu nihai olamaz.")
        if s.status in {STATUS_NOT_STARTED, STATUS_READY}:
            s.status = STATUS_BLOCKED
    elif not s.missing_inputs and svl_engine_status is None and svl_status in {
        STATUS_NOT_STARTED, STATUS_MISSING_DATA, STATUS_STALE, STATUS_BLOCKED
    }:
        s.status = STATUS_READY
        s.notes.append("SVL adayları ve arıza/EPR sonucu mevcut; seçim motoru çalıştırılabilir.")
    s.next_action = "Geçici/çevrimsel yük profilini tanımlayın."
    stages.append(s)

    # 10 — Transient
    transient_status, transient_notes = _engine_status(project, runtime, "transient")
    if transient_status is None:
        transient_status = STATUS_COMPLETE if progress.thermal == "TRANSIENT_COMPLETE" else STATUS_NOT_STARTED
    s = _base_evaluation(STAGE_SPECS[9], transient_status)
    s.notes.extend(transient_notes)
    if not project.transient_study.profiles:
        s.missing_inputs.append("Yük-zaman profili")
        s.status = STATUS_MISSING_DATA
    elif transient_status == STATUS_NOT_STARTED:
        s.status = STATUS_READY
        s.notes.append("Yük-zaman profili tanımlı; IEC 60853 motoru henüz çalıştırılmadı.")
    s.next_action = "Birleşik tasarım iterasyonu için kapıları gözden geçirin."
    stages.append(s)

    # 11 — Combined iteration
    iteration_runtime, iteration_notes = _engine_status(project, runtime, "iteration")
    if iteration_runtime:
        iteration_status = iteration_runtime
    else:
        prerequisite = stages[0:10]
        hard_blockers = [item for item in prerequisite if item.status in {STATUS_MISSING_DATA, STATUS_BLOCKED}]
        if hard_blockers:
            iteration_status = STATUS_BLOCKED
        elif any(item.status in {STATUS_PRELIMINARY, STATUS_CONDITIONAL, STATUS_STALE, STATUS_NOT_STARTED} for item in prerequisite):
            iteration_status = STATUS_CONDITIONAL
        else:
            iteration_status = STATUS_READY
        if progress.final_design in {"READY", "COMPLETE", "PASS"}:
            iteration_status = STATUS_COMPLETE
    s = _base_evaluation(STAGE_SPECS[10], iteration_status)
    s.notes.extend(iteration_notes)
    if iteration_status == STATUS_BLOCKED:
        s.blocking_reasons.extend(
            f"{item.short_title}: {item.status}" for item in stages[:10]
            if item.status in {STATUS_MISSING_DATA, STATUS_BLOCKED}
        )
    s.next_action = "Tasarım kararını kaydedin; rapor ve tedarik çıktılarını üretin."
    stages.append(s)

    # 12 — Deliverables
    report_status, report_notes = _engine_status(project, runtime, "report")
    procurement_status, procurement_notes = _engine_status(project, runtime, "procurement")
    deliverable_runtime = _runtime_status(runtime, "deliverables")
    if deliverable_runtime:
        deliverable_status = deliverable_runtime
    elif any(item == STATUS_STALE for item in (report_status, procurement_status)):
        deliverable_status = STATUS_STALE
    elif report_status == STATUS_COMPLETE and procurement_status == STATUS_COMPLETE:
        deliverable_status = STATUS_COMPLETE
    elif any(item in {STATUS_COMPLETE, STATUS_CONDITIONAL} for item in (report_status, procurement_status)):
        deliverable_status = STATUS_CONDITIONAL
    elif stages[10].status == STATUS_COMPLETE:
        deliverable_status = STATUS_READY
    elif stages[10].status in {STATUS_READY, STATUS_CONDITIONAL}:
        deliverable_status = STATUS_CONDITIONAL
    else:
        deliverable_status = STATUS_BLOCKED
    s = _base_evaluation(STAGE_SPECS[11], deliverable_status)
    s.notes.extend(list(dict.fromkeys(report_notes + procurement_notes)))
    if deliverable_status == STATUS_BLOCKED:
        s.blocking_reasons.append("Birleşik tasarım kararı henüz rapor kapısını açmıyor.")
    s.next_action = "Rapor oluşturun veya BOQ/BOM/RFQ paketini üretin."
    stages.append(s)

    for stage in stages:
        _stage_dimensions(project, stage)

    current_stage_id = getattr(project.workflow, "current_stage_id", "system_load") or "system_load"
    if current_stage_id not in {item.stage_id for item in stages}:
        current_stage_id = "system_load"

    recommended = next(
        (
            item for item in stages
            if item.status in {
                STATUS_MISSING_DATA,
                STATUS_BLOCKED,
                STATUS_PRELIMINARY,
                STATUS_READY,
                STATUS_CONDITIONAL,
                STATUS_STALE,
                STATUS_NOT_STARTED,
            }
        ),
        stages[-1],
    )
    if all(item.status == STATUS_COMPLETE for item in stages[:-1]):
        overall_status = STATUS_COMPLETE
    elif any(item.status in {STATUS_MISSING_DATA, STATUS_BLOCKED} for item in stages):
        overall_status = STATUS_BLOCKED
    elif any(item.status in {STATUS_CONDITIONAL, STATUS_PRELIMINARY, STATUS_STALE} for item in stages):
        overall_status = STATUS_CONDITIONAL
    else:
        overall_status = STATUS_READY

    return ProjectWorkflowEvaluation(
        stages=stages,
        current_stage_id=current_stage_id,
        recommended_stage_id=recommended.stage_id,
        recommended_action=recommended.next_action,
        overall_status=overall_status,
    )


def workflow_stage_specs() -> tuple[WorkflowStageSpec, ...]:
    return STAGE_SPECS
