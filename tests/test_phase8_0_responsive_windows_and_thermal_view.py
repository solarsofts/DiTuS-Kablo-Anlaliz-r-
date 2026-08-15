"""FAZ 8.0 — responsive window + thermal viewport regression contracts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "src" / "ucd" / "ui"


def _text(name: str) -> str:
    return (UI / name).read_text(encoding="utf-8")


def test_global_window_manager_covers_nested_auxiliary_dialogs() -> None:
    layout = _text("window_layout.py")
    main = (ROOT / "src" / "ucd" / "main.py").read_text(encoding="utf-8")
    assert "class ResponsiveWindowManager(QObject)" in layout
    assert "QEvent.Show" in layout
    assert "install_responsive_window_manager(app)" in main
    assert "Qt.WindowMinMaxButtonsHint" in layout


def test_screen_fit_does_not_lock_maximum_size() -> None:
    layout = _text("window_layout.py")
    # The old FAZ 8.0 implementation capped maximumSize to availableGeometry,
    # which made maximise ineffective and trapped helper windows.
    assert ".setMaximumSize(" not in layout
    assert "widget.resize(width, height)" in layout
    assert "widget.setMinimumSize(0, 0)" in layout


def test_start_dialog_is_not_fixed_pixel_size() -> None:
    wizard = _text("project_wizard.py")
    start = wizard[wizard.index("class StartDialog"):]
    assert "setFixedSize(" not in start
    assert "fit_window(self, DENSITY_NORMAL" in start


def test_installation_designer_can_shrink_inside_small_work_area() -> None:
    source = _text("installation_designer_dialog.py")
    assert "self.setMinimumSize(300, 260)" in source
    assert "right.setMinimumWidth(360)" in source
    assert "parameter_scroll.setMinimumHeight(140)" in source
    assert "lower_panel.setMinimumHeight(180)" in source
    assert "self.tabs.setMinimumHeight(150)" in source
    assert "right.setMinimumWidth(610)" not in source


def test_stage_host_keeps_navigation_reachable_with_scrollable_body() -> None:
    source = _text("stage_host.py")
    assert "self.body_scroll = QScrollArea()" in source
    assert "self.body_scroll.setWidgetResizable(True)" in source
    assert "layout.addWidget(self.body_scroll, 1)" in source
    assert "layout.addWidget(self.footer)" in source


def test_nodal_thermal_plot_does_not_fit_against_unbounded_text() -> None:
    source = _text("graphics_views.py")
    block = source[source.index("    def draw_nodal_thermal"):source.index("class TransientThermalView")]
    assert "QGraphicsTextItem()" in block
    assert "title.setTextWidth(width)" in block
    assert "summary.setTextWidth(width)" in block
    assert "display_bounds = QRectF(" in block
    assert "itemsBoundingRect().adjusted(-25, -20, 25, 25)" not in block


def test_nodal_cables_keep_true_geometry_and_visibility_marker() -> None:
    source = _text("graphics_views.py")
    block = source[source.index("    def draw_nodal_thermal"):source.index("class TransientThermalView")]
    assert "physical_diameter = max(2.0, cable_outer_diameter_m * min(sx, sy))" in block
    assert "ItemIgnoresTransformations" in block
    assert "if physical_diameter < 16.0:" in block
    assert "phase_label.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)" in block


def test_thermal_screen_has_explicit_refit_control_and_compact_help() -> None:
    source = _text("main_window.py")
    block = source[source.index("    def _build_thermal_review_widget"):source.index("    def _build_transient_widget")]
    assert 'QPushButton("Görünüme Sığdır")' in block
    assert "self.thermal_view.fit_current_view()" in block
    assert "self.thermal_view.setMinimumHeight(300)" in block
    assert "full_note = (" in block
