from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

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
    ProjectWorkflowEvaluation,
    WorkflowStageEvaluation,
)
from ucd.ui.workflow_user_state import user_stage_state


STATUS_TR = {
    STATUS_NOT_STARTED: "Yapılacak",
    STATUS_MISSING_DATA: "Veri gerekli",
    STATUS_PRELIMINARY: "Koşullu",
    STATUS_READY: "Hesaplanabilir",
    STATUS_RUNNING: "Çalışıyor",
    STATUS_CONDITIONAL: "Koşullu",
    STATUS_COMPLETE: "Tamamlandı",
    STATUS_STALE: "Yeniden hesapla",
    STATUS_BLOCKED: "Bloke",
}

INPUT_READINESS_TR = {
    "MISSING": "Eksik", "PRELIMINARY": "Ön kabul", "COMPLETE": "Tam", "UNKNOWN": "Bilinmiyor",
}
RUN_STATUS_TR = {
    "NOT_RUN": "Çalıştırılmadı", "RUNNING": "Çalışıyor", "SUCCESS": "Başarılı",
    "FAILED": "Başarısız", "NOT_APPLICABLE": "Uygulanmaz",
}
FRESHNESS_TR = {
    "CURRENT": "Güncel", "STALE": "Yeniden hesapla", "NOT_APPLICABLE": "Uygulanmaz",
}
MATURITY_TR = {
    "SCREENING": "Ön eleme", "CONDITIONAL": "Koşullu", "VERIFIED": "Doğrulanmış",
}

STATUS_COLORS = {
    STATUS_NOT_STARTED: ("#eef2f5", "#536675", "#c6d0d9"),
    STATUS_MISSING_DATA: ("#fff0f0", "#a92323", "#dd8a8a"),
    STATUS_PRELIMINARY: ("#fff8df", "#775c00", "#d8bd58"),
    STATUS_READY: ("#e8f3ff", "#1f5f91", "#6ea8d6"),
    STATUS_RUNNING: ("#e7f2ff", "#0e5ca3", "#4d95d1"),
    STATUS_CONDITIONAL: ("#fff4dc", "#8b5e00", "#dfad42"),
    STATUS_COMPLETE: ("#e8f7ed", "#24653a", "#70b184"),
    STATUS_STALE: ("#f2ebff", "#67438a", "#aa8ac7"),
    STATUS_BLOCKED: ("#fce8e8", "#8f2020", "#cf6666"),
}


def status_text(status: str) -> str:
    return STATUS_TR.get(status, status)


def status_style(status: str) -> str:
    bg, fg, border = STATUS_COLORS.get(status, STATUS_COLORS[STATUS_NOT_STARTED])
    return (
        f"background:{bg}; color:{fg}; border:1px solid {border}; "
        "border-radius:5px; padding:4px 8px; font-weight:700;"
    )


class WorkflowStageBar(QWidget):
    stageSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._evaluation: ProjectWorkflowEvaluation | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(3)
        caption = QLabel("PROJE TASARIM AKIŞI")
        caption.setStyleSheet("font-weight:750; color:#173d5d; padding-left:4px;")
        outer.addWidget(caption)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        self._row = QHBoxLayout(content)
        self._row.setContentsMargins(2, 2, 2, 4)
        self._row.setSpacing(5)
        self._row.addStretch(1)
        scroll.setWidget(content)
        scroll.setFixedHeight(72)
        outer.addWidget(scroll)

    def set_evaluation(self, evaluation: ProjectWorkflowEvaluation) -> None:
        self._evaluation = evaluation
        existing = set(self._buttons)
        for stage in evaluation.stages:
            button = self._buttons.get(stage.stage_id)
            if button is None:
                button = QPushButton()
                button.setCheckable(True)
                button.setMinimumWidth(108)
                button.setMaximumHeight(52)
                button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                button.clicked.connect(lambda checked=False, sid=stage.stage_id: self.stageSelected.emit(sid))
                self._row.insertWidget(self._row.count() - 1, button)
                self._buttons[stage.stage_id] = button
            existing.discard(stage.stage_id)
            button.setText(f"{stage.number}. {stage.short_title}\n{status_text(stage.status)}")
            button.setToolTip(
                f"{stage.title}\nDurum: {status_text(stage.status)}\nSonraki işlem: {stage.next_action}"
            )
            bg, fg, border = STATUS_COLORS.get(stage.status, STATUS_COLORS[STATUS_NOT_STARTED])
            checked = stage.stage_id == evaluation.current_stage_id
            extra = "border-width:2px;" if checked else ""
            button.setStyleSheet(
                "QPushButton {"
                f"background:{bg}; color:{fg}; border:1px solid {border}; {extra}"
                "border-radius:6px; padding:5px 8px; text-align:left; font-weight:650;"
                "} QPushButton:hover { border-color:#2c6eaa; }"
                "QPushButton:checked { border:2px solid #123f63; }"
            )
            button.setChecked(checked)
        for stage_id in existing:
            button = self._buttons.pop(stage_id)
            self._row.removeWidget(button)
            button.deleteLater()

    def select_stage(self, stage_id: str) -> None:
        for sid, button in self._buttons.items():
            button.setChecked(sid == stage_id)


class WorkflowGuideWidget(QWidget):
    openStageRequested = Signal(str)
    openRecommendedRequested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._stage_id = ""
        self._recommended_stage_id = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)
        self.title = QLabel("Aşama Rehberi")
        self.title.setWordWrap(True)
        self.title.setStyleSheet("font-size:12pt; font-weight:750; color:#173d5d;")
        layout.addWidget(self.title)
        self.status = QLabel("—")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setFrameShape(QFrame.NoFrame)
        self.detail.setStyleSheet("background:#f8fafc; border:1px solid #d5dde5;")
        layout.addWidget(self.detail, 1)
        self.open_stage = QPushButton("Bu Aşamayı Aç")
        self.open_stage.clicked.connect(lambda: self.openStageRequested.emit(self._stage_id))
        layout.addWidget(self.open_stage)
        self.open_recommended = QPushButton("Önerilen Sonraki Adıma Git")
        self.open_recommended.setStyleSheet(
            "background:#d98919; color:white; font-weight:700; padding:8px 10px; border-radius:4px;"
        )
        self.open_recommended.clicked.connect(
            lambda: self.openRecommendedRequested.emit(self._recommended_stage_id)
        )
        layout.addWidget(self.open_recommended)

    def set_stage(
        self,
        stage: WorkflowStageEvaluation,
        evaluation: ProjectWorkflowEvaluation,
    ) -> None:
        self._stage_id = stage.stage_id
        self._recommended_stage_id = evaluation.recommended_stage_id
        display = user_stage_state(stage)
        self.title.setText(f"{stage.number}. {stage.title}")
        self.status.setText(display.label)
        self.status.setStyleSheet(status_style(display.color_status))

        parts: list[str] = []
        parts.append("ŞU ANKİ DURUM")
        parts.append(f"• {display.reason}")
        parts.append("")
        parts.append("BU AŞAMADA KULLANICI NE TANIMLAR?")
        parts.extend(f"• {item}" for item in stage.user_inputs)
        parts.append("")
        if stage.missing_inputs:
            parts.append("TAMAMLANMASI GEREKENLER")
            parts.extend(f"• {item}" for item in stage.missing_inputs)
            parts.append("")
        if stage.blocking_reasons:
            parts.append("İLERLEMEYİ ENGELLEYENLER")
            parts.extend(f"• {item}" for item in stage.blocking_reasons)
            parts.append("")
        parts.append("BU ADIM NE ÜRETİR?")
        parts.extend(f"• {item}" for item in stage.outputs)
        parts.append("")
        parts.append("ÇALIŞACAK MOTORLAR")
        parts.extend(f"• {item}" for item in stage.engines)
        parts.append("")
        parts.append("SONRAKİ TEK İŞLEM")
        parts.append(display.action)
        if stage.notes:
            parts.extend(["", "TEKNİK AYRINTI"])
            parts.extend(f"• {item}" for item in stage.notes)
        self.detail.setPlainText("\n".join(parts))
        self.open_recommended.setText(
            f"Önerilen: {evaluation.stage(evaluation.recommended_stage_id).short_title}"
        )


class ProjectIdentityHeader(QWidget):
    def __init__(self, mascot_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)
        self.logo = QLabel()
        self.logo.setFixedSize(QSize(54, 54))
        self.logo.setAlignment(Qt.AlignCenter)
        if mascot_path.exists():
            pixmap = QPixmap(str(mascot_path))
            if not pixmap.isNull():
                self.logo.setPixmap(pixmap.scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.logo)
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        self.project_title = QLabel("DiTuS Kablo Analizör")
        self.project_title.setStyleSheet("font-size:13pt; font-weight:800; color:#163d5d;")
        self.project_meta = QLabel()
        self.project_meta.setStyleSheet("color:#536675;")
        text_col.addWidget(self.project_title)
        text_col.addWidget(self.project_meta)
        layout.addLayout(text_col, 1)
        self.overall_status = QLabel("—")
        self.overall_status.setAlignment(Qt.AlignCenter)
        self.overall_status.setMinimumWidth(130)
        layout.addWidget(self.overall_status)
        self.setStyleSheet("background:#f8fafc; border:1px solid #ccd7e1; border-radius:6px;")

    def update_project(self, project_name: str, project_code: str, overall_status: str) -> None:
        self.project_title.setText(project_name or "DiTuS Kablo Analizör")
        self.project_meta.setText(f"{project_code or '—'} · DiTuS Kablo Analizör")
        self.overall_status.setText(status_text(overall_status))
        self.overall_status.setStyleSheet(status_style(overall_status))
