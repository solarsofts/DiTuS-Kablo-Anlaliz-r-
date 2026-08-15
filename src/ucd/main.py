from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QTimer
from PySide6.QtWidgets import QApplication

from ucd import __version__
from ucd.ui.main_window import MainWindow
from ucd.ui.theme import APP_STYLE
from ucd.ui.window_layout import install_responsive_window_manager


def main() -> int:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv)
    app.setApplicationName("DiTuS Kablo Analizör")
    app.setOrganizationName("DiTuS Engineering")
    app.setApplicationVersion(__version__)
    QLocale.setDefault(QLocale(QLocale.Turkish, QLocale.Turkey))
    app.setStyleSheet(APP_STYLE)
    install_responsive_window_manager(app)

    window = MainWindow(project_root=Path(__file__).resolve().parents[2])
    window.show()
    QTimer.singleShot(0, window.show_start_dialog)
    return app.exec()
