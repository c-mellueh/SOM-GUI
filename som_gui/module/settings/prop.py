from __future__ import annotations
from PySide6.QtWidgets import QWidget, QToolBox
from PySide6.QtGui import QAction
from typing import Callable, TYPE_CHECKING, Type
if TYPE_CHECKING:
    from . import ui
class SettingsProperties:
    page_dict: dict[str, list[Type[QWidget]]] = dict()  # dict[pageName,list[Widget]]
    tab_widget_dict: dict[str, tuple[QToolBox, dict[str, QWidget]]] = dict()
    accept_functions: list[Callable] = list()
    widget: ui.Dialog = None
    actions: dict[str, QAction] = dict()
