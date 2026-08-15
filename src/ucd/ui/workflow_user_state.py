from __future__ import annotations

from dataclasses import dataclass

from ucd.calculations.project_workflow import (
    STATUS_BLOCKED,
    STATUS_COMPLETE,
    STATUS_CONDITIONAL,
    STATUS_MISSING_DATA,
    STATUS_NOT_STARTED,
    STATUS_PRELIMINARY,
    STATUS_READY,
    STATUS_RUNNING,
    STATUS_STALE,
    WorkflowStageEvaluation,
)


@dataclass(frozen=True)
class UserStageState:
    """Concise user-facing workflow state.

    The calculation registry keeps its four technical dimensions, while this
    view deliberately answers only three questions: What is the state? Why?
    What should the user do next?
    """

    label: str
    reason: str
    action: str
    color_status: str


def _first(items: list[str], fallback: str = "") -> str:
    return items[0].strip() if items else fallback


def _stale_reason(stage: WorkflowStageEvaluation) -> str:
    for note in stage.notes:
        if note.startswith("Sonuçtan sonra değişen girdiler:"):
            value = note.split(":", 1)[1].strip()
            first = value.split(",", 1)[0].strip()
            if first:
                return f"{first} değişti."
    return "Bağlı proje verisi değişti."


def user_stage_state(stage: WorkflowStageEvaluation) -> UserStageState:
    action = stage.next_action or "Bu aşamayı açın."

    if stage.run_status == "RUNNING" or stage.status == STATUS_RUNNING:
        return UserStageState("Çalışıyor", "Hesap motoru çalışıyor.", action, STATUS_RUNNING)

    if stage.freshness == "STALE" or stage.status == STATUS_STALE:
        return UserStageState("Yeniden hesapla", _stale_reason(stage), action, STATUS_STALE)

    if stage.blocking_reasons or stage.status == STATUS_BLOCKED:
        reason = _first(stage.blocking_reasons, "Zorunlu bir önceki aşama tamamlanmadı.")
        return UserStageState("Bloke", reason, action, STATUS_BLOCKED)

    if stage.missing_inputs or stage.status == STATUS_MISSING_DATA or stage.input_readiness == "MISSING":
        reason = _first(stage.missing_inputs, "Zorunlu proje verisi eksik.")
        return UserStageState("Veri gerekli", reason, action, STATUS_MISSING_DATA)

    if stage.run_status == "SUCCESS":
        if stage.maturity == "VERIFIED" and stage.status == STATUS_COMPLETE:
            return UserStageState("Tamamlandı", "Sonuç güncel ve doğrulanmış girdilere dayanıyor.", action, STATUS_COMPLETE)
        reason = _first(stage.notes, "Hesap tamamlandı; doğrulanması gereken kabuller var.")
        return UserStageState("Koşullu", reason, action, STATUS_CONDITIONAL)

    if stage.status == STATUS_COMPLETE:
        return UserStageState("Tamamlandı", "Bu aşamanın güncel sonucu mevcut.", action, STATUS_COMPLETE)

    if stage.status in {STATUS_READY} or stage.input_readiness == "COMPLETE":
        return UserStageState("Hesaplanabilir", "Gerekli ana girdiler mevcut.", action, STATUS_READY)

    if stage.status in {STATUS_PRELIMINARY, STATUS_CONDITIONAL} or stage.input_readiness == "PRELIMINARY":
        reason = _first(stage.notes, "Ön tasarım verisi mevcut; kullanıcı onayı veya doğrulama gerekiyor.")
        return UserStageState("Koşullu", reason, action, STATUS_CONDITIONAL)

    if stage.status == STATUS_NOT_STARTED or stage.run_status == "NOT_RUN":
        return UserStageState("Yapılacak", "Bu aşamada henüz işlem yapılmadı.", action, STATUS_NOT_STARTED)

    return UserStageState("Yapılacak", "Bu aşamayı gözden geçirin.", action, STATUS_NOT_STARTED)
