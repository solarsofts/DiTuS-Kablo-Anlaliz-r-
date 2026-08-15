from __future__ import annotations

from copy import deepcopy
from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ucd.calculations.cable_library import merge_builtin_catalogs, merge_catalog_library
from ucd.models.project import CableCatalogRecord, CableLibraryData, ProjectData
from ucd.ui.cable_application_dialog import CableApplicationDialog
from .window_layout import fit_window, DENSITY_NORMAL


class ProjectCableSelectionDialog(QDialog):
    """Focused project cable choice; not a database administration screen."""

    def __init__(
        self,
        project: ProjectData,
        catalog_library: CableLibraryData | None = None,
        on_applied: Callable[[], None] | None = None,
        open_database: Callable[[], None] | None = None,
        define_project_cable: Callable[[], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.project = project
        self.catalog_library = catalog_library or project.cable_library
        self.on_applied = on_applied
        self.open_database = open_database
        self.define_project_cable = define_project_cable
        self.filtered: list[CableCatalogRecord] = []
        merge_builtin_catalogs(self.catalog_library)
        self.setWindowTitle("Proje Kablosu Seç")
        fit_window(self, DENSITY_NORMAL)
        self._build_ui()
        self._refresh_filters()
        self._refresh_table()
        self._refresh_assignment_state()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Proje Kablosu Seç")
        title.setStyleSheet("font-size:15pt; font-weight:800; color:#173d5d;")
        layout.addWidget(title)
        info = QLabel(
            "Bu ekran yalnız aktif projeye kablo seçmek ve atamak içindir. "
            "Katalog ekleme/düzenleme işlemleri Veri Tabanları → Kablolar menüsündedir."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background:#eaf0f5; padding:8px; border-radius:4px;")
        layout.addWidget(info)

        filters = QGroupBox("Hazır ürünleri filtrele")
        form = QFormLayout(filters)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Üretici, seri, model veya kayıt ID")
        self.manufacturer = QComboBox()
        self.voltage = QComboBox()
        self.material = QComboBox()
        self.material.addItems(["Tümü", "Cu", "Al"])
        self.minimum_area = QDoubleSpinBox()
        self.minimum_area.setRange(0, 10000)
        self.minimum_area.setSuffix(" mm²")
        self.parallel = QSpinBox()
        self.parallel.setRange(1, 12)
        self.parallel.setValue(max(1, self.project.cable.parallel_cables_per_phase))
        form.addRow("Ara", self.search)
        form.addRow("Üretici", self.manufacturer)
        form.addRow("Gerilim sınıfı", self.voltage)
        form.addRow("İletken", self.material)
        form.addRow("Minimum kesit", self.minimum_area)
        form.addRow("Kablo / faz", self.parallel)
        for widget in (self.search, self.manufacturer, self.voltage, self.material, self.minimum_area):
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self._refresh_table)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self._refresh_table)
            else:
                widget.valueChanged.connect(self._refresh_table)
        layout.addWidget(filters)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Seçim", "Üretici", "Seri / model", "Gerilim", "İletken", "Kesit", "Veri durumu", "Kayıt"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.itemDoubleClicked.connect(lambda *_: self._assign_selected())
        layout.addWidget(self.table, 1)

        self.selected_summary = QLabel("Bir ürün seçin.")
        self.selected_summary.setWordWrap(True)
        self.selected_summary.setStyleSheet(
            "font-weight:700; padding:9px; background:#fff8df; border:1px solid #d8bd58; border-radius:4px;"
        )
        layout.addWidget(self.selected_summary)
        self.assignment_state = QLabel()
        self.assignment_state.setWordWrap(True)
        self.assignment_state.setStyleSheet("padding:8px; background:#f7f9fb; border:1px solid #ccd7e1;")
        layout.addWidget(self.assignment_state)

        actions = QHBoxLayout()
        database = QPushButton("Veri Tabanındaki Kabloları Yönet")
        database.clicked.connect(self._open_database)
        manual = QPushButton("Bu Proje İçin Yeni Kablo Tanımla")
        manual.clicked.connect(self._define_project_cable)
        assign = QPushButton("Seçili Kabloyu Projeye Ata")
        assign.setStyleSheet("background:#2d6f9f; color:white; font-weight:750; padding:8px 14px;")
        assign.clicked.connect(self._assign_selected)
        close = QPushButton("Kapat")
        close.clicked.connect(self.close)
        actions.addWidget(database)
        actions.addWidget(manual)
        actions.addStretch(1)
        actions.addWidget(assign)
        actions.addWidget(close)
        layout.addLayout(actions)

    def _refresh_filters(self) -> None:
        manufacturers = sorted({r.manufacturer for r in self.catalog_library.records if r.manufacturer})
        voltages = sorted({r.voltage_class for r in self.catalog_library.records if r.voltage_class})
        self.manufacturer.clear()
        self.manufacturer.addItems(["Tümü", *manufacturers])
        self.voltage.clear()
        self.voltage.addItems(["Tümü", *voltages])

    def _refresh_table(self) -> None:
        query = self.search.text().strip().lower()
        manufacturer = self.manufacturer.currentText()
        voltage = self.voltage.currentText()
        material = self.material.currentText()
        area = self.minimum_area.value()
        rows: list[CableCatalogRecord] = []
        for record in self.catalog_library.records:
            haystack = " ".join((record.record_id, record.manufacturer, record.series, record.model, record.voltage_class)).lower()
            if query and query not in haystack:
                continue
            if manufacturer not in {"", "Tümü"} and record.manufacturer != manufacturer:
                continue
            if voltage not in {"", "Tümü"} and record.voltage_class != voltage:
                continue
            if material != "Tümü" and record.conductor_material.upper() != material.upper():
                continue
            if record.conductor_area_mm2 < area:
                continue
            rows.append(record)
        self.filtered = rows
        self.table.setRowCount(len(rows))
        assigned = self.project.cable_application.selected_catalog_record_id or self.project.cable.catalog_record_id
        assigned_row = -1
        for row, record in enumerate(rows):
            selected_mark = "✓ ATANMIŞ" if record.record_id == assigned else ""
            if record.record_id == assigned:
                assigned_row = row
            values = [
                selected_mark,
                record.manufacturer,
                " / ".join(x for x in (record.series, record.model) if x),
                record.voltage_class,
                record.conductor_material,
                f"{record.conductor_area_mm2:g} mm²",
                record.status,
                record.record_id,
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if record.record_id == assigned:
                    cell.setBackground(QColor("#e8f7ed"))
                self.table.setItem(row, col, cell)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        if assigned_row >= 0 and self.table.currentRow() < 0:
            self.table.selectRow(assigned_row)

    def _selected(self) -> CableCatalogRecord | None:
        row = self.table.currentRow()
        return self.filtered[row] if 0 <= row < len(self.filtered) else None

    def _selection_changed(self) -> None:
        record = self._selected()
        self._update_selection_marks()
        if record is None:
            self.selected_summary.setText("Bir ürün seçin.")
            return
        assigned_id = self.project.cable_application.selected_catalog_record_id or self.project.cable.catalog_record_id
        status = "bu kayıt projeye atanmış" if record.record_id == assigned_id else "projeye henüz atanmadı"
        self.selected_summary.setText(
            f"SEÇİLİ KABLO — {status}\n"
            f"{record.manufacturer} {record.series} {record.model} · {record.voltage_class} · "
            f"1×{record.conductor_area_mm2:g} {record.conductor_material} · {self.parallel.value()} kablo/faz"
        )

    def _update_selection_marks(self) -> None:
        selected = self._selected()
        selected_id = selected.record_id if selected else ""
        assigned_id = self.project.cable_application.selected_catalog_record_id or self.project.cable.catalog_record_id
        for row, record in enumerate(self.filtered):
            if record.record_id == selected_id and record.record_id == assigned_id:
                mark = "✓ SEÇİLİ / ATANMIŞ"
            elif record.record_id == selected_id:
                mark = "▶ SEÇİLİ"
            elif record.record_id == assigned_id:
                mark = "✓ ATANMIŞ"
            else:
                mark = ""
            item = self.table.item(row, 0)
            if item is not None:
                item.setText(mark)

    def _refresh_assignment_state(self) -> None:
        app = self.project.cable_application
        assigned = bool(app.applied_snapshot_hash or self.project.cable.snapshot_hash)
        if assigned:
            routes = [item.route_section_name for item in app.assignments if item.active]
            owner = self.window().parent() if self.window() is not self else self.parent()
            saved = "Proje dosyası henüz kaydedilmedi" if getattr(owner, "dirty", False) else "Kaydedildi"
            self.assignment_state.setText(
                "PROJE DURUMU\n"
                f"✓ Projeye atanmış kablo: {self.project.cable.name}\n"
                f"✓ Atanan güzergâh: {', '.join(routes) or 'Proje güzergâhı'}\n"
                f"• {saved}"
            )
        else:
            self.assignment_state.setText(
                "PROJE DURUMU\n✕ Projeye atanmış kablo yok\n• Ürün seçimi projeyi değiştirmez; atama için açık onay gerekir."
            )

    def _assign_selected(self) -> None:
        record = self._selected()
        if record is None:
            QMessageBox.information(self, "Kablo seçimi", "Önce tablodan bir kablo seçin.")
            return
        if not self.project.route_sections:
            QMessageBox.warning(self, "Güzergâh gerekli", "Kablo atanmadan önce en az bir güzergâh bölümü tanımlayın.")
            return
        # Copy only the selected reusable database record and its sources into
        # the active project. Calculations then use the project's fixed copy.
        source_ids = set(record.source_ids)
        incoming = CableLibraryData(
            records=[deepcopy(record)],
            sources=[
                deepcopy(source)
                for source in self.catalog_library.sources
                if source.source_id in source_ids
            ],
            package_name="Projeye aktarılan kablo kaydı",
            package_source="APPLICATION_DATABASE_COPY",
        )
        merge_catalog_library(self.project.cable_library, incoming, replace=True)
        candidate_id = f"{record.record_id}::P{self.parallel.value()}"
        dialog = CableApplicationDialog(
            self.project,
            record.record_id,
            candidate_id,
            self.parallel.value(),
            on_applied=self._application_completed,
            parent=self,
        )
        dialog.exec()

    def _application_completed(self) -> None:
        if self.on_applied:
            self.on_applied()
        self._refresh_table()
        self._refresh_assignment_state()
        self.selected_summary.setText(
            f"✓ KABLO PROJEYE ATANDI\n{self.project.cable.name}\n"
            "Bağlı hesaplar yeniden hesaplanacak olarak işaretlendi. Proje dosyasını Kaydet komutuyla kaydedin."
        )

    def _open_database(self) -> None:
        if self.open_database:
            callback = self.open_database
            self.reject()
            QTimer.singleShot(0, callback)
        else:
            QMessageBox.information(self, "Veri Tabanları", "Veri Tabanları → Kablolar menüsünü kullanın.")

    def _define_project_cable(self) -> None:
        if self.define_project_cable:
            callback = self.define_project_cable
            self.reject()
            QTimer.singleShot(0, callback)
            return
        QMessageBox.information(
            self,
            "Proje kablosu tanımı",
            "Proje Kablo Editörü açılarak yalnız bu projede kullanılacak kablo tanımlanmalıdır.",
        )
