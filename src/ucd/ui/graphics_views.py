from __future__ import annotations

from ucd.calculations.result_status import display_foreground

import math
from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsTextItem,
    QGraphicsView,
)

from ucd.cad.dxf_reader import DxfGeometry
from ucd.calculations.bonding import BondingInputError, resolve_major_paths
from ucd.calculations.thermal_review import (
    extract_material_boundary_segments,
    extract_quantized_isotherm_segments,
)


class ZoomPanGraphicsView(QGraphicsView):
    """Common engineering-canvas zoom contract.

    ``FIT`` means the whole declared engineering composition is visible.  A
    wheel zoom switches the view to ``MANUAL`` and viewport resize events must
    then preserve the user's transform.  Zoom-out is clamped at the current
    fit-to-content scale, so an engineering drawing can never be shrunk into an
    unreadable postage stamp.
    """

    ZOOM_STEP = 1.10
    MAX_ZOOM_OVER_FIT = 16.0

    def __init__(self, scene: QGraphicsScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._zoom_fit_bounds: QRectF | None = None
        self._zoom_fit_scale: float | None = None
        self._zoom_view_mode = "MANUAL"
        self._zoom_applying_fit = False

    def set_fit_bounds(self, bounds: QRectF, *, fit_now: bool = True) -> None:
        if not bounds.isValid() or bounds.isEmpty():
            return
        self._zoom_fit_bounds = QRectF(bounds)
        if fit_now:
            self.fit_to_bounds()

    def fit_to_bounds(self) -> None:
        bounds = self._zoom_fit_bounds
        if bounds is None or not bounds.isValid() or bounds.isEmpty():
            return
        if self.viewport().width() <= 4 or self.viewport().height() <= 4:
            return
        self._zoom_applying_fit = True
        try:
            self.fitInView(bounds, Qt.KeepAspectRatio)
            self._zoom_fit_scale = max(abs(float(self.transform().m11())), 1e-12)
            self._zoom_view_mode = "FIT"
        finally:
            self._zoom_applying_fit = False

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        # Scrollbar appearance also resizes the viewport.  Only a view which is
        # still intentionally in FIT mode may react by fitting again.  A wheel
        # zoom sets MANUAL before the transform changes, so user zoom is never
        # cancelled by the resulting scrollbar resize.
        if self._zoom_view_mode == "FIT" and not self._zoom_applying_fit:
            self.fit_to_bounds()

    def wheelEvent(self, event) -> None:  # noqa: N802
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        current = max(abs(float(self.transform().m11())), 1e-12)
        factor = self.ZOOM_STEP if delta > 0 else 1.0 / self.ZOOM_STEP
        target = current * factor
        fit_scale = self._zoom_fit_scale

        if fit_scale is not None:
            if delta < 0 and target <= fit_scale * 1.001:
                self.fit_to_bounds()
                event.accept()
                return
            maximum = fit_scale * self.MAX_ZOOM_OVER_FIT
            if delta > 0 and current >= maximum * 0.999:
                event.accept()
                return
            if delta > 0 and target > maximum:
                factor = maximum / current

        # This assignment must happen before scale(): scrollbar creation can
        # synchronously emit a viewport resize event.
        self._zoom_view_mode = "MANUAL"
        self.scale(factor, factor)
        event.accept()


class PlanView(ZoomPanGraphicsView):
    def __init__(self, parent=None) -> None:
        self.scene_obj = QGraphicsScene()
        super().__init__(self.scene_obj, parent)
        # Route canvas defaults to normal selection. Pan is intentionally not
        # represented by a permanent hand cursor; users can zoom with the wheel
        # and explicit pan tooling will be added with the route designer.
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.ArrowCursor)
        self.setSceneRect(-100, -100, 1600, 900)
        self._draw_background_grid()
        self.draw_sample_route()

    def _draw_background_grid(self) -> None:
        minor = QPen(QColor("#edf1f5"), 0)
        major = QPen(QColor("#dce4eb"), 0)
        for x in range(-100, 1501, 25):
            self.scene_obj.addLine(x, -100, x, 800, major if x % 100 == 0 else minor)
        for y in range(-100, 801, 25):
            self.scene_obj.addLine(-100, y, 1500, y, major if y % 100 == 0 else minor)

    def clear_geometry(self) -> None:
        self.scene_obj.clear()
        self._draw_background_grid()

    def draw_sample_route(self) -> None:
        path = QPainterPath(QPointF(80, 170))
        path.lineTo(360, 170)
        path.cubicTo(480, 170, 480, 320, 610, 320)
        path.lineTo(930, 320)
        path.lineTo(1160, 500)
        item = QGraphicsPathItem(path)
        item.setPen(QPen(QColor("#2c6eaa"), 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.scene_obj.addItem(item)
        for point, label in [((80, 170), "Başlangıç"), ((610, 320), "JB-01"), ((930, 320), "LB-01"), ((1160, 500), "Bitiş")]:
            x, y = point
            node = self.scene_obj.addEllipse(x - 8, y - 8, 16, 16, QPen(QColor("#1d4f7c"), 2), QBrush(QColor("#ffffff")))
            node.setZValue(5)
            text = self.scene_obj.addSimpleText(label, QFont("Segoe UI", 9))
            text.setBrush(QColor("#263746"))
            text.setPos(x + 10, y - 18)
        note = self.scene_obj.addSimpleText("Örnek güzergâh — DXF içe aktarınca değiştirilir", QFont("Segoe UI", 10))
        note.setBrush(QColor("#6b7b88"))
        note.setPos(80, 90)
        self.set_fit_bounds(self.scene_obj.itemsBoundingRect().adjusted(-60, -60, 60, 60))

    def load_dxf(self, geometry: DxfGeometry) -> None:
        self.clear_geometry()
        layer_colors: dict[str, QColor] = {}
        palette = ["#2c6eaa", "#7f3c8d", "#e07a1f", "#3f8f5b", "#a33b3b", "#566573"]

        def color_for(layer: str) -> QColor:
            if layer not in layer_colors:
                layer_colors[layer] = QColor(palette[len(layer_colors) % len(palette)])
            return layer_colors[layer]

        for start, end, layer in geometry.lines:
            self.scene_obj.addLine(start[0], -start[1], end[0], -end[1], QPen(color_for(layer), 1.4))
        for points, closed, layer in geometry.polylines:
            path = QPainterPath(QPointF(points[0][0], -points[0][1]))
            for x, y in points[1:]:
                path.lineTo(x, -y)
            if closed:
                path.closeSubpath()
            item = self.scene_obj.addPath(path, QPen(color_for(layer), 1.6))
            item.setToolTip(f"Katman: {layer}")
        for center, radius, layer in geometry.circles:
            self.scene_obj.addEllipse(center[0] - radius, -center[1] - radius, radius * 2, radius * 2,
                                      QPen(color_for(layer), 1.2))
        for pos, text, layer in geometry.texts:
            item = self.scene_obj.addSimpleText(text, QFont("Segoe UI", 8))
            item.setBrush(color_for(layer))
            item.setPos(pos[0], -pos[1])
        bounds = self.scene_obj.itemsBoundingRect()
        if bounds.isValid() and not bounds.isEmpty():
            self.setSceneRect(bounds.adjusted(-100, -100, 100, 100))
            self.set_fit_bounds(bounds.adjusted(-40, -40, 40, 40))


class CableItem(QGraphicsEllipseItem):
    def __init__(self, phase: str, x: float, y: float, callback: Callable[[], None]) -> None:
        diameter = 48.0
        super().__init__(-diameter / 2, -diameter / 2, diameter, diameter)
        self.phase = phase
        self.callback = callback
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("#f8fafc")))
        self.setPen(QPen(QColor("#2c6eaa"), 3))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        label = QGraphicsSimpleTextItem(phase, self)
        label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        br = label.boundingRect()
        label.setPos(-br.width() / 2, -br.height() / 2)

    def itemChange(self, change, value):  # noqa: N802
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene() is not None:
            self.callback()
        return result


class CrossSectionView(ZoomPanGraphicsView):
    def __init__(self, on_change: Callable[[dict[str, tuple[float, float]]], None] | None = None, parent=None) -> None:
        self.scene_obj = QGraphicsScene()
        super().__init__(self.scene_obj, parent)
        self.on_change = on_change
        self.cables: dict[str, CableItem] = {}
        self.setSceneRect(0, 0, 900, 650)
        self._build_scene()
        self.set_fit_bounds(QRectF(0, 0, 900, 650))

    def _build_scene(self) -> None:
        sky = self.scene_obj.addRect(0, 0, 900, 100, QPen(Qt.NoPen), QBrush(QColor("#f7fbff")))
        soil = self.scene_obj.addRect(0, 100, 900, 550, QPen(Qt.NoPen), QBrush(QColor("#e8e1d6")))
        sky.setZValue(-10)
        soil.setZValue(-10)
        self.scene_obj.addLine(0, 100, 900, 100, QPen(QColor("#5f6f78"), 3))
        backfill = QGraphicsRectItem(250, 230, 400, 300)
        backfill.setBrush(QBrush(QColor("#d9c8aa")))
        backfill.setPen(QPen(QColor("#9a8260"), 2, Qt.DashLine))
        backfill.setZValue(-5)
        self.scene_obj.addItem(backfill)
        self.scene_obj.addSimpleText("Termal dolgu", QFont("Segoe UI", 10)).setPos(265, 245)
        self.scene_obj.addSimpleText("Zemin yüzeyi", QFont("Segoe UI", 10)).setPos(20, 70)
        positions = {"A": (410, 340), "B": (490, 340), "C": (450, 410)}
        for phase, pos in positions.items():
            item = CableItem(phase, *pos, self._emit_positions)
            self.cables[phase] = item
            self.scene_obj.addItem(item)
        hint = self.scene_obj.addSimpleText("Kabloları sürükleyerek kesit yerleşimini değiştirin", QFont("Segoe UI", 10))
        hint.setBrush(QColor("#526878"))
        hint.setPos(20, 610)
        self._draw_dimensions()

    def _draw_dimensions(self) -> None:
        a, b, c = (self.cables[k].pos() for k in ("A", "B", "C"))
        for p1, p2 in ((a, b), (b, c), (c, a)):
            self.scene_obj.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(QColor("#8fa1af"), 1, Qt.DotLine))

    def _emit_positions(self) -> None:
        if self.on_change:
            self.on_change({phase: (round(item.pos().x(), 1), round(item.pos().y(), 1)) for phase, item in self.cables.items()})


class SimpleDiagramView(ZoomPanGraphicsView):
    def __init__(self, diagram: str, parent=None) -> None:
        self.scene_obj = QGraphicsScene()
        super().__init__(self.scene_obj, parent)
        self.diagram = diagram
        self._last_bonding = None
        self._last_bonding_result = None
        self._highlight_loop_name = ""
        self._last_fit_bounds: QRectF | None = None
        self.setSceneRect(0, 0, 1100, 650)
        if diagram == "profile":
            self._draw_profile()
        elif diagram == "bonding":
            self._draw_bonding()
        elif diagram == "thermal":
            self._draw_empty_thermal()
        initial_bounds = self.scene_obj.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        self._last_fit_bounds = initial_bounds
        self.set_fit_bounds(initial_bounds)

    def fit_current_view(self) -> None:
        """Son çizimin görünür kompozisyonunu viewport'a yeniden sığdır."""
        if self._last_fit_bounds is not None and self._last_fit_bounds.isValid():
            self.set_fit_bounds(self._last_fit_bounds)

    def _draw_profile(self) -> None:
        self.scene_obj.addSimpleText("Boyuna profil ve hesap segmentleri", QFont("Segoe UI", 13, QFont.Bold)).setPos(40, 25)
        ground = QPainterPath(QPointF(40, 180))
        for x, y in [(220, 175), (360, 150), (540, 165), (720, 125), (930, 150), (1050, 145)]:
            ground.lineTo(x, y)
        self.scene_obj.addPath(ground, QPen(QColor("#596b78"), 3))
        cable = QPainterPath(QPointF(40, 330))
        for x, y in [(220, 325), (360, 310), (540, 330), (720, 315), (930, 340), (1050, 335)]:
            cable.lineTo(x, y)
        self.scene_obj.addPath(cable, QPen(QColor("#2c6eaa"), 5))
        for x, label in [(40, "0+000"), (360, "1+250"), (540, "1+390"), (720, "1+670"), (1050, "2+950")]:
            self.scene_obj.addLine(x, 120, x, 420, QPen(QColor("#c4ced7"), 1, Qt.DashLine))
            self.scene_obj.addSimpleText(label, QFont("Segoe UI", 9)).setPos(x - 20, 430)
        self.scene_obj.addSimpleText("Standart hendek", QFont("Segoe UI", 9)).setPos(120, 480)
        self.scene_obj.addSimpleText("Yol geçişi", QFont("Segoe UI", 9)).setPos(395, 480)
        self.scene_obj.addSimpleText("HDD", QFont("Segoe UI", 9)).setPos(600, 480)

    def _draw_bonding(self) -> None:
        self.scene_obj.addSimpleText("Cross-bonding ağı — proje verisi bekleniyor", QFont("Segoe UI", 13, QFont.Bold)).setPos(40, 25)
        self.scene_obj.addSimpleText("Bonding editöründeki düğüm ve minor section verileri burada çizilir.", QFont("Segoe UI", 10)).setPos(40, 90)

    def highlight_bonding_loop(self, loop_name: str = "") -> None:
        self._highlight_loop_name = loop_name or ""
        if self._last_bonding is not None:
            self.draw_bonding_system(self._last_bonding, self._last_bonding_result)

    @staticmethod
    def _connection_mapping(bonding, joint_node_id: str) -> dict[str, str]:
        link_by_joint = {box.joint_node_id: box for box in bonding.link_boxes}
        box = link_by_joint.get(joint_node_id)
        mapping: dict[str, str] = {}
        for connection in bonding.connections:
            same_joint = connection.node_id == joint_node_id
            same_box = box is not None and connection.link_box_id == box.link_box_id
            if connection.connection_type.upper() == "CROSS" and (same_joint or same_box):
                mapping[connection.from_sheath.upper()] = connection.to_sheath.upper()
        return mapping

    def draw_bonding_system(self, bonding, result=None) -> None:
        if self.diagram != "bonding":
            return
        self._last_bonding = bonding
        self._last_bonding_result = result
        self.scene_obj.clear()
        title = self.scene_obj.addSimpleText(
            f"{bonding.name} — {bonding.scheme}", QFont("Segoe UI", 13, QFont.Bold)
        )
        title.setPos(30, 10)

        nodes = sorted(bonding.nodes, key=lambda n: n.position_m)
        if len(nodes) < 2:
            self.scene_obj.addSimpleText("En az iki bonding düğümü gerekli.", QFont("Segoe UI", 11)).setPos(40, 80)
            return
        total = max(nodes[-1].position_m - nodes[0].position_m, 1.0)
        minor_count = max(len(bonding.minor_sections), 1)
        scene_width = max(1450.0, min(6200.0, 330.0 * minor_count + 260.0))
        left, right = 165.0, scene_width - 100.0
        x_by_id = {
            node.node_id: left + (right - left) * (node.position_m - nodes[0].position_m) / total
            for node in nodes
        }

        # Standing-voltage profile
        profile_top, profile_bottom = 55.0, 155.0
        self.scene_obj.addSimpleText("Metalik kılıf gerilim profili", QFont("Segoe UI", 9, QFont.Bold)).setPos(30, profile_top)
        self.scene_obj.addLine(left, profile_bottom, right, profile_bottom, QPen(QColor("#8b99a5"), 1))
        if result is not None and result.standing_voltage_profile:
            vmax_scale = max(result.voltage_limit_v, result.max_standing_voltage_v, 1.0)
            limit_y = profile_bottom - (result.voltage_limit_v / vmax_scale) * 78.0
            self.scene_obj.addLine(left, limit_y, right, limit_y, QPen(QColor("#c13f3f"), 2, Qt.DashLine))
            limit_text = self.scene_obj.addSimpleText(f"Limit {result.voltage_limit_v:.0f} V", QFont("Segoe UI", 8))
            limit_text.setBrush(QColor("#a52f2f"))
            limit_text.setPos(right - 75, limit_y - 18)
            voltage_path = QPainterPath()
            first = True
            for point in result.standing_voltage_profile:
                x = left + (right - left) * (point.chainage_m - nodes[0].position_m) / total
                y = profile_bottom - (point.voltage_v / vmax_scale) * 78.0
                if first:
                    voltage_path.moveTo(x, y)
                    first = False
                else:
                    voltage_path.lineTo(x, y)
            self.scene_obj.addPath(voltage_path, QPen(QColor("#e07a1f"), 3))
        else:
            note = self.scene_obj.addSimpleText("Hesaplanmadı", QFont("Segoe UI", 8))
            note.setBrush(QColor("#6b7b88"))
            note.setPos(left + 10, profile_top + 30)

        ys = {"A": 295.0, "B": 405.0, "C": 515.0}
        loop_colors = {"A": "#a43b3b", "B": "#c59b28", "C": "#2c6eaa"}
        for phase, y in ys.items():
            lane = QColor("#b9c4cc")
            self.scene_obj.addLine(left, y, right, y, QPen(lane, 1, Qt.DashLine))
            label = self.scene_obj.addSimpleText(f"Fiziksel metalik kılıf {phase}", QFont("Segoe UI", 9, QFont.Bold))
            label.setBrush(QColor("#556875"))
            label.setPos(25, y - 12)

        # Legend: colors represent continuous loop identity, not physical phase.
        legend_x = left
        for index, loop_id in enumerate("ABC"):
            x = legend_x + index * 150
            self.scene_obj.addLine(x, 190, x + 28, 190, QPen(QColor(loop_colors[loop_id]), 5, Qt.SolidLine, Qt.RoundCap))
            text = self.scene_obj.addSimpleText(f"Loop {loop_id}", QFont("Segoe UI", 8, QFont.Bold))
            text.setBrush(QColor(loop_colors[loop_id]))
            text.setPos(x + 35, 180)
        info = self.scene_obj.addSimpleText(
            "Renk = sürekli metalik kılıf çevrimi; satır = o minor section'daki fiziksel faz metalik kılıfı",
            QFont("Segoe UI", 8),
        )
        info.setBrush(QColor("#60727f"))
        info.setPos(legend_x + 465, 180)

        link_by_joint = {box.joint_node_id: box for box in bonding.link_boxes}
        ground_by_joint: set[str] = {node.node_id for node in nodes if node.grounded}
        for connection in bonding.connections:
            if connection.connection_type.upper() == "SOLID_GROUND":
                node_id = connection.node_id
                if not node_id and connection.link_box_id:
                    box = next((b for b in bonding.link_boxes if b.link_box_id == connection.link_box_id), None)
                    node_id = box.joint_node_id if box else ""
                if node_id:
                    ground_by_joint.add(node_id)

        # Major-section bands and graph-derived loop paths.
        for major_start in range(0, len(bonding.minor_sections), 3):
            model_group = tuple(bonding.minor_sections[major_start:major_start + 3])
            if len(model_group) != 3:
                continue
            major_index = major_start // 3 + 1
            x_start = x_by_id.get(model_group[0].start_node_id, left)
            x_end = x_by_id.get(model_group[-1].end_node_id, right)
            band = self.scene_obj.addRect(
                x_start, 220, x_end - x_start, 350, QPen(Qt.NoPen),
                QBrush(QColor("#f5f8fb" if major_index % 2 else "#edf3f7")),
            )
            band.setZValue(-6)
            major_label = self.scene_obj.addSimpleText(f"MAJOR {major_index}", QFont("Segoe UI", 8, QFont.Bold))
            major_label.setBrush(QColor("#71818d"))
            major_label.setPos((x_start + x_end) / 2 - 28, 226)
            try:
                paths = resolve_major_paths(bonding, model_group)
            except BondingInputError as exc:
                warning = self.scene_obj.addSimpleText(str(exc), QFont("Segoe UI", 8, QFont.Bold))
                warning.setBrush(QColor("#a43b3b"))
                warning.setPos(x_start + 15, 245)
                continue

            for minor_index, section in enumerate(model_group):
                x1 = x_by_id.get(section.start_node_id, x_start)
                x2 = x_by_id.get(section.end_node_id, x_end)
                occupancy = []
                for loop_index, loop_id in enumerate("ABC"):
                    phase = paths[loop_index][minor_index]
                    occupancy.append(phase)
                    selected = not self._highlight_loop_name or self._highlight_loop_name == f"M{major_index}-Loop {loop_id}"
                    color = QColor(loop_colors[loop_id])
                    if not selected:
                        color.setAlpha(55)
                    width = 7 if selected and self._highlight_loop_name else 4
                    item = self.scene_obj.addLine(
                        x1 + 22, ys[phase], x2 - 22, ys[phase],
                        QPen(color, width, Qt.SolidLine, Qt.RoundCap),
                    )
                    item.setToolTip(
                        f"M{major_index}-Loop {loop_id}: {''.join(paths[loop_index])}\n"
                        f"{section.section_id} içinde fiziksel metalik kılıf {phase}"
                    )
                    loop_tag = self.scene_obj.addSimpleText(loop_id, QFont("Segoe UI", 7, QFont.Bold))
                    loop_tag.setBrush(color)
                    loop_tag.setPos(x1 + 27, ys[phase] - 22)

                section_text = self.scene_obj.addSimpleText(
                    f"{section.section_id} · {section.length_m:.1f} m\n"
                    f"Loop A/B/C → {'/'.join(occupancy)}", QFont("Segoe UI", 8),
                )
                section_text.setBrush(QColor("#405566"))
                section_text.setPos((x1 + x2) / 2 - 58, 580)

            # Draw each internal link-box transition using the corresponding loop color.
            for transition_index, joint_id in enumerate((model_group[0].end_node_id, model_group[1].end_node_id)):
                x = x_by_id[joint_id]
                mapping = self._connection_mapping(bonding, joint_id)
                for loop_index, loop_id in enumerate("ABC"):
                    source_phase = paths[loop_index][transition_index]
                    target_phase = paths[loop_index][transition_index + 1]
                    selected = not self._highlight_loop_name or self._highlight_loop_name == f"M{major_index}-Loop {loop_id}"
                    color = QColor(loop_colors[loop_id])
                    if not selected:
                        color.setAlpha(55)
                    width = 7 if selected and self._highlight_loop_name else 4
                    cross_path = QPainterPath(QPointF(x - 22, ys[source_phase]))
                    cross_path.cubicTo(
                        x - 7, ys[source_phase], x + 7, ys[target_phase], x + 22, ys[target_phase]
                    )
                    item = self.scene_obj.addPath(
                        cross_path, QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                    )
                    item.setToolTip(
                        f"M{major_index}-Loop {loop_id}: {source_phase}→{target_phase}\n"
                        f"{joint_id} / {link_by_joint.get(joint_id).link_box_id if joint_id in link_by_joint else 'Link box yok'}"
                    )

                box = link_by_joint.get(joint_id)
                if box is not None:
                    panel_y = 232.0
                    panel_width = 276.0
                    panel = self.scene_obj.addRect(
                        x - panel_width / 2.0, panel_y, panel_width, 58,
                        QPen(QColor("#7f3c8d"), 2), QBrush(QColor("#fbf6fc"))
                    )
                    local_mapping = " · ".join(
                        f"{phase}-L→{mapping.get(phase, '?')}-R" for phase in "ABC"
                    )
                    cumulative_mapping = " · ".join(
                        f"{loop_id}→{paths[loop_index][transition_index + 1]}"
                        for loop_index, loop_id in enumerate("ABC")
                    )
                    label = self.scene_obj.addSimpleText(
                        f"{box.link_box_id} · yerel L→R\n{local_mapping}",
                        QFont("Segoe UI", 7, QFont.Bold),
                    )
                    label.setBrush(QColor("#6c2a7a"))
                    label.setPos(x - panel_width / 2.0 + 7, panel_y + 4)
                    cumulative = self.scene_obj.addSimpleText(
                        f"Başlangıca göre: {cumulative_mapping}", QFont("Segoe UI", 7)
                    )
                    cumulative.setBrush(QColor("#6f6073"))
                    cumulative.setPos(x - panel_width / 2.0 + 7, panel_y + 34)
                    panel.setToolTip(
                        f"{box.link_box_id} yerel çapraz bağlantısı: {local_mapping}\n"
                        f"Major başlangıcına göre kümülatif yol: {cumulative_mapping}\n"
                        f"Lead {box.lead_length_m:.1f} m · {box.lead_type}"
                    )

        # Physical joint markers, link-box lead and grounding.
        for node in nodes:
            x = x_by_id[node.node_id]
            self.scene_obj.addLine(x, 280, x, 548, QPen(QColor("#647785"), 1, Qt.DotLine))
            for phase, y in ys.items():
                port = self.scene_obj.addEllipse(
                    x - 4, y - 4, 8, 8, QPen(QColor("#475a68"), 1), QBrush(QColor("#ffffff"))
                )
                port.setToolTip(f"{node.node_id} · fiziksel metalik kılıf {phase}")

            box = link_by_joint.get(node.node_id)
            if box is not None:
                bx = x if abs(box.position_m - node.position_m) < 0.1 else left + (right - left) * (box.position_m - nodes[0].position_m) / total
                self.scene_obj.addLine(bx, 278, x, 280, QPen(QColor("#7f3c8d"), 2, Qt.DashLine))

            if node.node_id in ground_by_joint:
                self.scene_obj.addLine(x, 548, x, 558, QPen(QColor("#333333"), 2))
                self.scene_obj.addLine(x - 12, 558, x + 12, 558, QPen(QColor("#333333"), 2))
                self.scene_obj.addLine(x - 8, 564, x + 8, 564, QPen(QColor("#333333"), 2))
                self.scene_obj.addLine(x - 4, 570, x + 4, 570, QPen(QColor("#333333"), 2))

            node_label = self.scene_obj.addSimpleText(
                f"{node.node_id}\n{node.position_m:.1f} m", QFont("Segoe UI", 8, QFont.Bold)
            )
            node_label.setPos(x - 25, 625)

        if result is not None:
            cancellation = "İdeal iptal" if result.ideal_cancellation else "Residual akım mevcut"
            status_text = (
                f"{result.solver_mode} · {result.major_section_count} major · "
                f"λ1={result.lambda1:.6f} · Vmax={result.max_standing_voltage_v:.2f}/{result.voltage_limit_v:.2f} V · "
                f"cond(max)={result.maximum_matrix_condition_number:.3g} · {cancellation}"
            )
            status = self.scene_obj.addSimpleText(status_text, QFont("Segoe UI", 9, QFont.Bold))
            status.setBrush(QColor("#1d5f4a" if result.voltage_limit_ok and result.lead_length_ok else "#a43b3b"))
            status.setPos(left, 675)
        else:
            status = self.scene_obj.addSimpleText(
                "Hesaplanmadı — bağlantı grafiği çizilir; akım ve matris sonucu için Bonding Hesapla'yı çalıştırın.",
                QFont("Segoe UI", 9),
            )
            status.setBrush(QColor("#6b7b88"))
            status.setPos(left, 675)

        bounds = self.scene_obj.itemsBoundingRect().adjusted(-30, -25, 30, 35)
        self._last_fit_bounds = bounds
        self.setSceneRect(bounds)
        # Long bonding routes open as an overview.  The fit scale is also the
        # hard zoom-out floor; wheel-up enters MANUAL mode and may zoom into any
        # major/minor section without resizeEvent snapping back to overview.
        self.set_fit_bounds(bounds)

    def _draw_empty_thermal(self) -> None:
        self.scene_obj.addSimpleText("2D Nodal Yeraltı Termal Çözüm", QFont("Segoe UI", 14, QFont.Bold)).setPos(300, 180)
        note = self.scene_obj.addSimpleText(
            "Termal Güzergâh ekranından 2D Nodal Çalıştır komutunu kullanın.\n"
            "Kararlı durum sıcaklık alanı, kablo sıcaklıkları, enerji dengesi ve bölgesel ampacity burada gösterilir.",
            QFont("Segoe UI", 11),
        )
        note.setBrush(QColor("#586d7d"))
        note.setPos(210, 250)

    def draw_nodal_thermal(
        self,
        result,
        *,
        scenario_name: str = "",
        display_options: dict[str, bool] | None = None,
        context: dict[str, object] | None = None,
    ) -> None:
        """Render the numerical 2D field with auditable engineering overlays.

        The temperature raster, material boundaries and cable positions all come
        from the solved finite-volume model. Optional trench/water annotations are
        supplied from the selected route-region template.
        """
        options = {
            "show_material_boundaries": True,
            "show_geometry": True,
            "show_cables": True,
            "show_mesh": False,
            "show_isotherms": False,
            "show_hotspot": True,
            "show_material_legend": True,
        }
        if display_options:
            options.update({key: bool(value) for key, value in display_options.items()})
        context = dict(context or {})

        self.scene_obj.clear()
        x_edges = list(result.x_edges_m)
        y_edges = list(result.depth_edges_m)
        temperatures = result.temperature_c
        if len(x_edges) < 2 or len(y_edges) < 2 or not temperatures:
            self._draw_empty_thermal()
            return

        xmin, xmax = x_edges[0], x_edges[-1]
        ymin, ymax = y_edges[0], y_edges[-1]
        width = 920.0
        height = 570.0
        left = 95.0
        top = 82.0
        sx = width / max(xmax - xmin, 1e-12)
        sy = height / max(ymax - ymin, 1e-12)
        flat = [value for row in temperatures for value in row]
        tmin = min(flat)
        tmax = max(flat)
        span = max(tmax - tmin, 1e-9)
        cell_count = (len(x_edges) - 1) * (len(y_edges) - 1)
        stride = max(1, int(math.ceil(math.sqrt(cell_count / 7000.0))))

        def color_for(value: float) -> QColor:
            ratio = max(0.0, min(1.0, (value - tmin) / span))
            return QColor.fromHsvF((1.0 - ratio) * 0.67, 0.82, 0.96)

        def scene_point(x_m: float, depth_m: float) -> QPointF:
            return QPointF(left + (x_m - xmin) * sx, top + (depth_m - ymin) * sy)

        # Render to one raster image. This avoids the false white grid/seam
        # artefact created by thousands of adjacent antialiased QGraphicsRectItems.
        image_width = max(2, int(round(width)))
        image_height = max(2, int(round(height)))
        image = QImage(image_width, image_height, QImage.Format.Format_RGB32)
        image.fill(QColor("#ffffff"))
        image_painter = QPainter(image)
        image_painter.setRenderHint(QPainter.Antialiasing, False)
        for iy in range(0, len(y_edges) - 1, stride):
            y2_index = min(len(y_edges) - 1, iy + stride)
            for ix in range(0, len(x_edges) - 1, stride):
                x2_index = min(len(x_edges) - 1, ix + stride)
                samples = [
                    temperatures[j][i]
                    for j in range(iy, y2_index)
                    for i in range(ix, x2_index)
                ]
                value = sum(samples) / len(samples)
                px1 = int(round((x_edges[ix] - xmin) * sx))
                py1 = int(round((y_edges[iy] - ymin) * sy))
                px2 = int(round((x_edges[x2_index] - xmin) * sx))
                py2 = int(round((y_edges[y2_index] - ymin) * sy))
                image_painter.fillRect(px1, py1, max(1, px2 - px1 + 1), max(1, py2 - py1 + 1), color_for(value))
        image_painter.end()
        raster = self.scene_obj.addPixmap(QPixmap.fromImage(image))
        raster.setPos(left, top)
        raster.setZValue(-20)

        # Material interfaces taken from the solver's cell material map.
        if options["show_material_boundaries"]:
            boundary_path = QPainterPath()
            for x1, y1, x2, y2 in extract_material_boundary_segments(
                x_edges, y_edges, result.material_ids
            ):
                p1 = scene_point(x1, y1)
                p2 = scene_point(x2, y2)
                boundary_path.moveTo(p1)
                boundary_path.lineTo(p2)
            boundary_item = self.scene_obj.addPath(
                boundary_path, QPen(QColor(35, 47, 58, 175), 1.15)
            )
            boundary_item.setZValue(5)

        # Optional approximate isotherms are a display aid only.
        if options["show_isotherms"]:
            iso_path = QPainterPath()
            for x1, y1, x2, y2 in extract_quantized_isotherm_segments(
                x_edges, y_edges, temperatures, level_count=7
            ):
                p1 = scene_point(x1, y1)
                p2 = scene_point(x2, y2)
                iso_path.moveTo(p1)
                iso_path.lineTo(p2)
            iso_item = self.scene_obj.addPath(
                iso_path, QPen(QColor(255, 255, 255, 145), 1.0, Qt.DotLine)
            )
            iso_item.setZValue(6)

        if options["show_mesh"]:
            mesh_path = QPainterPath()
            mesh_stride_x = max(1, int(math.ceil((len(x_edges) - 1) / 85.0)))
            mesh_stride_y = max(1, int(math.ceil((len(y_edges) - 1) / 70.0)))
            for index in range(0, len(x_edges), mesh_stride_x):
                x = left + (x_edges[index] - xmin) * sx
                mesh_path.moveTo(x, top)
                mesh_path.lineTo(x, top + height)
            for index in range(0, len(y_edges), mesh_stride_y):
                y = top + (y_edges[index] - ymin) * sy
                mesh_path.moveTo(left, y)
                mesh_path.lineTo(left + width, y)
            mesh_item = self.scene_obj.addPath(
                mesh_path, QPen(QColor(255, 255, 255, 105), 0.75)
            )
            mesh_item.setZValue(7)

        # Explicit route-section geometry annotations. The actual material
        # interfaces remain the authoritative solved-cell boundaries above.
        if options["show_geometry"]:
            trench_center = float(context.get("trench_center_x_m", 0.0) or 0.0)
            trench_width = float(context.get("trench_width_m", 0.0) or 0.0)
            trench_depth = float(context.get("trench_depth_m", 0.0) or 0.0)
            trench_slope = max(0.0, float(context.get("trench_side_slope_h_to_v", 0.0) or 0.0))
            if trench_width > 0 and trench_depth > 0:
                bottom_half = trench_width / 2.0
                top_half = bottom_half + trench_slope * trench_depth
                trench_polygon = QPolygonF([
                    scene_point(trench_center - top_half, 0.0),
                    scene_point(trench_center + top_half, 0.0),
                    scene_point(trench_center + bottom_half, trench_depth),
                    scene_point(trench_center - bottom_half, trench_depth),
                ])
                trench = self.scene_obj.addPolygon(
                    trench_polygon,
                    QPen(QColor("#6c4d2f"), 1.8, Qt.DashLine),
                    QBrush(Qt.NoBrush),
                )
                trench.setToolTip(
                    f"Kablo-Kanal hendek sınırı: alt W={trench_width:.3f} m, "
                    f"D={trench_depth:.3f} m, şev={trench_slope:.3f} H/V"
                )
                trench.setZValue(9)

                def add_layer_boundary(depth_m: float, label: str) -> None:
                    if not (0.0 < depth_m < trench_depth):
                        return
                    local_half = bottom_half + trench_slope * (trench_depth - depth_m)
                    p1 = scene_point(trench_center - local_half, depth_m)
                    p2 = scene_point(trench_center + local_half, depth_m)
                    line = self.scene_obj.addLine(
                        p1.x(), p1.y(), p2.x(), p2.y(),
                        QPen(QColor("#704b2a"), 1.0, Qt.DotLine),
                    )
                    line.setToolTip(label)
                    line.setZValue(9)

                bedding = max(0.0, float(context.get("bedding_thickness_m", 0.0) or 0.0))
                thermal_backfill = max(0.0, float(context.get("thermal_backfill_height_m", 0.0) or 0.0))
                selected_fill = max(0.0, float(context.get("selected_fill_thickness_m", 0.0) or 0.0))
                surface_layer = max(0.0, float(context.get("surface_layer_thickness_m", 0.0) or 0.0))
                bedding_top = max(0.0, trench_depth - bedding)
                thermal_backfill_top = max(0.0, bedding_top - thermal_backfill)
                selected_fill_top = max(0.0, thermal_backfill_top - selected_fill)
                add_layer_boundary(bedding_top, "Yataklama / kum zarfı üst sınırı")
                add_layer_boundary(thermal_backfill_top, "Termal backfill üst sınırı")
                add_layer_boundary(selected_fill_top, "Seçilmiş dolgu üst sınırı")
                add_layer_boundary(surface_layer, "Yüzey tabakası alt sınırı")

            installation_type = str(context.get("installation_type", "") or "").upper()
            duct_slots = tuple(context.get("duct_slots", ()) or ())
            for slot in duct_slots:
                if not isinstance(slot, dict):
                    continue
                slot_x = float(slot.get("x_m", 0.0) or 0.0)
                slot_depth = float(slot.get("depth_m", 0.0) or 0.0)
                inner = max(0.0, float(slot.get("inner_diameter_m", 0.0) or 0.0))
                outer = max(inner, float(slot.get("outer_diameter_m", 0.0) or 0.0))
                if outer <= 0:
                    continue
                centre = scene_point(slot_x, slot_depth)
                outer_px = max(4.0, outer * min(sx, sy))
                inner_px = max(2.0, inner * min(sx, sy))
                duct_outer_item = self.scene_obj.addEllipse(
                    centre.x() - outer_px / 2.0, centre.y() - outer_px / 2.0,
                    outer_px, outer_px,
                    QPen(QColor("#d9e2e8"), 1.5), QBrush(Qt.NoBrush),
                )
                duct_outer_item.setToolTip(
                    f"Duct {slot.get('slot_id', '')}: Øi={inner:.3f} m, Ød={outer:.3f} m"
                )
                duct_outer_item.setZValue(11)
                duct_inner_item = self.scene_obj.addEllipse(
                    centre.x() - inner_px / 2.0, centre.y() - inner_px / 2.0,
                    inner_px, inner_px,
                    QPen(QColor("#8da0ae"), 0.9, Qt.DotLine), QBrush(Qt.NoBrush),
                )
                duct_inner_item.setZValue(11)

            if installation_type == "DUCT_BANK":
                bank_width = max(0.0, float(context.get("duct_bank_width_m", 0.0) or 0.0))
                bank_height = max(0.0, float(context.get("duct_bank_height_m", 0.0) or 0.0))
                if bank_width > 0 and bank_height > 0:
                    depths = [float(item.get("depth_m", 0.0) or 0.0) for item in duct_slots if isinstance(item, dict)]
                    if not depths:
                        depths = [float(item.depth_m) for item in result.cables]
                    bank_depth = sum(depths) / len(depths) if depths else trench_depth / 2.0
                    p1 = scene_point(trench_center - bank_width / 2.0, bank_depth - bank_height / 2.0)
                    p2 = scene_point(trench_center + bank_width / 2.0, bank_depth + bank_height / 2.0)
                    bank = self.scene_obj.addRect(
                        min(p1.x(), p2.x()), min(p1.y(), p2.y()),
                        abs(p2.x() - p1.x()), abs(p2.y() - p1.y()),
                        QPen(QColor("#656d78"), 1.4, Qt.DashDotLine), QBrush(Qt.NoBrush),
                    )
                    bank.setToolTip("Duct bank / grout fiziksel sınırı")
                    bank.setZValue(10)

            if bool(context.get("cover_slab_enabled", False)):
                slab_width = max(0.0, float(context.get("cover_slab_width_m", 0.0) or 0.0))
                slab_thickness = max(0.0, float(context.get("cover_slab_thickness_m", 0.0) or 0.0))
                slab_depth = max(0.0, float(context.get("cover_slab_depth_m", 0.0) or 0.0))
                if slab_width > 0 and slab_thickness > 0:
                    p1 = scene_point(trench_center - slab_width / 2.0, slab_depth - slab_thickness / 2.0)
                    p2 = scene_point(trench_center + slab_width / 2.0, slab_depth + slab_thickness / 2.0)
                    slab = self.scene_obj.addRect(
                        min(p1.x(), p2.x()), min(p1.y(), p2.y()),
                        abs(p2.x() - p1.x()), abs(p2.y() - p1.y()),
                        QPen(QColor("#5f6973"), 1.4), QBrush(QColor(235, 238, 240, 65)),
                    )
                    slab.setToolTip("Koruma plakası")
                    slab.setZValue(10)

            groundwater = float(context.get("groundwater_depth_m", 0.0) or 0.0)
            if ymin <= groundwater <= ymax:
                gy = top + (groundwater - ymin) * sy
                water = self.scene_obj.addLine(
                    left, gy, left + width, gy, QPen(QColor("#2b83ba"), 2, Qt.DashDotLine)
                )
                water.setToolTip(f"Yeraltı su seviyesi: {groundwater:.3f} m")
                water.setZValue(8)
                water_label = self.scene_obj.addSimpleText("Yeraltı su seviyesi", QFont("Segoe UI", 8))
                water_label.setBrush(QColor("#1e6d9f"))
                water_label.setPos(left + 8, gy - 19)
                water_label.setZValue(9)

        self.scene_obj.addRect(
            left, top, width, height, QPen(QColor("#34495e"), 1.5), QBrush(Qt.NoBrush)
        ).setZValue(12)
        surface_y = top + (0.0 - ymin) * sy
        self.scene_obj.addLine(
            left, surface_y, left + width, surface_y, QPen(QColor("#263746"), 2)
        ).setZValue(13)

        critical_cable = max(
            result.cables, key=lambda item: item.conductor_temperature_c, default=None
        )
        if options["show_cables"]:
            cable_outer_diameter_m = float(context.get("cable_outer_diameter_m", 0.105) or 0.105)
            # Fiziksel çap gerçek ölçeğinde çizilir. Uzak alan nedeniyle ekranda
            # birkaç piksele düştüğünde ayrıca transformdan bağımsız bir görünürlük
            # halkası eklenir; bu halka fiziksel çap değildir, yalnız konum işaretidir.
            physical_diameter = max(2.0, cable_outer_diameter_m * min(sx, sy))
            for cable in result.cables:
                cx = left + (cable.x_m - xmin) * sx
                cy = top + (cable.depth_m - ymin) * sy
                is_critical = critical_cable is not None and cable.cable_id == critical_cable.cable_id
                energized = cable.current_a > 1e-9 or cable.total_loss_w_m > 1e-9
                if is_critical:
                    pen = QPen(QColor("#fff19a"), 3.2)
                elif energized:
                    pen = QPen(QColor("#ffffff"), 2.0)
                else:
                    pen = QPen(QColor("#d2d9df"), 1.8, Qt.DashLine)
                item = self.scene_obj.addEllipse(
                    cx - physical_diameter / 2.0, cy - physical_diameter / 2.0,
                    physical_diameter, physical_diameter,
                    pen, QBrush(QColor("#14202a" if energized else "#66727b")),
                )
                item.setZValue(20)
                item.setToolTip(
                    f"{cable.cable_id} · {'ENERJİLİ' if energized else 'PASİF'}\n"
                    f"I={cable.current_a:.2f} A\n"
                    f"Tcond={cable.conductor_temperature_c:.2f} °C\n"
                    f"Tjacket={cable.jacket_temperature_c:.2f} °C\n"
                    f"Q={cable.total_loss_w_m:.3f} W/m"
                )

                # Kablo gerçek ölçekte çok küçükse termal renk alanı içinde
                # kaybolmaması için ekran-pikseli sabit bir halo.
                if physical_diameter < 16.0:
                    halo = self.scene_obj.addEllipse(-9.0, -9.0, 18.0, 18.0,
                        QPen(QColor("#fff19a" if is_critical else "#f6fbff"), 1.8),
                        QBrush(Qt.NoBrush))
                    halo.setPos(cx, cy)
                    halo.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
                    halo.setZValue(21)
                    halo.setToolTip(item.toolTip())

                # Faz/devre etiketi ekran ölçeğinden bağımsız kalır; aksi halde
                # fitInView sonrası 5–6 px'e düşüp okunamaz hale geliyordu.
                phase_text = f"{cable.circuit_index}{cable.phase}"
                phase_label = self.scene_obj.addSimpleText(phase_text, QFont("Segoe UI", 8, QFont.Bold))
                phase_label.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
                phase_label.setBrush(QColor("#ffffff"))
                phase_label.setPos(cx + max(5.0, physical_diameter * 0.45), cy - 16.0)
                phase_label.setZValue(22)

        if options["show_hotspot"]:
            max_index = max(
                ((value, iy, ix) for iy, row in enumerate(temperatures) for ix, value in enumerate(row)),
                key=lambda item: item[0],
            )
            max_value, hot_iy, hot_ix = max_index
            hot_x = (x_edges[hot_ix] + x_edges[hot_ix + 1]) / 2.0
            hot_y = (y_edges[hot_iy] + y_edges[hot_iy + 1]) / 2.0
            hp = scene_point(hot_x, hot_y)
            self.scene_obj.addEllipse(
                hp.x() - 8, hp.y() - 8, 16, 16, QPen(QColor("#ffffff"), 2.2), QBrush(Qt.NoBrush)
            ).setZValue(18)
            self.scene_obj.addLine(hp.x() - 12, hp.y(), hp.x() + 12, hp.y(), QPen(QColor("#4a1e1e"), 1.2)).setZValue(19)
            self.scene_obj.addLine(hp.x(), hp.y() - 12, hp.x(), hp.y() + 12, QPen(QColor("#4a1e1e"), 1.2)).setZValue(19)
            hot_label = self.scene_obj.addSimpleText(f"Tmax alan = {max_value:.2f} °C", QFont("Segoe UI", 8, QFont.Bold))
            hot_label.setBrush(QColor("#5b1d1d"))
            hot_label.setPos(hp.x() + 10, hp.y() - 27)
            hot_label.setZValue(20)

        title_text = f"{result.region_id} · {result.region_name}"
        if scenario_name:
            title_text += f" · {scenario_name}"
        title_text += " · 2D enine kesit kararlı durum sıcaklık alanı"
        title = QGraphicsTextItem()
        title.setPlainText(title_text)
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setTextWidth(width)
        title.setDefaultTextColor(QColor("#223746"))
        title.setPos(left, 12)
        title.setZValue(30)
        self.scene_obj.addItem(title)

        margin = result.ampacity_per_cable_a - result.design_current_per_cable_a
        summary_text = (
            f"Devre={result.active_circuit_count}/{result.present_circuit_count} enerjili · "
            f"Iref={result.design_current_per_cable_a:.1f} A/kablo · "
            f"Iamp,2D={result.ampacity_per_cable_a:.1f} A · marj={margin:+.1f} A\n"
            f"Tcond,max={result.maximum_conductor_temperature_c:.2f}/{result.temperature_limit_c:.1f} °C · "
            f"IEC={result.iec_ampacity_per_cable_a:.1f} A ({result.difference_from_iec_percent:+.2f} %) · "
            f"Enerji hata=%{result.energy_balance_error_percent:.4f}"
        )
        summary = QGraphicsTextItem()
        summary.setPlainText(summary_text)
        summary.setFont(QFont("Segoe UI", 8, QFont.Bold))
        summary.setTextWidth(width)
        summary.setDefaultTextColor(QColor(display_foreground(result.status)))
        summary.setPos(left, top + height + 8)
        summary.setZValue(30)
        self.scene_obj.addItem(summary)

        legend_x = left + width + 24
        legend_height = 320.0
        steps = 48
        for index in range(steps):
            ratio = index / max(steps - 1, 1)
            value = tmax - ratio * span
            self.scene_obj.addRect(
                legend_x, top + ratio * legend_height, 22, legend_height / steps + 1,
                QPen(Qt.NoPen), QBrush(color_for(value)),
            )
        self.scene_obj.addSimpleText(f"{tmax:.1f} °C", QFont("Segoe UI", 8)).setPos(legend_x + 28, top - 7)
        self.scene_obj.addSimpleText(f"{tmin:.1f} °C", QFont("Segoe UI", 8)).setPos(legend_x + 28, top + legend_height - 7)
        self.scene_obj.addSimpleText(
            f"Mesh {result.mesh_nx}×{result.mesh_ny}\n{result.mesh_cell_count} hücre\n"
            f"Residual {result.maximum_linear_residual:.2e}\n"
            f"Qsrc/Qout {result.total_heat_source_w_m:.3f}/{result.total_boundary_heat_w_m:.3f} W/m",
            QFont("Segoe UI", 8),
        ).setPos(legend_x, top + legend_height + 35)

        if options["show_material_legend"]:
            material_names = dict(context.get("material_names", {}) or {})
            unique_materials = []
            for row in result.material_ids:
                for material_id in row:
                    if material_id not in unique_materials:
                        unique_materials.append(material_id)
            legend_title = self.scene_obj.addSimpleText("Çözülen malzemeler", QFont("Segoe UI", 8, QFont.Bold))
            legend_title.setPos(legend_x, top + legend_height + 112)
            for index, material_id in enumerate(unique_materials[:11]):
                label = str(material_names.get(material_id, material_id))
                if len(label) > 30:
                    label = label[:27] + "…"
                item = self.scene_obj.addSimpleText(f"• {material_id}: {label}", QFont("Segoe UI", 7))
                item.setBrush(QColor("#405566"))
                item.setPos(legend_x, top + legend_height + 130 + index * 17)

        # Uzun başlık/özet veya malzeme adı scene bounding rect'i büyütüp
        # sıcaklık alanını küçültmesin. Görsel için sabit bir kompozisyon alanı
        # tanımlanır; metinler bu alan içinde sarılır/kısaltılır.
        sidebar_width = 245.0
        display_bounds = QRectF(
            left - 42.0, 4.0,
            width + sidebar_width + 70.0,
            height + 190.0,
        )
        self._last_fit_bounds = display_bounds
        self.setSceneRect(display_bounds)
        self.set_fit_bounds(display_bounds)



class TransientThermalView(ZoomPanGraphicsView):
    """Compact load/temperature plot drawn from transient solver points."""

    def __init__(self, parent=None) -> None:
        self.scene_obj = QGraphicsScene()
        super().__init__(self.scene_obj, parent)
        self.setMinimumHeight(300)
        self.draw_result(None)

    def draw_result(self, result) -> None:
        self.scene_obj.clear()
        width, height = 1050.0, 470.0
        left, right, top, bottom = 85.0, 1015.0, 55.0, 405.0
        self.setSceneRect(0, 0, width, height)
        title_text = "IEC 60853 geçici sıcaklık ve yük profili"
        if result is not None:
            title_text = f"{result.region_id} — {result.region_name} · {result.profile_name}"
        title = self.scene_obj.addSimpleText(title_text, QFont("Segoe UI", 12, QFont.Bold))
        title.setPos(left, 12)
        self.scene_obj.addLine(left, bottom, right, bottom, QPen(QColor("#4f6270"), 1.5))
        self.scene_obj.addLine(left, top, left, bottom, QPen(QColor("#4f6270"), 1.5))
        if result is None or not result.points:
            note = self.scene_obj.addSimpleText("Geçici termal hesap sonucu bekleniyor.", QFont("Segoe UI", 10))
            note.setBrush(QColor("#6b7b88"))
            note.setPos(left + 30, top + 70)
            return

        points = result.points
        max_time = max(float(point.time_h) for point in points) or 1.0
        t_min = min(0.0, min(float(point.maximum_jacket_temperature_c) for point in points) - 5.0)
        t_max = max(
            float(result.emergency_temperature_limit_c),
            max(float(point.maximum_conductor_temperature_c) for point in points) + 5.0,
        )
        current_max = max(float(point.current_a) for point in points) or 1.0

        def x_of(time_h: float) -> float:
            return left + (right - left) * time_h / max_time

        def y_of_temp(value: float) -> float:
            return bottom - (bottom - top) * (value - t_min) / max(t_max - t_min, 1e-12)

        def y_of_current(value: float) -> float:
            band_top = top + 0.62 * (bottom - top)
            return bottom - (bottom - band_top) * value / current_max

        for index in range(6):
            value = t_min + index * (t_max - t_min) / 5.0
            y = y_of_temp(value)
            self.scene_obj.addLine(left, y, right, y, QPen(QColor("#dce4ea"), 0.8, Qt.DotLine))
            label = self.scene_obj.addSimpleText(f"{value:.0f} °C", QFont("Segoe UI", 8))
            label.setBrush(QColor("#526878"))
            label.setPos(18, y - 10)
        for index in range(7):
            time_h = index * max_time / 6.0
            x = x_of(time_h)
            self.scene_obj.addLine(x, top, x, bottom, QPen(QColor("#e4eaef"), 0.8, Qt.DotLine))
            label = self.scene_obj.addSimpleText(f"{time_h:.1f} h", QFont("Segoe UI", 8))
            label.setBrush(QColor("#526878"))
            label.setPos(x - 16, bottom + 8)

        normal_y = y_of_temp(float(result.normal_temperature_limit_c))
        emergency_y = y_of_temp(float(result.emergency_temperature_limit_c))
        self.scene_obj.addLine(left, normal_y, right, normal_y, QPen(QColor("#d08c20"), 1.5, Qt.DashLine))
        self.scene_obj.addLine(left, emergency_y, right, emergency_y, QPen(QColor("#b23a3a"), 1.5, Qt.DashLine))

        conductor_path = QPainterPath()
        jacket_path = QPainterPath()
        current_path = QPainterPath()
        for index, point in enumerate(points):
            x = x_of(float(point.time_h))
            yc = y_of_temp(float(point.maximum_conductor_temperature_c))
            yj = y_of_temp(float(point.maximum_jacket_temperature_c))
            yi = y_of_current(float(point.current_a))
            if index == 0:
                conductor_path.moveTo(x, yc)
                jacket_path.moveTo(x, yj)
                current_path.moveTo(x, yi)
            else:
                conductor_path.lineTo(x, yc)
                jacket_path.lineTo(x, yj)
                current_path.lineTo(x, yi)
        self.scene_obj.addPath(conductor_path, QPen(QColor("#c4473d"), 3.0))
        self.scene_obj.addPath(jacket_path, QPen(QColor("#2c6eaa"), 2.2))
        self.scene_obj.addPath(current_path, QPen(QColor("#4e8b57"), 2.0, Qt.DashLine))

        legend = [
            ("İletken sıcaklığı", QColor("#c4473d")),
            ("Jacket sıcaklığı", QColor("#2c6eaa")),
            ("Akım (alt bant, bağıl)", QColor("#4e8b57")),
        ]
        for index, (text_value, color) in enumerate(legend):
            x = left + 210.0 * index
            self.scene_obj.addLine(x, 42, x + 28, 42, QPen(color, 3))
            label = self.scene_obj.addSimpleText(text_value, QFont("Segoe UI", 8, QFont.Bold))
            label.setBrush(color)
            label.setPos(x + 34, 32)

        max_point = max(points, key=lambda item: item.maximum_conductor_temperature_c)
        marker_x = x_of(float(max_point.time_h))
        marker_y = y_of_temp(float(max_point.maximum_conductor_temperature_c))
        self.scene_obj.addEllipse(marker_x - 5, marker_y - 5, 10, 10, QPen(QColor("#7d1f1f"), 2), QBrush(QColor("#ffffff")))
        tooltip = self.scene_obj.addSimpleText(
            f"Tmax {max_point.maximum_conductor_temperature_c:.2f} °C @ {max_point.time_h:.2f} h",
            QFont("Segoe UI", 8, QFont.Bold),
        )
        tooltip.setBrush(QColor("#7d1f1f"))
        tooltip.setPos(min(marker_x + 8, right - 190), max(top, marker_y - 25))
        self.set_fit_bounds(self.scene_obj.itemsBoundingRect().adjusted(-20, -15, 20, 20))
