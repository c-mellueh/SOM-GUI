from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtGui import QBrush, QPalette, QColor

from som_gui import tool
import SOMcreator
from som_gui.module.compare import ui
import som_gui.core.tool
import som_gui
from PySide6.QtWidgets import QTableWidgetItem, QTreeWidgetItem
from PySide6.QtCore import Qt
from som_gui.module.project.constants import CLASS_REFERENCE
from som_gui.module.compare import trigger
from som_gui.module.compare.prop import COMPARE_SETTING
if TYPE_CHECKING:
    from som_gui.module.compare.prop import CompareProperties

style_list = [
    [None, [0, 1]],
    ["#897e00", [0, 1]],  # Yellow
    ["#006605", [1]],  # green
    ["#840002", [0]]  # red

]

class Compare(som_gui.core.tool.Compare):

    @classmethod
    def get_properties(cls) -> CompareProperties:
        return som_gui.CompareProperties

    @classmethod
    def create_import_dialog(cls):
        dialog = ui.ImportDialog()
        dialog.widget.button.clicked.connect(trigger.project_button_clicked)
        dialog.widget.button_switch.clicked.connect(trigger.switch_button_clicked)
        cls.get_properties().import_dialog = dialog
        cls.get_properties().layout_proj0 = dialog.widget.layout_top
        cls.get_properties().layout_proj1 = dialog.widget.layout_bottom
        cls.get_properties().label_project = dialog.widget.label_project
        cls.get_properties().layout_input = dialog.widget.layout_input

        return dialog

    @classmethod
    def get_import_dialog(cls) -> ui.ImportDialog:
        return cls.get_properties().import_dialog

    @classmethod
    def set_import_dialog_lineedit(cls, project_path: str):
        if project_path:
            cls.get_import_dialog().widget.line_edit.setText(project_path)



    @classmethod
    def set_projects(cls, project1, project2) -> None:
        cls.get_properties().projects = [project1, project2]

    @classmethod
    def get_project(cls, index=1) -> SOMcreator.Project:
        return cls.get_properties().projects[index]

    @classmethod
    def get_uuid_dict(cls, index=1) -> dict:
        uuid_dict = cls.get_properties().uuid_dicts[index]
        project = cls.get_project(index)
        if uuid_dict is None:
            d = {hi.uuid: hi for hi in project.get_all_hirarchy_items()}
            cls.get_properties().uuid_dicts[index] = d
        return cls.get_properties().uuid_dicts[index]

    @classmethod
    def get_ident_dict(cls, index=1) -> dict:
        uuid_dict = cls.get_properties().ident_dicts[index]
        project = cls.get_project(index)
        if uuid_dict is None:
            d = {obj.ident_value: obj for obj in project.get_all_objects()}
            cls.get_properties().ident_dicts[index] = d
        return cls.get_properties().ident_dicts[index]

    @classmethod
    def find_matching_object(cls, obj: SOMcreator.Object, index=1) -> SOMcreator.Object | None:
        uuid_dict = cls.get_uuid_dict(index)
        ident_dict = cls.get_ident_dict(index)

        uuid_match = uuid_dict.get(obj.uuid)
        if uuid_match:
            return uuid_match
        ident_match = ident_dict.get(obj.ident_value)

        if ident_match:
            return ident_match

        return None

    @classmethod
    def find_matching_pset(cls, pset_0, property_set_uuid_dict1,
                           property_set_name_dict1) -> SOMcreator.PropertySet | None:
        if pset_0.uuid in property_set_uuid_dict1:
            return property_set_uuid_dict1[pset_0.uuid]
        if pset_0.name in property_set_name_dict1:
            return property_set_name_dict1[pset_0.name]
        return None

    @classmethod
    def compare_objects(cls, obj0: SOMcreator.Object, obj1: SOMcreator.Object):
        property_set_uuid_dict1 = {p.uuid: p for p in obj1.get_all_property_sets()}
        property_set_name_dict1 = {p.name: p for p in obj1.get_all_property_sets()}
        # ToDo: Edgecase where 1 pset has matching uuid but different pset has same name
        pset_list = list()

        missing_property_sets1 = list(obj1.get_all_property_sets())

        for property_set0 in obj0.get_all_property_sets():
            match = cls.find_matching_pset(property_set0, property_set_uuid_dict1, property_set_name_dict1)
            if match is not None:
                missing_property_sets1.remove(match)
                pset_list.append((property_set0, match))
                cls.compare_psets(property_set0, match)
            else:
                pset_list.append((property_set0, None))

        for property_set1 in missing_property_sets1:
            pset_list.append((None, property_set1))
        cls.get_properties().pset_lists[obj0] = pset_list
        cls.get_properties().pset_lists[obj1] = pset_list

    @classmethod
    def compare_psets(cls, pset0: SOMcreator.PropertySet, pset1: SOMcreator.PropertySet):
        attribute_uuid_dict1 = {a.uuid: a for a in pset1.get_all_attributes()}
        attribute_name_dict1 = {a.name: a for a in pset1.get_all_attributes()}
        missing_attributes1 = list(pset1.get_all_attributes())
        attributes_list = list()
        for attribute0 in pset0.get_all_attributes():
            match = cls.find_matching_pset(attribute0, attribute_uuid_dict1, attribute_name_dict1)
            if match is not None:
                missing_attributes1.remove(match)
                attributes_list.append((attribute0, match))
            else:
                attributes_list.append((attribute0, None))
        for attribute1 in missing_attributes1:
            attributes_list.append((None, attribute1))

        for a1, a2 in attributes_list:
            cls.compare_attributes(a1, a2)

        cls.get_properties().attributes_lists[pset0] = attributes_list
        cls.get_properties().attributes_lists[pset1] = attributes_list

    @classmethod
    def compare_attributes(cls, attribute0: SOMcreator.Attribute, attribute1: SOMcreator.Attribute):
        if attribute0 is not None:
            values0 = set(attribute0.value)
        else:
            values0 = set()
        if attribute1 is not None:
            values1 = set(attribute1.value)
        else:
            values1 = set()

        unique0 = values0.difference(values1)
        main = values0.intersection(values1)
        unique1 = values1.difference(values0)

        value_list = [(v, v) for v in main] + [(v, None) for v in unique0] + [(None, v) for v in unique1]
        if attribute0 is not None:
            cls.get_properties().values_lists[attribute0] = value_list
        if attribute1 is not None:
            cls.get_properties().values_lists[attribute1] = value_list

    @classmethod
    def create_object_dicts(cls):
        project_0 = cls.get_project(0)
        project_1 = cls.get_project(1)
        missing_objects_0 = list()
        missing_objects_1 = list(project_1.get_all_objects())
        object_dict0 = dict()
        object_dict1 = dict()
        for obj in project_0.get_all_objects():
            match = cls.find_matching_object(obj, 1)
            if match is not None:
                object_dict0[obj] = match
                object_dict1[match] = obj
                missing_objects_1.remove(match)
                cls.compare_objects(obj, match)
            else:
                object_dict0[obj] = None
                missing_objects_0.append(obj)
        for obj in missing_objects_1:
            object_dict1[obj] = None
        cls.get_properties().missing_objects = [missing_objects_0, missing_objects_1]
        cls.get_properties().object_dicts = [object_dict0, object_dict1]

    @classmethod
    def create_window(cls):
        cls.get_properties().window = ui.CompareDialog()
        return cls.get_window()

    @classmethod
    def get_window(cls) -> ui.CompareDialog:
        return cls.get_properties().window

    @classmethod
    def get_object_dict(cls, index=1) -> dict:
        return cls.get_properties().object_dicts[index]

    @classmethod
    def get_missing_objects(cls, index=1) -> list:
        return cls.get_properties().missing_objects[index]

    @classmethod
    def add_object_to_item(cls, obj: SOMcreator.Object, item: QTreeWidgetItem, index: int):

        start_index = index
        ident_text = f"({obj.ident_value})" if obj.ident_value else ""
        text = f"{obj.name} {ident_text}"
        item.setText(start_index, text)
        item.setData(start_index, CLASS_REFERENCE, obj)
        cls.get_properties().object_tree_item_dict[obj] = item

    @classmethod
    def fill_object_tree_layer(cls, objects: list[SOMcreator.Object], parent_item: QTreeWidgetItem):
        obj_dict0, obj_dict1 = cls.get_object_dict(0), cls.get_object_dict(1)

        for obj in objects:
            match_obj = obj_dict0.get(obj)
            item = QTreeWidgetItem()
            cls.add_object_to_item(obj, item, 0)
            if match_obj:
                cls.add_object_to_item(match_obj, item, 1)
            parent_item.addChild(item)
            cls.fill_object_tree_layer(list(obj.children), item)

    @classmethod
    def find_existing_parent(cls, obj: SOMcreator.Object):
        tree = cls.get_window().widget.tree_widget_object
        object_tree_item_dict = cls.get_properties().object_tree_item_dict
        parent = obj.parent
        while parent is not None:
            if parent in object_tree_item_dict:
                return object_tree_item_dict[parent]
            parent = parent.parent
        return tree.invisibleRootItem()

    @classmethod
    def add_missing_objects_to_tree(cls, root_objects: list[SOMcreator.Object]):
        missing_objects = cls.get_missing_objects(1)
        for obj in root_objects:
            if obj in missing_objects:
                parent = cls.find_existing_parent(obj)
                item = QTreeWidgetItem()
                cls.add_object_to_item(obj, item, 1)
                parent.addChild(item)
            cls.add_missing_objects_to_tree(list(obj.children))

    @classmethod
    def fill_object_tree(cls):
        tree = cls.get_window().widget.tree_widget_object
        proj0, proj1 = cls.get_project(0), cls.get_project(1)
        cls.fill_object_tree_layer(tool.Project.get_root_objects(False, proj0), tree.invisibleRootItem())
        cls.add_missing_objects_to_tree(tool.Project.get_root_objects(False, proj1))

    @classmethod
    def create_triggers(cls, window: ui.CompareDialog):
        window.widget.tree_widget_object.itemSelectionChanged.connect(trigger.object_tree_selection_changed)
        window.widget.tree_widget_propertysets.itemSelectionChanged.connect(trigger.pset_tree_selection_changed)

    @classmethod
    def get_pset_tree(cls):
        return cls.get_window().widget.tree_widget_propertysets

    @classmethod
    def fill_pset_table(cls, obj: SOMcreator.Object):

        pset_list = cls.get_properties().pset_lists.get(obj)
        tree = cls.get_pset_tree()
        root = tree.invisibleRootItem()
        for child_index in reversed(range(tree.invisibleRootItem().childCount())):
            root.removeChild(root.child(child_index))

        if pset_list is None:
            return

        for pset0, pset1 in pset_list:
            item = QTreeWidgetItem()
            root.addChild(item)
            if pset0:
                item.setText(0, pset0.name)
                item.setData(0, CLASS_REFERENCE, pset0)
            if pset1:
                item.setText(1, pset1.name)
                item.setData(1, CLASS_REFERENCE, pset1)

            cls.add_attribute_to_psetitem(item)

    @classmethod
    def add_attribute_to_psetitem(cls, pset_item: QTreeWidgetItem):
        pset0 = pset_item.data(0, CLASS_REFERENCE)
        pset1 = pset_item.data(1, CLASS_REFERENCE)

        if pset0 is not None and pset1 is None:
            attribute_list = [(a, None) for a in pset0.get_all_attributes()]
        elif pset1 is not None and pset0 is None:
            attribute_list = [(None, a) for a in pset1.get_all_attributes()]
        else:
            attribute_list = cls.get_properties().attributes_lists.get(pset0)
        print(attribute_list)
        if attribute_list is None:
            return

        for attribute0, attribute1 in attribute_list:
            item = QTreeWidgetItem()
            pset_item.addChild(item)
            if attribute0:
                item.setText(0, attribute0.name)
                item.setData(0, CLASS_REFERENCE, attribute0)
            if attribute1:
                item.setText(1, attribute1.name)
                item.setData(1, CLASS_REFERENCE, attribute1)

    @classmethod
    def get_object_tree(cls):
        return cls.get_window().widget.tree_widget_object

    @classmethod
    def get_selected_object(cls) -> SOMcreator.Object | None:
        item = cls.get_object_tree().selectedItems()[0]
        data = item.data(0, CLASS_REFERENCE)
        if data is None:
            data = item.data(1, CLASS_REFERENCE)
        return data

    @classmethod
    def get_selected_pset(cls) -> SOMcreator.PropertySet | SOMcreator.Attribute | None:
        selected_items = cls.get_pset_tree().selectedItems()
        if not selected_items:
            return None
        item = selected_items[0]
        data = item.data(0, CLASS_REFERENCE)
        if data is None:
            data = item.data(1, CLASS_REFERENCE)
        return data

    @classmethod
    def get_value_table(cls):
        return cls.get_window().widget.table_widget_values

    @classmethod
    def fill_value_table(cls, attribute: SOMcreator.Attribute):

        value_list = cls.get_properties().values_lists.get(attribute)
        table = cls.get_value_table()
        table.setRowCount(0)

        if value_list is None:
            return

        for value0, value1 in value_list:
            item0 = QTableWidgetItem()
            item1 = QTableWidgetItem()

            if value0 is not None:
                item0.setText(value0)

            if value1 is not None:
                item1.setText(value1)

            table.insertRow(table.rowCount())
            table.setItem(table.rowCount() - 1, 0, item0)
            table.setItem(table.rowCount() - 1, 1, item1)

    @classmethod
    def attributes_are_identical(cls, attribute0: SOMcreator.Attribute, attribute1: SOMcreator.Attribute):
        if attribute0 is None or attribute1 is None:
            return False
        values = set(attribute0.value) == set(attribute1.value)
        data_types = attribute0.data_type == attribute1.data_type
        value_types = attribute0.value_type == attribute1.value_type
        names = attribute0.name == attribute1.name
        return all((values, data_types, value_types, names))

    @classmethod
    def property_sets_are_identical(cls, property_set0: SOMcreator.PropertySet, property_set1: SOMcreator.PropertySet):
        if property_set0 is None or property_set1 is None:
            return False
        names = property_set0.name == property_set1.name
        attribute_list = cls.get_properties().attributes_lists.get(property_set0)
        if not attribute_list:
            return False
        attributes_are_matching = all(cls.attributes_are_identical(a0, a1) for a0, a1 in attribute_list)
        return all((names, attributes_are_matching))

    @classmethod
    def objects_are_identical(cls, object0: SOMcreator.Object, object1: SOMcreator.Object):
        if object0 is None or object1 is None:
            return
        names = object0.name == object1.name
        identifier = object0.ident_value == object1.ident_value
        property_set_list = cls.get_properties().pset_lists.get(object0)
        if not property_set_list:
            return False
        psets_are_matching = all(cls.property_sets_are_identical(p0, p1) for p0, p1 in property_set_list)
        return all((names, identifier, psets_are_matching))

    @classmethod
    def set_tree_row_color(cls, item: QTreeWidgetItem, style_index):
        item.setData(0, CLASS_REFERENCE + 1, style_index)
        color, column_list = style_list[style_index]
        for column in column_list:
            brush = QBrush(QColor(color)) if color is not None else QPalette().base()
            item.setBackground(column, brush)

    @classmethod
    def style_parent_item(cls, item: QTreeWidgetItem, style: int):
        parent = item.parent()
        if parent is None or parent == item.treeWidget().invisibleRootItem():
            return
        parent_style_index = parent.data(0, CLASS_REFERENCE + 1)
        if parent_style_index < style:
            cls.set_tree_row_color(parent, style)
            cls.style_parent_item(parent, style)



    @classmethod
    def style_object_tree_item(cls, item: QTreeWidgetItem):
        obj0 = item.data(0, CLASS_REFERENCE)
        obj1 = item.data(1, CLASS_REFERENCE)

        if obj0 is None:
            style = 2


        elif obj1 is None:
            style = 3

        else:
            if isinstance(obj0, SOMcreator.Object):
                compare_func = cls.objects_are_identical
            elif isinstance(obj0, SOMcreator.PropertySet):
                compare_func = cls.property_sets_are_identical
            else:
                compare_func = cls.attributes_are_identical

            style = 0 if compare_func(obj0, obj1) else 1

        cls.set_tree_row_color(item, style)
        if isinstance(obj0, SOMcreator.Object) or isinstance(obj1, SOMcreator.Object):
            cls.style_parent_item(item, style)

        for child_index in range(item.childCount()):
            if not isinstance(obj0, SOMcreator.Attribute):
                cls.style_object_tree_item(item.child(child_index))

    @classmethod
    def set_header_labels(cls, h0: str, h1: str):
        cls.get_object_tree().setHeaderLabels([h0, h1])
        cls.get_pset_tree().setHeaderLabels([h0, h1])
        cls.get_value_table().setHorizontalHeaderLabels([h0, h1])

    @classmethod
    def header_name(cls, project: SOMcreator.Project):
        return f"{project.name} v{project.version}"