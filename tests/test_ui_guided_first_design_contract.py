from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_WINDOW = ROOT / "src" / "ucd" / "ui" / "main_window.py"
CABLE_SELECTION = ROOT / "src" / "ucd" / "ui" / "project_cable_selection_dialog.py"
CABLE_LIBRARY = ROOT / "src" / "ucd" / "ui" / "cable_library_widget.py"
ROUTE_DIALOG = ROOT / "src" / "ucd" / "ui" / "route_section_dialog.py"
PLAN_VIEW = ROOT / "src" / "ucd" / "ui" / "graphics_views.py"
WORKFLOW_USER = ROOT / "src" / "ucd" / "ui" / "workflow_user_state.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _method_block(source: str, name: str, next_name: str) -> str:
    start = source.index(f"    def {name}")
    end = source.index(f"    def {next_name}", start)
    return source[start:end]


def test_project_tree_does_not_expose_cable_database() -> None:
    source = _source(MAIN_WINDOW)
    block = _method_block(source, "_build_tree(self) -> None:", "_set_property_rows")
    assert '"Kablo Kütüphanesi"' not in block
    assert '"Projeye Atanmış Kablolar"' in block


def test_top_level_database_menu_is_separate_from_project_cable_menu() -> None:
    source = _source(MAIN_WINDOW)
    block = _method_block(source, "_build_menu(self) -> None:", "_build_toolbar")
    assert 'self.menuBar().addMenu("Kablo")' in block
    assert 'self.menuBar().addMenu("Veri Tabanları")' in block
    assert "database_menu.addAction(self.act_cable_library)" in block
    assert "cable_menu.addAction(self.act_project_cable_select)" in block
    assert "cable_menu.addAction(self.act_cable_library)" not in block
    assert 'self.menuBar().addMenu("Araçlar")' not in block


def test_project_cable_selection_has_visible_select_assign_save_lifecycle() -> None:
    source = _source(CABLE_SELECTION)
    assert '"▶ SEÇİLİ"' in source
    assert '"✓ ATANMIŞ"' in source
    assert '"✓ SEÇİLİ / ATANMIŞ"' in source
    assert 'QPushButton("Seçili Kabloyu Projeye Ata")' in source
    assert '"Proje dosyası henüz kaydedilmedi"' in source
    assert "Ürün seçimi projeyi değiştirmez" in source
    assert "define_project_cable" in source


def test_database_and_project_cable_editor_modes_are_separated() -> None:
    source = _source(CABLE_LIBRARY)
    assert 'title_text = "Kablo Veri Tabanı" if self.database_mode else "Proje Kablo Editörü"' in source
    assert "if not self.database_mode:" in source
    assert 'tabs.addTab(self._build_candidate_tab(), "Proje Adayları")' in source
    assert "def begin_new_manual_cable" in source


def test_first_design_only_recommends_and_waits_for_explicit_assignment() -> None:
    source = _source(MAIN_WINDOW)
    block = _method_block(source, "run_first_design_iteration", "new_project")
    assert 'basis.selected_candidate_id = ""' in block
    assert 'last_iteration_status = "CONDITIONAL_READY"' in block
    assert '"Aday projeye atanmadı; kullanıcı kararı bekleniyor."' in block
    assert "apply_candidate_to_project" not in block
    for forbidden in (
        "run_bonding_solver",
        "run_fault_study",
        "run_svl_selection",
        "run_transient_thermal_analysis",
    ):
        assert forbidden not in block


def test_route_editor_is_summary_table_plus_short_form_and_explicit_acceptance() -> None:
    source = _source(MAIN_WINDOW)
    block = _method_block(source, "_build_route_table_widget", "_build_thermal_route_widget")
    assert "QAbstractItemView.NoEditTriggers" in block
    assert 'QPushButton("Bölüm Ekle")' in block
    assert 'QPushButton("Seçili Bölümü Düzenle")' in block
    assert 'QPushButton("Mevcut Güzergâhı Kabul Et")' in block
    assert "RouteSectionDialog" in source
    route_source = _source(ROUTE_DIALOG)
    assert 'buttons.button(QDialogButtonBox.Save).setText("Bölümü Kaydet")' in route_source
    assert "SOURCE_PREFIX" in route_source


def test_plan_canvas_uses_selection_cursor_by_default() -> None:
    source = _source(PLAN_VIEW)
    assert "self.setDragMode(QGraphicsView.NoDrag)" in source
    assert "self.setCursor(Qt.ArrowCursor)" in source


def test_user_facing_workflow_states_are_plain_language() -> None:
    source = _source(WORKFLOW_USER)
    for label in (
        "Yapılacak",
        "Veri gerekli",
        "Hesaplanabilir",
        "Tamamlandı",
        "Koşullu",
        "Yeniden hesapla",
        "Bloke",
    ):
        assert label in source
