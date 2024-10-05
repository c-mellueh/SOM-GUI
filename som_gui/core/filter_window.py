from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Type
import SOMcreator
from PySide6.QtCore import Qt, QItemSelection
if TYPE_CHECKING:
    from som_gui import tool


def open_window(filter_window: Type[tool.FilterWindow], project: Type[tool.Project]):
    widget = filter_window.create_widget()
    filter_window.connect_project_table(project.get())
    filter_window.connect_object_tree(project.get())
    filter_window.connect_pset_tree(project.get())
    widget.show()

def pt_context_menu(local_pos, orientation: int, filter_window: Type[tool.FilterWindow], project: Type[tool.Project]):
    proj = project.get()

    menu_list = list()
    table = filter_window.get_project_table()
    if orientation == Qt.Orientation.Horizontal:  # use_case
        index = table.horizontalHeader().logicalIndexAt(local_pos)
        usecase = proj.get_usecase_by_index(index)
        if len(proj.get_usecases()) > 1:
            menu_list.append(("Anwendungsfall löschen", lambda: filter_window.remove_usecase(usecase, proj)))
        menu_list.append(("Anwendungsfall umbenennen", lambda: filter_window.rename_filter(usecase)))
        menu_list.append(("Anwendungsfall hinzufügen", lambda: filter_window.add_usecase(proj)))
        pos = table.horizontalHeader().viewport().mapToGlobal(local_pos)

    else:
        index = table.verticalHeader().logicalIndexAt(local_pos)
        phase = proj.get_phase_by_index(index)
        if len(proj.get_phases()) > 1:
            menu_list.append(("Leistungsphase löschen", lambda: filter_window.remove_phase(phase, proj)))
        menu_list.append(("Leistungsphase umbenennen", lambda: filter_window.rename_filter(phase)))
        menu_list.append(("Leistungsphase hinzufügen", lambda: filter_window.add_phase(proj)))
        pos = table.horizontalHeader().viewport().mapToGlobal(local_pos)

    filter_window.create_context_menu(menu_list, pos)


def update_object_tree(filter_window: Type[tool.FilterWindow]):
    filter_window.get_object_tree().model().update()


def object_tree_selection_changed(selected: QItemSelection, filter_window: Type[tool.FilterWindow]):
    indexes = selected.indexes()
    if len(indexes) == 0:
        return
    index = indexes[0]
    obj: SOMcreator.Object = index.internalPointer()
    filter_window.set_active_object(obj)
    filter_window.set_object_label(obj.name)
    update_pset_tree(filter_window)


def update_pset_tree(filter_window: Type[tool.FilterWindow]):
    filter_window.get_pset_tree().model().update()
