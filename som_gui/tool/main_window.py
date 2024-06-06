from __future__ import annotations
import som_gui.core.tool
import som_gui
from typing import TYPE_CHECKING, Callable
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar, QApplication, QLabel
from som_gui import tool

if TYPE_CHECKING:
    from som_gui.module.main_window.prop import MainWindowProperties, MenuDict
    from som_gui.tool.object import ObjectDataDict
    from som_gui.main_window import Ui_MainWindow


class MainWindow(som_gui.core.tool.MainWindow):
    @classmethod
    def set_window_title(cls, title: str):
        cls.get().setWindowTitle(title)

    @classmethod
    def create_status_label(cls):
        label = QLabel()
        prop = cls.get_main_menu_properties()
        prop.status_bar_label = label
        cls.get_ui().statusbar.addWidget(label)

    @classmethod
    def set_status_bar_text(cls, text: str):
        cls.get_main_menu_properties().status_bar_label.setText(text)

    @classmethod
    def get_menu_bar(cls) -> QMenuBar:
        return cls.get_ui().menubar

    @classmethod
    def get_menu_dict(cls) -> MenuDict:
        prop = cls.get_main_menu_properties()
        return prop.menu_dict


    @classmethod
    def get_main_menu_properties(cls) -> MainWindowProperties:
        return som_gui.MainWindowProperties

    @classmethod
    def get_ui(cls) -> Ui_MainWindow:
        return cls.get_main_menu_properties().ui

    @classmethod
    def get(cls) -> som_gui.MainWindow:
        return cls.get_main_menu_properties().window

    @classmethod
    def get_app(cls) -> QApplication:
        return som_gui.MainUi.window.app

    @classmethod
    def set(cls, window):
        prop = cls.get_main_menu_properties()
        prop.window = window
        prop.ui = window.ui

    @classmethod
    def get_object_infos(cls) -> ObjectDataDict:
        ui = cls.get_ui()
        d: ObjectDataDict = dict()
        d["name"] = ui.line_edit_object_name.text()
        d["is_group"] = False
        d["ident_pset_name"] = ui.lineEdit_ident_pSet.text()
        d["ident_attribute_name"] = ui.lineEdit_ident_attribute.text()
        d["ident_value"] = ui.lineEdit_ident_value.text()
        d["ifc_mappings"] = ["IfcBuildingElementProxy"]
        d["abbreviation"] = ui.line_edit_abbreviation.text()
        return d

    @classmethod
    def get_pset_name(cls):
        return cls.get_ui().lineEdit_pSet_name.text()
