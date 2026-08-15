APP_STYLE = r"""
QMainWindow, QWidget {
    background: #eef2f5;
    color: #203040;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMenuBar, QMenu, QToolBar, QStatusBar {
    background: #f8fafc;
    border-color: #cfd8e3;
}
QMenuBar::item:selected, QMenu::item:selected {
    background: #dbe8f5;
}
QToolBar {
    spacing: 5px;
    padding: 5px;
    border-bottom: 1px solid #c8d2dc;
}
QToolButton {
    background: #ffffff;
    border: 1px solid #c7d2dc;
    border-radius: 4px;
    padding: 6px 10px;
}
QToolButton:hover { background: #e9f2fb; }
QToolButton:pressed { background: #d6e6f5; }
QTreeWidget, QTableWidget, QListWidget, QPlainTextEdit, QTextEdit, QGraphicsView {
    background: #ffffff;
    border: 1px solid #c8d2dc;
    alternate-background-color: #f5f8fa;
    selection-background-color: #2c6eaa;
    selection-color: #ffffff;
}
QHeaderView::section {
    background: #e5ebf1;
    padding: 5px;
    border: 0;
    border-right: 1px solid #c8d2dc;
    border-bottom: 1px solid #c8d2dc;
    font-weight: 600;
}
QTabWidget::pane {
    border: 1px solid #c8d2dc;
    background: #ffffff;
}
QTabBar::tab {
    background: #dde5ec;
    padding: 7px 12px;
    border: 1px solid #c8d2dc;
    border-bottom: none;
}
QTabBar::tab:selected { background: #ffffff; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #ffffff;
    border: 1px solid #bfcbd6;
    border-radius: 3px;
    padding: 4px;
}
QPushButton {
    background: #2c6eaa;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 7px 12px;
}
QPushButton:hover { background: #245d91; }
QPushButton:disabled { background: #a8b4bf; }
QGroupBox {
    background: #f8fafc;
    border: 1px solid #c8d2dc;
    border-radius: 5px;
    margin-top: 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QSplitter::handle { background: #cbd5df; }
"""
