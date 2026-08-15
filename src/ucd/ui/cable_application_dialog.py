from __future__ import annotations

from copy import deepcopy
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ucd.calculations.project_application import (
    ProjectCableApplicationError,
    apply_catalog_candidate_to_project,
    assess_cable_completion,
    evaluate_application_iteration_gates,
    resolve_source_conflict,
)
from ucd.models.project import (
    CONFLICT_CREATE_SCENARIOS,
    CONFLICT_UNRESOLVED,
    CONFLICT_USE_SOURCE,
    CONFLICT_USE_USER_VALUE,
    ProjectData,
)
from .window_layout import fit_window, DENSITY_NORMAL


class CableApplicationDialog(QDialog):
    """Apply one catalog candidate to selected route sections with explicit data gates."""

    def __init__(
        self,
        project: ProjectData,
        record_id: str,
        candidate_id: str,
        parallel_cables_per_phase: int,
        on_applied: Callable[[], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.project = project
        self.record_id = record_id
        self.candidate_id = candidate_id
        self.parallel = parallel_cables_per_phase
        self.on_applied = on_applied
        self.route_checks: dict[str, QCheckBox] = {}
        self.conflict_combos: dict[str, QComboBox] = {}
        self.applied = False
        self.setWindowTitle("Gerçek Kabloyu Projeye Uygulama")
        fit_window(self, DENSITY_NORMAL)
        self._build_ui()
        self._refresh_preview()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        record = next((r for r in self.project.cable_library.records if r.record_id == self.record_id), None)
        header = QLabel(
            f"{record.manufacturer if record else ''} · {record.model if record else self.record_id}\n"
            f"Aday: {self.candidate_id} · {self.parallel} kablo/faz"
        )
        header.setStyleSheet("font-size: 13pt; font-weight: 700; color: #183b56; padding: 7px;")
        layout.addWidget(header)

        notice = QLabel(
            "Bu işlem seçilen katalog kaydını proje içine kopyalar. Katalog daha sonra değişse bile "
            "bu projede kullanılan kablo verisi değişmez. Eksik katman geometrisi veya termal değerler "
            "üretici verisi olarak kabul edilmez."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("background: #fff7d6; color: #6d5510; padding: 8px;")
        layout.addWidget(notice)

        tabs = QTabWidget()
        tabs.addTab(self._build_route_tab(), "1 · Güzergâh Ataması")
        tabs.addTab(self._build_completion_tab(), "2 · Veri Tamamlama")
        tabs.addTab(self._build_conflict_tab(), "3 · Kaynak Çelişkileri")
        tabs.addTab(self._build_gate_tab(), "4 · İterasyon Kapıları")
        layout.addWidget(tabs, 1)

        actions = QHBoxLayout()
        refresh = QPushButton("Önizlemeyi Yenile")
        refresh.clicked.connect(self._refresh_preview)
        apply_button = QPushButton("Seçili Kabloyu Projeye Ata")
        apply_button.clicked.connect(self._apply)
        actions.addWidget(refresh)
        actions.addStretch(1)
        actions.addWidget(apply_button)
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_route_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        info = QLabel(
            "Aynı proje kablosunun uygulanacağı yeraltı güzergâh bölümlerini seçin. "
            "Seçilmeyen bölümler kayıt altında kalır ancak aktif kablo ataması almaz."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        group = QGroupBox("Yeraltı güzergâh bölümleri")
        group_layout = QVBoxLayout(group)
        for section in self.project.route_sections:
            check = QCheckBox(f"{section.name} — {section.length_m:g} m — {section.section_type}")
            check.setChecked(True)
            check.toggled.connect(self._refresh_preview)
            group_layout.addWidget(check)
            self.route_checks[section.name] = check
        group_layout.addStretch(1)
        layout.addWidget(group, 1)
        return tab

    def _build_completion_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.completion_summary = QLabel()
        self.completion_summary.setWordWrap(True)
        self.completion_summary.setStyleSheet("font-weight: 650; padding: 7px; background: #eaf0f5;")
        layout.addWidget(self.completion_summary)
        self.completion_table = QTableWidget(0, 8)
        self.completion_table.setHorizontalHeaderLabels(
            ["Kategori", "Parametre", "Durum", "Değer", "Birim", "Kaynak", "Gerekli hesap", "Not"]
        )
        self.completion_table.setAlternatingRowColors(True)
        self.completion_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.completion_table, 1)
        return tab

    def _build_conflict_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        info = QLabel(
            "Kaynak kayıtları silinmez veya birbiriyle birleştirilmez. Karar, kaynak değerinden ayrı bir denetim kaydı olarak saklanır."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        self.conflict_table = QTableWidget(len(self.project.source_audit.conflicts), 5)
        self.conflict_table.setHorizontalHeaderLabels(["Önem", "Çelişki", "Kaynak değerler", "Karar", "Mevcut durum"])
        records = {item.record_id: item for item in self.project.source_audit.records}
        existing = {item.conflict_id: item for item in self.project.cable_application.conflict_decisions}
        for row, conflict in enumerate(self.project.source_audit.conflicts):
            values = []
            for record_id in conflict.record_ids:
                record = records.get(record_id)
                if record:
                    values.append(f"{record_id}: {record.value} {record.unit} ({record.context})")
            for col, text in enumerate((conflict.severity, conflict.title, "\n".join(values))):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.conflict_table.setItem(row, col, item)
            combo = QComboBox()
            combo.addItem("Kararsız bırak", (CONFLICT_UNRESOLVED, [], None, ""))
            for record_id in conflict.record_ids:
                record = records.get(record_id)
                if record:
                    combo.addItem(
                        f"Kaynak kullan: {record_id} = {record.value} {record.unit}",
                        (CONFLICT_USE_SOURCE, [record_id], record.value, record.unit),
                    )
            combo.addItem("Ayrı senaryolar oluştur", (CONFLICT_CREATE_SCENARIOS, list(conflict.record_ids), None, ""))
            combo.addItem("Kullanıcı tarafından doğrulanmış değer gir", (CONFLICT_USE_USER_VALUE, [], None, ""))
            previous = existing.get(conflict.conflict_id)
            if previous:
                for index in range(combo.count()):
                    action, selected, _, _ = combo.itemData(index)
                    if action == previous.action and (action != CONFLICT_USE_SOURCE or selected == previous.selected_record_ids):
                        combo.setCurrentIndex(index)
                        break
            elif conflict.disposition and conflict.disposition != CONFLICT_UNRESOLVED:
                # Preserve source-document baseline dispositions without pretending they were user decisions.
                combo.setToolTip(f"Kaynak vakadaki mevcut disposition: {conflict.disposition}")
            self.conflict_table.setCellWidget(row, 3, combo)
            self.conflict_combos[conflict.conflict_id] = combo
            state = QTableWidgetItem(conflict.disposition or CONFLICT_UNRESOLVED)
            state.setFlags(state.flags() & ~Qt.ItemIsEditable)
            self.conflict_table.setItem(row, 4, state)
        self.conflict_table.resizeColumnsToContents()
        self.conflict_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.conflict_table, 1)
        return tab

    def _build_gate_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.gate_summary = QLabel()
        self.gate_summary.setStyleSheet("font-weight: 700; padding: 7px; background: #eaf0f5;")
        layout.addWidget(self.gate_summary)
        self.gate_text = QPlainTextEdit()
        self.gate_text.setReadOnly(True)
        layout.addWidget(self.gate_text, 1)
        return tab

    def _selected_sections(self) -> list[str]:
        return [name for name, check in self.route_checks.items() if check.isChecked()]

    def _temporary_project(self) -> ProjectData:
        temp = deepcopy(self.project)
        apply_catalog_candidate_to_project(
            temp,
            self.record_id,
            self.candidate_id,
            self.parallel,
            self._selected_sections(),
        )
        return temp

    def _refresh_preview(self) -> None:
        try:
            temp = self._temporary_project()
            completion = assess_cable_completion(temp)
        except Exception as exc:
            self.completion_summary.setText(f"Önizleme hazırlanamadı: {exc}")
            return
        self.completion_summary.setText(
            f"Durum: {completion.status} · bloke eden eksik {completion.blocking_count} · "
            f"üretici teyidi {completion.manufacturer_confirmation_count} · varsayım {completion.assumption_count}"
        )
        self.completion_table.setRowCount(len(completion.items))
        for row, item in enumerate(completion.items):
            value = "—" if item.value is None else str(item.value)
            values = [
                item.category, item.label, item.status, value, item.unit, item.source_reference,
                ", ".join(item.required_for), item.notes,
            ]
            for col, text in enumerate(values):
                cell = QTableWidgetItem(text)
                cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                if item.blocking and item.status == "MISSING":
                    cell.setBackground(QColor("#f8d7da"))
                elif item.status in {"MANUFACTURER_CONFIRMATION_REQUIRED", "ENGINEERING_ASSUMPTION"}:
                    cell.setBackground(QColor("#fff3cd"))
                self.completion_table.setItem(row, col, cell)
        self.completion_table.resizeColumnsToContents()
        self.completion_table.horizontalHeader().setStretchLastSection(True)

        summary = evaluate_application_iteration_gates(temp)
        self.gate_summary.setText(f"Ön iterasyon durumu: {summary.status}")
        self.gate_text.setPlainText("\n".join(summary.trace))

    def _apply_conflict_decisions(self) -> None:
        records = {item.record_id: item for item in self.project.source_audit.records}
        for conflict in self.project.source_audit.conflicts:
            combo = self.conflict_combos[conflict.conflict_id]
            action, selected, default_value, default_unit = combo.currentData()
            if action == CONFLICT_UNRESOLVED:
                continue
            value = default_value
            unit = default_unit
            if action == CONFLICT_USE_USER_VALUE:
                spin = QDoubleSpinBox(self)
                spin.setDecimals(8)
                spin.setRange(-1e9, 1e9)
                if conflict.record_ids and records.get(conflict.record_ids[0]):
                    record = records[conflict.record_ids[0]]
                    if isinstance(record.value, (int, float)):
                        spin.setValue(float(record.value))
                    unit = record.unit
                box = QDialog(self)
                box.setWindowTitle(conflict.title)
                form = QFormLayout(box)
                form.addRow("Doğrulanmış değer", spin)
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(box.accept)
                buttons.rejected.connect(box.reject)
                form.addRow(buttons)
                if box.exec() != QDialog.Accepted:
                    raise ProjectCableApplicationError(f"{conflict.conflict_id} kullanıcı değeri girişi iptal edildi.")
                value = spin.value()
            resolve_source_conflict(
                self.project,
                conflict.conflict_id,
                action,
                selected,
                value,
                unit,
                rationale="v0.15.1 proje uygulama sihirbazı kararı",
                decided_by="Kullanıcı",
            )

    def _apply(self) -> None:
        if not self._selected_sections():
            QMessageBox.warning(self, "Güzergâh ataması", "En az bir güzergâh bölümü seçilmelidir.")
            return
        try:
            self._apply_conflict_decisions()
            result = apply_catalog_candidate_to_project(
                self.project,
                self.record_id,
                self.candidate_id,
                self.parallel,
                self._selected_sections(),
            )
            gates = evaluate_application_iteration_gates(self.project)
        except Exception as exc:
            QMessageBox.critical(self, "Kablo projeye uygulanamadı", str(exc))
            return
        self.applied = True
        if self.on_applied:
            self.on_applied()
        self.gate_summary.setText(f"Uygulama sonrası iterasyon durumu: {gates.status}")
        self.gate_text.setPlainText("\n".join(gates.trace))
        QMessageBox.information(
            self,
            "Kablo projeye uygulandı",
            f"Atanan güzergâh bölümü: {len(result.assigned_route_sections)}\n"
            f"Veri durumu: {result.completion.status}\n"
            f"İterasyon kapısı: {gates.status}",
        )
