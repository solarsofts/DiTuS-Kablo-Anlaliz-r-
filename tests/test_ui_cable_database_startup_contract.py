from pathlib import Path


def test_database_mode_refresh_treats_candidate_label_as_optional() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src" / "ucd" / "ui" / "cable_library_widget.py"
    ).read_text(encoding="utf-8")

    assert "self.candidate_basis_label: QLabel | None = None" in source
    assert "label = self.candidate_basis_label" in source
    assert "if label is None:" in source
    assert "label.setText(" in source


def test_hotfix_keeps_candidate_tab_project_only() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src" / "ucd" / "ui" / "cable_library_widget.py"
    ).read_text(encoding="utf-8")

    assert "if not self.database_mode:" in source
    assert 'tabs.addTab(self._build_candidate_tab(), "Proje Adayları")' in source


def test_candidate_basis_refresh_is_noop_without_project_tab() -> None:
    import ast
    from types import SimpleNamespace

    source = (
        Path(__file__).resolve().parents[1]
        / "src" / "ucd" / "ui" / "cable_library_widget.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "CableLibraryWidget"
    )
    method_node = next(
        node for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "_refresh_candidate_basis"
    )
    module = ast.Module(body=[method_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, object] = {}
    exec(compile(module, "<candidate-basis-method>", "exec"), namespace)

    fake_widget = SimpleNamespace(candidate_basis_label=None)
    namespace["_refresh_candidate_basis"](fake_widget)
