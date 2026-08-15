from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_application_orchestration_has_no_qt_dependency():
    source = (ROOT / "src/ucd/calculations/application_orchestration.py").read_text(encoding="utf-8")
    assert "PySide6" not in source
    assert "QMessageBox" not in source


def test_thermal_preprocessor_sequence_is_outside_main_window():
    source = (ROOT / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    method = source[source.index("    def run_thermal_preprocessor"):source.index("    def _populate_thermal_results")]
    assert "run_application_thermal_preprocessor(self.project)" in method
    assert "materialize_project_route_sections(" not in method
    assert "solve_section_thermal(" not in method
