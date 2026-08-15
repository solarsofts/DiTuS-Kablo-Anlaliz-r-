from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ucd.calculations.cable_physical_parameters import (
    PhysicalCableParameterResult,
    render_physical_parameter_result,
    run_project_physical_parameter_study,
)
from ucd.models.project import ProjectData
from .window_layout import fit_window, DENSITY_WIDE


class CablePhysicalParametersDialog(QDialog):
    """v0.16.4 shadow comparison UI.

    Construction metadata can be completed here.  The physical result is stored
    as a shadow study only and cannot replace the locked IEC 60287 scalar path.
    """

    def __init__(
        self,
        project: ProjectData,
        on_changed: Callable[[], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.project = project
        self.on_changed = on_changed
        self.last_result: PhysicalCableParameterResult | None = None

        self.setWindowTitle("DiTuS — Kablo Fiziksel Parametre Motoru v0.16.6")
        fit_window(self, DENSITY_WIDE)

        root = QVBoxLayout(self)
        title = QLabel("IEC tabanlı fiziksel parametre hesabı — SHADOW_COMPARE")
        title.setStyleSheet("font-size:14pt; font-weight:800; color:#173d5d; padding:4px;")
        root.addWidget(title)

        info = QLabel(
            "Bu sürüm Rdc, ks/kp, skin/proximity, Rac, kapasitans, dielektrik kayıp, "
            "kılıf direnci, GMR ve T1–T3 için fiziksel alternatif üretir. Sonuçlar kilitli "
            "v0.16.3.1 IEC/bonding/termal solver girdilerini değiştirmez. Eksik iletken yapısı "
            "uydurulmaz; hesap açıkça bloke edilir."
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding:8px; background:#eef4f8; border:1px solid #c9d7e2;")
        root.addWidget(info)

        controls_box = QGroupBox("Hesap kapsamı ve iletken yapısı")
        controls = QFormLayout(controls_box)
        self.section_combo = QComboBox()
        self.section_combo.addItems([section.name for section in self.project.route_sections])
        selected = self.project.physical_parameter_study.selected_route_section_name
        if selected:
            self.section_combo.setCurrentText(selected)
        controls.addRow("Güzergâh bölümü", self.section_combo)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(20.0, 250.0)
        self.temperature_spin.setDecimals(2)
        self.temperature_spin.setSuffix(" °C")
        self.temperature_spin.setValue(
            self.project.physical_parameter_study.target_temperature_c
            or self.project.cable.max_temperature_c
        )
        controls.addRow("Hedef iletken sıcaklığı", self.temperature_spin)

        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["ROUND", "SECTOR", "HOLLOW", "OTHER"])
        self.shape_combo.setCurrentText(self.project.cable.conductor_shape)
        controls.addRow("İletken şekli", self.shape_combo)

        self.stranding_combo = QComboBox()
        self.stranding_combo.addItems([
            "SOLID", "COMPACTED_STRANDED", "MILLIKEN", "SEGMENTAL", "OTHER", "UNKNOWN"
        ])
        self.stranding_combo.setCurrentText(self.project.cable.conductor_stranding_type)
        controls.addRow("İletken yapısı", self.stranding_combo)

        self.insulation_combo = QComboBox()
        self.insulation_combo.addItems(["EXTRUDED", "FLUID_PAPER_PPL", "MINERAL", "OTHER", "UNKNOWN"])
        self.insulation_combo.setCurrentText(self.project.cable.conductor_insulation_system)
        controls.addRow("İzolasyon sistemi sınıfı", self.insulation_combo)

        self.milliken_combo = QComboBox()
        self.milliken_combo.addItems([
            "UNKNOWN", "INSULATED_WIRES", "BARE_UNIDIRECTIONAL",
            "BARE_BIDIRECTIONAL", "FLUID_PAPER_PPL"
        ])
        self.milliken_combo.setCurrentText(self.project.cable.milliken_wire_profile)
        controls.addRow("Cu Milliken tel profili", self.milliken_combo)

        coefficient_widget = QWidget()
        coefficient_layout = QHBoxLayout(coefficient_widget)
        coefficient_layout.setContentsMargins(0, 0, 0, 0)
        self.ks_spin = QDoubleSpinBox()
        self.ks_spin.setRange(0.0, 10.0)
        self.ks_spin.setDecimals(6)
        self.ks_spin.setValue(self.project.cable.skin_effect_coefficient_ks)
        self.ks_spin.setToolTip("0 = IEC yapı tablosundan otomatik çöz")
        self.kp_spin = QDoubleSpinBox()
        self.kp_spin.setRange(0.0, 10.0)
        self.kp_spin.setDecimals(6)
        self.kp_spin.setValue(self.project.cable.proximity_effect_coefficient_kp)
        self.kp_spin.setToolTip("0 = IEC yapı tablosundan otomatik çöz")
        coefficient_layout.addWidget(QLabel("ks"))
        coefficient_layout.addWidget(self.ks_spin)
        coefficient_layout.addSpacing(12)
        coefficient_layout.addWidget(QLabel("kp"))
        coefficient_layout.addWidget(self.kp_spin)
        controls.addRow("Açık katsayı çifti (0=otomatik)", coefficient_widget)
        root.addWidget(controls_box)

        action_row = QHBoxLayout()
        self.run_button = QPushButton("Fiziksel Shadow Hesabını Çalıştır")
        self.run_button.clicked.connect(self._run)
        action_row.addWidget(self.run_button)
        action_row.addStretch(1)
        self.status_label = QLabel("Henüz çalıştırılmadı")
        self.status_label.setStyleSheet("font-weight:700; padding:5px;")
        action_row.addWidget(self.status_label)
        root.addLayout(action_row)

        splitter = QSplitter(Qt.Horizontal)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Parametre", "Kilitli/sertifikalı girdi", "Fiziksel shadow", "Birim", "Fark", "Kaynak/statü"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self.table)

        self.trace_text = QTextEdit()
        self.trace_text.setReadOnly(True)
        self.trace_text.setPlaceholderText("Hesap izi ve kapsam uyarıları burada gösterilir.")
        splitter.addWidget(self.trace_text)
        splitter.setSizes([860, 540])
        root.addWidget(splitter, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText("Kapat")
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        if self.project.physical_parameter_study.last_result:
            self.trace_text.setPlainText(
                "Önceki shadow sonucu proje içinde kayıtlıdır. Güncel kablo/geometri için hesabı yeniden çalıştırın."
            )

    @staticmethod
    def _item(value: str) -> QTableWidgetItem:
        return QTableWidgetItem(value)

    def _commit_inputs(self) -> None:
        cable = self.project.cable
        cable.conductor_shape = self.shape_combo.currentText()
        cable.conductor_stranding_type = self.stranding_combo.currentText()
        cable.conductor_insulation_system = self.insulation_combo.currentText()
        cable.milliken_wire_profile = self.milliken_combo.currentText()
        cable.skin_effect_coefficient_ks = self.ks_spin.value()
        cable.proximity_effect_coefficient_kp = self.kp_spin.value()
        study = self.project.physical_parameter_study
        study.selected_route_section_name = self.section_combo.currentText()
        study.target_temperature_c = self.temperature_spin.value()

    def _run(self) -> None:
        self._commit_inputs()
        try:
            result = run_project_physical_parameter_study(
                self.project,
                section_name=self.section_combo.currentText(),
                target_temperature_c=self.temperature_spin.value(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Fiziksel parametre hesabı tamamlanamadı", str(exc))
            return
        self.last_result = result
        self._populate_result(result)
        if self.on_changed is not None:
            self.on_changed()

    def _populate_result(self, result: PhysicalCableParameterResult) -> None:
        def number(value: float, digits: int = 8) -> str:
            return f"{value:.{digits}f}"

        rows = [
            ("Rdc20", number(result.rdc20_input_ohm_km, 9), number(result.rdc20_geometry_ohm_km, 9), "Ω/km",
             number(100.0 * (result.rdc20_geometry_ohm_km - result.rdc20_input_ohm_km) / result.rdc20_input_ohm_km, 3) + "%" if result.rdc20_input_ohm_km > 0 else "—", result.rdc20_basis_source),
            ("α20", number(result.alpha_used_per_c, 6), number(result.material_alpha_reference_per_c, 6), "1/°C", "—", "Girdi / malzeme referansı"),
            ("ks", "0=otomatik veya açık girdi", number(result.ks, 6), "-", "—", result.coefficient_source),
            ("kp", "0=otomatik veya açık girdi", number(result.kp, 6), "-", "—", result.coefficient_source),
            ("Skin faktörü ys", number(result.legacy_skin_effect_factor_ys, 8), number(result.skin_effect_factor_ys, 8), "-", "—", "Legacy / IEC shadow"),
            ("Proximity faktörü yp", number(result.legacy_proximity_effect_factor_yp, 8), number(result.proximity_effect_factor_yp, 8), "-", "—", "Legacy / IEC shadow"),
            ("Rac", number(result.legacy_ac_resistance_ohm_km, 9), number(result.physical_ac_resistance_ohm_km, 9), "Ω/km", f"{result.ac_resistance_difference_percent:+.3f}%", "Legacy / fiziksel shadow"),
            ("Kapasitans", number(result.capacitance_input_uf_km, 6), number(result.capacitance_geometry_uf_km, 6), "µF/km", f"{result.capacitance_difference_percent:+.3f}%", "Üretici/proje / geometri"),
            ("Dielektrik kayıp Wd", number(result.dielectric_loss_input_w_m, 6), number(result.dielectric_loss_geometry_w_m, 6), "W/m", "—", "Aynı tanδ, farklı C"),
            ("Kılıf Rdc20", number(result.sheath_resistance_input_ohm_km, 9), number(result.sheath_resistance_geometry_ohm_km, 9), "Ω/km", "—", result.sheath_resistance_basis_source),
            ("İletken GMR", number(self.project.cable.conductor_gmr_mm, 6), number(result.conductor_gmr_mm, 6), "mm", "—", "Girdi / eşdeğer yaklaşım"),
            ("T1", number(self.project.cable.thermal_resistance_t1_km_w, 6), number(result.t1_km_w, 6), "K·m/W", "—", "Legacy alan / fiziksel katman"),
            ("T2", number(self.project.cable.thermal_resistance_t2_km_w, 6), number(result.t2_km_w, 6), "K·m/W", "—", "Legacy alan / fiziksel katman"),
            ("T3", number(self.project.cable.thermal_resistance_t3_km_w, 6), number(result.t3_km_w, 6), "K·m/W", "—", "Legacy alan / fiziksel katman"),
        ]
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row, column, self._item(str(value)))
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, 210)
        self.table.setColumnWidth(1, 190)
        self.table.setColumnWidth(2, 190)
        self.table.setColumnWidth(5, 270)

        state = "HAZIR" if result.final_design_ready else "KOŞULLU/BLOKE"
        self.status_label.setText(
            f"AC kapsamı: {'AÇIK' if result.supported_for_ac_resistance else 'BLOKE'} | "
            f"Hata: {result.error_count} | Uyarı: {result.warning_count} | Fiziksel kapı: {state}"
        )
        self.status_label.setStyleSheet(
            "font-weight:800; padding:5px; color:#176b39;" if result.final_design_ready
            else "font-weight:800; padding:5px; color:#9a4b00;"
        )
        self.trace_text.setPlainText(render_physical_parameter_result(result))
