import som_gui

import logging
import os
import sys
from logging import config

from som_gui import core
from som_gui import tool
import ifcopenshell.guid
import ifcopenshell.express
from som_gui.translate import rc_som_gui

def main(initial_file: str | None = None, log_level=None, open_last_project=False):

    print("START")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTranslator, QLocale, QLibraryInfo
    import som_gui.core.main_window
    import som_gui.core.project
    from som_gui.module.project.constants import OPEN_PATH
    if log_level is not None:
        tool.Logging.set_log_level(log_level)

    app = QApplication(sys.argv)

    path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    translator = QTranslator(app)
    if translator.load(QLocale.system(), 'qtbase', '_', path):
        app.installTranslator(translator)
    translator = QTranslator(app)
    path = ':/translations'
    if translator.load("QLocale.system(), 'translation', '_', path"):
        app.installTranslator(translator)

    som_gui.register()
    core.main_window.create_main_window(app, tool.MainWindow)
    som_gui.load_ui_triggers()
    core.project.create_project(tool.Project)
    core.main_window.create_menus(tool.MainWindow, tool.Util)
    if initial_file is not None:
        core.project.open_project(initial_file, tool.Project)
    if open_last_project:
        core.project.open_project(tool.Appdata.get_path(OPEN_PATH), tool.Project)
    som_gui.retranslate_ui()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
