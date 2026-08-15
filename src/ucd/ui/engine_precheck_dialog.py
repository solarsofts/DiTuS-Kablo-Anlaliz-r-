from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ucd.calculations.engine_precheck import (
    CHECK_ASSUMPTION,
    CHECK_MISSING,
    GATE_HARD,
    PRECHECK_BLOCKED,
    PRECHECK_CONDITIONAL,
    EnginePrecheckResult,
)
from .window_layout import fit_window, DENSITY_NORMAL


class EnginePrecheckDialog(QDialog):
    """Compact, explicit gate review shown before a calculation starts."""

    CANCEL = 0
    RUN = 1
    OPEN_MISSING = 2

    def __init__(
        self,
        result: EnginePrecheckResult,
        mascot_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.result = result
        self.setWindowTitle(f"Hesap Ön Kontrolü — {result.method.display_name}")
        self.setModal(True)
        fit_window(self, DENSITY_NORMAL)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(9)

        header = QHBoxLayout()
        logo = QLabel()
        logo.setFixedSize(68, 68)
        logo.setAlignment(Qt.AlignCenter)
        if mascot_path and mascot_path.exists():
            pixmap = QPixmap(str(mascot_path))
            if not pixmap.isNull():
                logo.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo)

        text = QVBoxLayout()
        title = QLabel(result.method.display_name)
        title.setWordWrap(True)
        title.setStyleSheet("font-size:14pt; font-weight:800; color:#153f60;")
        text.addWidget(title)
        basis = QLabel(result.method.standard_basis)
        basis.setWordWrap(True)
        basis.setStyleSheet("color:#52697b;")
        text.addWidget(basis)
        header.addLayout(text, 1)

        self.status = QLabel(result.summary())
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setMinimumWidth(180)
        if result.status == PRECHECK_BLOCKED:
            self.status.setStyleSheet(
                "background:#fce8e8; color:#8f2020; border:1px solid #cf6666; "
                "border-radius:6px; padding:10px; font-weight:800;"
            )
        elif result.status == PRECHECK_CONDITIONAL:
            self.status.setStyleSheet(
                "background:#fff4dc; color:#805400; border:1px solid #dfad42; "
                "border-radius:6px; padding:10px; font-weight:800;"
            )
        else:
            self.status.setStyleSheet(
                "background:#e8f7ed; color:#24653a; border:1px solid #70b184; "
                "border-radius:6px; padding:10px; font-weight:800;"
            )
        header.addWidget(self.status)
        outer.addLayout(header)

        info = QLabel(
            "Zorunlu (HARD) girdi eksikse motor çalışmaz. Önerilen (SOFT) veri eksikse "
            "hesap açık varsayımlarla koşullu ön mühendislik seviyesinde çalışabilir."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background:#edf4fa; border:1px solid #bfd1df; padding:7px;")
        outer.addWidget(info)

        self.table = QTableWidget(len(result.items), 5)
        self.table.setHorizontalHeaderLabels(["Kapı", "Durum", "Girdi", "Açıklama", "Veri sahibi"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        for row, item in enumerate(result.items):
            state = "Eksik" if item.status == CHECK_MISSING else (
                "Varsayım" if item.status == CHECK_ASSUMPTION else "Mevcut"
            )
            values = [
                "Zorunlu" if item.gate == GATE_HARD else "Önerilen",
                state,
                item.label,
                item.detail or "—",
                item.owner_label or "—",
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if item.status == CHECK_MISSING:
                    cell.setBackground(QColor("#fff0f0") if item.gate == GATE_HARD else QColor("#fff8df"))
                elif item.status == CHECK_ASSUMPTION:
                    cell.setBackground(QColor("#fff4dc"))
                self.table.setItem(row, col, cell)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        outer.addWidget(self.table, 1)

        details: list[str] = []
        if result.assumptions:
            details.append("KULLANILACAK VARSAYIMLAR")
            details.extend(f"• {item}" for item in result.assumptions)
        if result.notes:
            if details:
                details.append("")
            details.append("YÖNTEM SINIRI / NOTLAR")
            details.extend(f"• {item}" for item in result.notes)
        if details:
            note = QPlainTextEdit("\n".join(details))
            note.setReadOnly(True)
            note.setMaximumHeight(145)
            note.setStyleSheet("background:#fafbfc; border:1px solid #d6dde4;")
            outer.addWidget(note)

        buttons = QHBoxLayout()
        self.open_missing = QPushButton("Eksikleri Tamamla")
        self.open_missing.setEnabled(bool(result.hard_missing or result.soft_missing))
        self.open_missing.clicked.connect(lambda: self.done(self.OPEN_MISSING))
        buttons.addWidget(self.open_missing)
        buttons.addStretch(1)
        cancel = QPushButton("İptal")
        cancel.clicked.connect(lambda: self.done(self.CANCEL))
        buttons.addWidget(cancel)
        run = QPushButton("Koşullu Hesapla" if result.status == PRECHECK_CONDITIONAL else "Hesabı Başlat")
        run.setEnabled(result.can_run)
        run.setDefault(result.can_run)
        run.setStyleSheet(
            "background:#2e76b5; color:white; font-weight:750; padding:8px 16px; border-radius:4px;"
        )
        run.clicked.connect(lambda: self.done(self.RUN))
        buttons.addWidget(run)
        outer.addLayout(buttons)
