from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ucd.calculations.calculation_policy import (
    audit_calculation_policy,
    bootstrap_calculation_policy,
    register_parameter_provenance,
    render_calculation_policy_audit,
)
from ucd.models.project import (
    CALC_METHOD_CERTIFIED_INPUT,
    CALC_METHOD_LEGACY_COEFFICIENT,
    CALC_METHOD_MANUAL_OVERRIDE,
    CALC_METHOD_PHYSICAL_AUTO,
    CALC_STATUS_CALCULATED,
    CALC_STATUS_PRELIMINARY_ONLY,
    CALC_STATUS_REQUIRES_CONFIRMATION,
    CALC_STATUS_VERIFIED,
    ProjectData,
)
from .window_layout import fit_window, DENSITY_NORMAL, DENSITY_WIDE


METHODS = (
    CALC_METHOD_PHYSICAL_AUTO,
    CALC_METHOD_CERTIFIED_INPUT,
    CALC_METHOD_MANUAL_OVERRIDE,
    CALC_METHOD_LEGACY_COEFFICIENT,
)
STATUSES = (
    CALC_STATUS_CALCULATED,
    CALC_STATUS_VERIFIED,
    CALC_STATUS_PRELIMINARY_ONLY,
    CALC_STATUS_REQUIRES_CONFIRMATION,
)


class ParameterProvenanceDialog(QDialog):
    """Edit only source/method metadata; engineering values remain read-only."""

    def __init__(
        self,
        project: ProjectData,
        on_changed: Callable[[], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.project = project
        self.on_changed = on_changed
        bootstrap_calculation_policy(self.project)

        self.setWindowTitle("DiTuS — Hesap Parametreleri ve Kaynakları v0.16.6")
        fit_window(self, DENSITY_WIDE)

        layout = QVBoxLayout(self)
        title = QLabel(
            "Fiziksel hesap / doğrulanmış girdi / manuel override / legacy katsayı ayrımı"
        )
        title.setStyleSheet("font-size:13pt; font-weight:800; color:#173d5d; padding:4px;")
        layout.addWidget(title)

        explanation = QLabel(
            "Bu ekran sayısal değerleri değiştirmez. Yalnız mevcut solver girdisinin kaynağını, "
            "yöntemini, statüsünü ve geçerlilik kapsamını kaydeder. Legacy katsayılar nihai tasarım "
            "kapısını bloke edecek şekilde işaretlenir."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("padding:7px; background:#eef4f8; border:1px solid #c9d7e2;")
        layout.addWidget(explanation)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-weight:700; padding:5px;")
        layout.addWidget(self.summary_label)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels([
            "Parametre", "Güncel değer", "Birim", "Yöntem", "Statü",
            "Kaynak tipi", "Kaynak / doküman", "Sayfa", "Standart",
            "Geçerlilik kapsamı", "Override gerekçesi / not",
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setWordWrap(True)
        layout.addWidget(self.table, 1)

        controls = QHBoxLayout()
        self.audit_button = QPushButton("Kaynak Denetimini Yenile")
        self.audit_button.clicked.connect(self._show_audit)
        controls.addWidget(self.audit_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Save).setText("Kaynak Kayıtlarını Kaydet")
        buttons.button(QDialogButtonBox.Close).setText("Kapat")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate()

    @staticmethod
    def _read_path(project: ProjectData, path: str):
        value = project
        for token in path.split("."):
            value = getattr(value, token)
        return value

    @staticmethod
    def _readonly_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _populate(self) -> None:
        records = sorted(
            self.project.calculation_policy.parameter_records,
            key=lambda item: (item.category, item.label),
        )
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            current = self._read_path(self.project, record.parameter_path)
            parameter_item = self._readonly_item(record.label)
            parameter_item.setData(Qt.UserRole, record.parameter_path)
            self.table.setItem(row, 0, parameter_item)
            self.table.setItem(row, 1, self._readonly_item(f"{current:g}" if isinstance(current, float) else str(current)))
            self.table.setItem(row, 2, self._readonly_item(record.unit))

            method_combo = QComboBox()
            method_combo.addItems(METHODS)
            method_combo.setCurrentText(record.method)
            self.table.setCellWidget(row, 3, method_combo)

            status_combo = QComboBox()
            status_combo.addItems(STATUSES)
            status_combo.setCurrentText(record.status)
            self.table.setCellWidget(row, 4, status_combo)

            for column, value in (
                (5, record.source_type),
                (6, record.source_reference),
                (7, record.source_page),
                (8, record.standard_reference),
                (9, record.validity_scope),
                (10, " | ".join(part for part in (record.override_reason, record.notes) if part)),
            ):
                self.table.setItem(row, column, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(6, 260)
        self.table.setColumnWidth(8, 250)
        self.table.setColumnWidth(9, 300)
        self.table.setColumnWidth(10, 300)
        self.table.horizontalHeader().setStretchLastSection(True)
        self._update_summary()

    def _update_summary(self) -> None:
        audit = audit_calculation_policy(self.project)
        state = "BLOKE" if audit.final_design_blocked else "AÇIK"
        self.summary_label.setText(
            f"Kayıt: {len(audit.records)} | Uyarı: {audit.warning_count} | "
            f"Hata: {audit.error_count} | Nihai tasarım kapısı: {state}"
        )

    def _save(self) -> None:
        try:
            for row in range(self.table.rowCount()):
                parameter_path = str(self.table.item(row, 0).data(Qt.UserRole))
                method = self.table.cellWidget(row, 3).currentText()
                status = self.table.cellWidget(row, 4).currentText()
                source_type = self.table.item(row, 5).text().strip()
                source_reference = self.table.item(row, 6).text().strip()
                source_page = self.table.item(row, 7).text().strip()
                standard_reference = self.table.item(row, 8).text().strip()
                validity_scope = self.table.item(row, 9).text().strip()
                note_text = self.table.item(row, 10).text().strip()

                if method == CALC_METHOD_MANUAL_OVERRIDE and not note_text:
                    raise ValueError(
                        f"{self.table.item(row, 0).text()}: manuel override için gerekçe zorunludur."
                    )
                register_parameter_provenance(
                    self.project,
                    parameter_path,
                    method=method,
                    status=status,
                    source_type=source_type or "PROJECT_INPUT",
                    source_reference=source_reference,
                    source_page=source_page,
                    standard_reference=standard_reference,
                    validity_scope=validity_scope,
                    confidence="HIGH" if status in {CALC_STATUS_CALCULATED, CALC_STATUS_VERIFIED} else "MEDIUM",
                    override_reason=note_text if method == CALC_METHOD_MANUAL_OVERRIDE else "",
                    notes="" if method == CALC_METHOD_MANUAL_OVERRIDE else note_text,
                )
        except Exception as exc:
            QMessageBox.warning(self, "Kaynak kaydı tamamlanamadı", str(exc))
            return

        self._update_summary()
        if self.on_changed is not None:
            self.on_changed()
        QMessageBox.information(
            self,
            "Kaynak kayıtları kaydedildi",
            "Yalnız parametre kaynak/yöntem metadatası güncellendi; sayısal solver girdileri değiştirilmedi.",
        )

    def _show_audit(self) -> None:
        self._update_summary()
        dialog = QDialog(self)
        dialog.setWindowTitle("Hesap Parametreleri Kaynak Denetimi")
        fit_window(dialog, DENSITY_NORMAL, center_on=self)
        layout = QVBoxLayout(dialog)
        text = QTableWidget(0, 1)
        text.setHorizontalHeaderLabels(["Denetim sonucu"])
        lines = render_calculation_policy_audit(self.project).splitlines()
        text.setRowCount(len(lines))
        for row, line in enumerate(lines):
            text.setItem(row, 0, self._readonly_item(line))
        text.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()
