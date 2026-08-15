from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_common_graphics_zoom_has_fit_manual_contract() -> None:
    source = (ROOT / "src/ucd/ui/graphics_views.py").read_text(encoding="utf-8")
    assert 'ZOOM_STEP = 1.10' in source
    assert 'MAX_ZOOM_OVER_FIT = 16.0' in source
    assert 'self._zoom_view_mode = "MANUAL"' in source
    assert 'self._zoom_view_mode = "FIT"' in source
    assert 'if self._zoom_view_mode == "FIT" and not self._zoom_applying_fit:' in source
    assert 'if delta < 0 and target <= fit_scale * 1.001:' in source
    assert 'self._zoom_view_mode = "MANUAL"\n        self.scale(factor, factor)' in source


def test_simple_diagram_no_longer_refits_unconditionally_on_resize() -> None:
    source = (ROOT / "src/ucd/ui/graphics_views.py").read_text(encoding="utf-8")
    simple = source.split("class SimpleDiagramView", 1)[1].split("class TransientThermalView", 1)[0]
    assert "def resizeEvent" not in simple
    assert "def wheelEvent" not in simple
    assert "self.set_fit_bounds(bounds)" in simple
    assert "self.set_fit_bounds(display_bounds)" in simple
    assert "self.resetTransform()\n            self.scale(0.82, 0.82)" not in simple


def test_installation_canvas_uses_same_fit_manual_principle() -> None:
    source = (ROOT / "src/ucd/ui/installation_designer_dialog.py").read_text(encoding="utf-8")
    canvas = source.split("class InstallationCanvas", 1)[1].split("class InstallationDesignerDialog", 1)[0]
    assert 'self._zoom_view_mode = "MANUAL"' in canvas
    assert 'self._zoom_view_mode = "FIT"' in canvas
    assert 'if self._zoom_view_mode == "FIT" and not self._zoom_applying_fit:' in canvas
    assert 'if not zoom_in and target <= fit_scale * 1.001:' in canvas
    assert 'maximum = fit_scale * 16.0' in canvas
    assert 'current <= 0.22' not in canvas


def test_cable_preview_uses_common_zoom_contract() -> None:
    source = (ROOT / "src/ucd/ui/cable_library_widget.py").read_text(encoding="utf-8")
    assert "class CableCrossSectionView(ZoomPanGraphicsView):" in source
    assert "self.set_fit_bounds(self.scene_obj.sceneRect())" in source
