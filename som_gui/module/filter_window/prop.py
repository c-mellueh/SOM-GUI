from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt
import SOMcreator

if TYPE_CHECKING:
    from . import ui
    from som_gui.module.attribute.ui import AttributeWidget

class FilterWindowProperties:
    widget: ui.FilterWidget = None
    active_object: SOMcreator.Object = None
    tree_is_clicked = False
    active_check_state: Qt.CheckState = None
    settings_widget: ui.SettingsWidget = None


class FilterCompareProperties:
    widget: AttributeWidget = None
    usecase_list = list()
    use_case_indexes = list()
    phase_list = list()
    phase_indexes = list()
    projects = [None, None]
    match_list = []
