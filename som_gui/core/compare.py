from __future__ import annotations
from typing import TYPE_CHECKING, Type

import SOMcreator
from SOMcreator import Project

if TYPE_CHECKING:
    from som_gui import tool
    from PySide6.QtWidgets import QTreeWidgetItem

def test(compare: Type[tool.Compare], project: Type[tool.Project]):
    other_file_path = "C:/Users/ChristophMellueh/Deutsche Bahn/INI-SW-M - BIM/AIA/SOM/Projekte/Mannheim/24-06-26_ACHS_0000_uebGeo_UE_UE_BAP_0_U_DBN_SOM_001.SOMjson"  # "C:/Users/ChristophMellueh/Desktop/test_som.SOMjson"
    project_0 = project.get()
    project_1 = Project.open(other_file_path)
    compare.set_projects(project_0, project_1)
    compare.create_object_dicts()
    window = compare.create_window()
    compare.fill_object_tree()
    root = compare.get_object_tree().invisibleRootItem()

    for child_index in range(root.childCount()):
        compare.style_object_tree_item(root.child(child_index))

    compare.set_header_labels(compare.header_name(project_0), compare.header_name(project_1))

    compare.create_triggers(window)
    window.exec()


def object_tree_selection_changed(compare: Type[tool.Compare]):
    obj = compare.get_selected_object()
    compare.fill_pset_table(obj)
    root = compare.get_pset_tree().invisibleRootItem()

    for child_index in range(root.childCount()):
        compare.style_object_tree_item(root.child(child_index))


def pset_tree_selection_changed(compare: Type[tool.Compare]):
    attribute = compare.get_selected_pset()
    compare.fill_value_table(attribute)
