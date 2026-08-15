from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
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

from ucd.calculations.thermal_material_library import (
    LIBRARY_REVISION,
    REFERENCE_SCOPE,
    built_in_reference_materials,
)
from ucd.models.project import ProjectData
from .window_layout import fit_window, DENSITY_WIDE


class ThermalMaterialLibraryDialog(QDialog):
    """Read-only built-in catalogue with explicit copy-to-project action."""

    def __init__(self, project: ProjectData, on_change=None, parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self.on_change = on_change
        self.records = built_in_reference_materials()
        self.setWindowTitle(f"DiTuS — Termal Malzeme Referans Kütüphanesi · {LIBRARY_REVISION}")
        fit_window(self, DENSITY_WIDE)
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel(
            "Bu kütüphane ön tasarım ve veri toplama içindir. Sağlam kaya değeri kırmataş dolguya doğrudan "
            "aktarılmaz; rating'i belirleyen zemin/backfill proje koşulunda ölçülmelidir."
        )
        title.setWordWrap(True)
        title.setStyleSheet(
            "font-size:11pt; font-weight:700; color:#173d5d; padding:8px; "
            "background:#edf4f8; border:1px solid #c7d5df; border-radius:5px;"
        )
        root.addWidget(title)
        scope = QLabel(REFERENCE_SCOPE)
        scope.setWordWrap(True)
        scope.setStyleSheet("font-size:8pt; color:#5c6d78; font-style:italic;")
        root.addWidget(scope)

        headers = [
            "Malzeme ID", "Ad", "Kategori", "k [W/mK]", "k min", "k max",
            "ρ [K·m/W]", "Nem durumu", "Test yöntemi", "Güvenilirlik",
            "Proje testi", "Kaynak", "Not",
        ]
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        row = QHBoxLayout()
        add_selected = QPushButton("Seçili Kayıtları Projeye Kopyala")
        add_all = QPushButton("Eksik Kayıtların Tümünü Projeye Ekle")
        add_selected.clicked.connect(self._add_selected)
        add_all.clicked.connect(self._add_all)
        row.addWidget(add_selected)
        row.addWidget(add_all)
        row.addStretch(1)
        root.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @staticmethod
    def _item(value) -> QTableWidgetItem:
        item = QTableWidgetItem(str(value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _populate(self) -> None:
        self.table.setRowCount(len(self.records))
        for row, material in enumerate(self.records):
            values = [
                material.material_id,
                material.name,
                material.category,
                f"{material.thermal_conductivity_w_mk:.3f}",
                f"{material.reference_conductivity_min_w_mk:.3f}",
                f"{material.reference_conductivity_max_w_mk:.3f}",
                f"{material.thermal_resistivity_km_w:.3f}",
                material.moisture_condition,
                material.test_method,
                material.reliability,
                "EVET" if material.requires_project_test else "HAYIR",
                material.source_reference,
                material.notes,
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, self._item(value))
        self.table.resizeColumnsToContents()

    def _copy_rows(self, rows: list[int]) -> None:
        existing = {item.material_id for item in self.project.thermal_design.materials}
        added = 0
        skipped = 0
        for row in rows:
            if not 0 <= row < len(self.records):
                continue
            record = self.records[row]
            if record.material_id in existing:
                skipped += 1
                continue
            self.project.thermal_design.materials.append(deepcopy(record))
            existing.add(record.material_id)
            added += 1
        if added and self.on_change is not None:
            self.on_change()
        QMessageBox.information(
            self,
            "Termal malzeme kütüphanesi",
            f"{added} kayıt projeye eklendi; {skipped} mevcut kayıt atlandı.",
        )

    def _add_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        if not rows:
            QMessageBox.information(self, "Termal malzeme", "Önce bir veya daha fazla satır seçin.")
            return
        self._copy_rows(rows)

    def _add_all(self) -> None:
        self._copy_rows(list(range(len(self.records))))
