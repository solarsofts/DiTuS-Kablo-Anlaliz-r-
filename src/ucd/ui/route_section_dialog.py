from __future__ import annotations

from copy import deepcopy

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ucd.models.project import RouteSection
from .window_layout import fit_window, DENSITY_COMPACT


SOURCE_PREFIX = "Veri kaynağı:"

INSTALLATION_TYPE_TR = {
    "DIRECT_BURIED": "doğrudan gömülü",
    "DUCT_BANK": "boru / kanal bankası",
    "CONCRETE_CHANNEL": "beton kablo kanalı",
    "TUNNEL": "kablo tüneli",
    "HDD": "yatay yönlendirilmiş sondaj",
    "OTHER": "diğer / özel kurulum",
}


class RouteSectionDialog(QDialog):
    """Short form for creating or editing one project route section."""

    def __init__(self, section: RouteSection | None = None, parent=None) -> None:
        super().__init__(parent)
        self.original = deepcopy(section) if section is not None else RouteSection("Yeni bölüm", 100.0)
        self.result_section: RouteSection | None = None
        self.setWindowTitle("Güzergâh Bölümü")
        fit_window(self, DENSITY_COMPACT)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(self.original.name)
        self.length = QDoubleSpinBox()
        self.length.setRange(0.01, 1_000_000.0)
        self.length.setDecimals(2)
        self.length.setSuffix(" m")
        self.length.setValue(max(0.01, self.original.length_m))
        self.section_type = QComboBox()
        self.section_type.addItems(["DIRECT_BURIED", "DUCT_BANK", "CONCRETE_CHANNEL", "TUNNEL", "HDD", "OTHER"])
        self.section_type.setCurrentText(self.original.section_type)
        self.section_type_caption = QLabel()
        self.section_type_caption.setStyleSheet("font-size:8pt; font-style:italic; color:#60727f;")
        section_type_widget = QWidget()
        section_type_layout = QVBoxLayout(section_type_widget)
        section_type_layout.setContentsMargins(0, 0, 0, 0)
        section_type_layout.setSpacing(2)
        section_type_layout.addWidget(self.section_type)
        section_type_layout.addWidget(self.section_type_caption)
        self.section_type.currentTextChanged.connect(self._update_installation_type_caption)
        self._update_installation_type_caption(self.section_type.currentText())
        self.depth = QDoubleSpinBox()
        self.depth.setRange(0.0, 100.0)
        self.depth.setDecimals(3)
        self.depth.setSuffix(" m")
        self.depth.setValue(self.original.burial_depth_m)
        self.soil = QDoubleSpinBox()
        self.soil.setRange(0.01, 20.0)
        self.soil.setDecimals(3)
        self.soil.setSuffix(" K·m/W")
        self.soil.setValue(self.original.soil_thermal_resistivity_km_w)
        self.cross_section = QLineEdit(self.original.cross_section_id)
        self.ambient = QDoubleSpinBox()
        self.ambient.setRange(-50.0, 100.0)
        self.ambient.setDecimals(1)
        self.ambient.setSuffix(" °C")
        self.ambient.setValue(self.original.ambient_temperature_c)
        self.phase_spacing = QDoubleSpinBox()
        self.phase_spacing.setRange(0.0, 20.0)
        self.phase_spacing.setDecimals(3)
        self.phase_spacing.setSuffix(" m")
        self.phase_spacing.setValue(self.original.phase_spacing_m)
        self.source = QComboBox()
        self.source.addItems(["Ölçülmüş", "Şartname", "Kaynak doküman", "Ön tasarım kabulü", "Bilinmiyor"])
        note_lines = []
        detected_source = "Bilinmiyor"
        for line in self.original.notes.splitlines():
            if line.strip().startswith(SOURCE_PREFIX):
                detected_source = line.split(":", 1)[1].strip() or detected_source
            else:
                note_lines.append(line)
        self.source.setCurrentText(detected_source)
        self.notes = QPlainTextEdit("\n".join(note_lines).strip())
        self.notes.setMaximumHeight(100)

        form.addRow("Bölüm adı", self.name)
        form.addRow("Uzunluk", self.length)
        form.addRow("Kurulum tipi", section_type_widget)
        form.addRow("Gömme derinliği", self.depth)
        form.addRow("Toprak ısıl özdirenci", self.soil)
        form.addRow("Kesit şablonu", self.cross_section)
        form.addRow("Ortam sıcaklığı", self.ambient)
        form.addRow("Faz aralığı", self.phase_spacing)
        form.addRow("Veri kaynağı", self.source)
        form.addRow("Not", self.notes)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Bölümü Kaydet")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_installation_type_caption(self, installation_type: str) -> None:
        self.section_type_caption.setText(INSTALLATION_TYPE_TR.get(installation_type, "özel kurulum"))

    def _accept(self) -> None:
        section = deepcopy(self.original)
        section.name = self.name.text().strip() or "Güzergâh bölümü"
        section.length_m = self.length.value()
        section.section_type = self.section_type.currentText()
        section.burial_depth_m = self.depth.value()
        section.soil_thermal_resistivity_km_w = self.soil.value()
        section.cross_section_id = self.cross_section.text().strip()
        section.ambient_temperature_c = self.ambient.value()
        section.phase_spacing_m = self.phase_spacing.value()
        note = self.notes.toPlainText().strip()
        source_note = f"{SOURCE_PREFIX} {self.source.currentText()}"
        section.notes = f"{note}\n{source_note}".strip()
        self.result_section = section
        self.accept()
