from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TypedDict

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu

if TYPE_CHECKING:
    from som_gui.module.main_window.ui import MainWindow
    from som_gui.module.main_window.qt.ui_MainWindow import Ui_MainWindow

class MainWindowProperties:
    ui: Ui_MainWindow | None = None
    window: MainWindow = None
    application: QApplication = None
    actions: dict[str, QAction] = dict()
