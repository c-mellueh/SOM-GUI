from __future__ import annotations
from PySide6.QtCore import Qt,QPointF
from PySide6.QtWidgets import QTableWidgetItem, QListWidgetItem, QAbstractScrollArea,QMenu,QCompleter,QWidget

from desiteRuleCreator.QtDesigns import ui_mainwindow
from desiteRuleCreator.Windows import popups,propertyset_window
from desiteRuleCreator.Windows.popups import msg_del_ident_pset, msg_del_items
from desiteRuleCreator.Windows.propertyset_window import PropertySetWindow
from desiteRuleCreator.data import custom_qt
from SOMcreator import classes, constants
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from desiteRuleCreator.main_window import MainWindow

class MappingTableItem(QTableWidgetItem):
    def __init__(self,property_set:classes.PropertySet) -> None:
        super(MappingTableItem, self).__init__()
        self.property_set = property_set
        self.update()
    def update(self) -> None:
        self.setText(";".join(self.property_set.ifc_mapping))


def get_parent_by_name(active_object: classes.Object, name: str) -> classes.PropertySet|None:
    """find Propertyset which has the same name and is not from the same object"""


    for pset in classes.PropertySet:
        is_master = pset.parent is None
        correct_name = pset.name == name
        if active_object is not None:
            is_same_obj = pset.object == active_object
        else:
            is_same_obj = False

        if is_master and correct_name and not is_same_obj:
            return pset


def init(main_window:MainWindow) -> None:
    def connect() -> None:
        main_window.pset_table.itemClicked.connect(main_window.list_object_clicked)
        main_window.pset_table.itemDoubleClicked.connect(main_window.list_object_double_clicked)
        main_window.ui.table_attribute.itemDoubleClicked.connect(main_window.attribute_double_clicked)
        main_window.ui.lineEdit_pSet_name.textChanged.connect(main_window.text_changed)
        main_window.pset_table.customContextMenuRequested.connect(main_window.open_pset_menu)
        main_window.ui.button_Pset_add.clicked.connect(main_window.add_pset)

    main_window.pset_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
    main_window.pset_buttons = [main_window.ui.button_Pset_add,]
    main_window.ui.tab_property_set.setEnabled(False)
    main_window.set_right_window_enable(False)
    connect()

def open_menu(main_window:MainWindow, position:QPointF) -> None:
    menu = QMenu()
    main_window.action_pset_delete_attribute = menu.addAction("Delete")
    main_window.action_pset_rename_attribute = menu.addAction("Rename")
    main_window.action_pset_delete_attribute.triggered.connect(main_window.delete_pset)
    main_window.action_pset_rename_attribute.triggered.connect(main_window.rename_pset)
    menu.exec(main_window.pset_table.viewport().mapToGlobal(position))


def predefined_pset_list(main_window:MainWindow) -> set[str]:
    def iterate_parents(parent:classes.Object) -> None:
        if parent is not None:
            for property_set in parent.property_sets:
                property_list.add(property_set.name)
            iterate_parents(parent.parent)

    property_list = {pset.name for pset in classes.PropertySet if pset.object is None}

    if main_window.active_object is not None:
        iterate_parents(main_window.active_object.parent)
        completer = QCompleter(property_list)
        main_window.ui.lineEdit_pSet_name.setCompleter(completer)
    return property_list


def modify_title(main_window:MainWindow, tab:QWidget, text:str=None) -> None:
    main_window.ui.tabWidget.setTabText(main_window.ui.tabWidget.indexOf(tab), text)


def clear_all(main_window:MainWindow) -> None:
    ui: ui_mainwindow.Ui_MainWindow = main_window.ui
    for row in range(main_window.pset_table.rowCount()):
        main_window.pset_table.removeRow(row)

    for row in range(ui.table_attribute.rowCount()):
        ui.table_attribute.removeRow(row)

    main_window.ui.lineEdit_pSet_name.clear()
    main_window.set_right_window_enable(False)
    modify_title(main_window, main_window.ui.tab_code, "Code")
    modify_title(main_window, main_window.ui.tab_property_set, "PropertySet")


def delete_selection(main_window:MainWindow) -> None:
    list_item:list[custom_qt.CustomTableItem] = main_window.pset_table.selectedItems()
    property_sets:list[classes.PropertySet] = [item.linked_data for item in list_item if item.column() == 0]
    row_list = [item.row() for item in list_item if item.column() ==0]


    obj = main_window.active_object
    delete_request = msg_del_items([pset.name for pset in property_sets])

    if not delete_request:
        return

    if obj.ident_attrib.property_set in property_sets:
        msg_del_ident_pset()
        return

    for property_set in property_sets:
        if property_set.is_child:
            property_set.parent.remove_child(property_set)
        else:
            property_set.delete()

    for i in sorted(row_list,reverse=True):
        main_window.pset_table.removeRow(i)


def rename(main_window:MainWindow) -> None:
    list_item:custom_qt.CustomTableItem = main_window.pset_table.selectedItems()[0]
    selected_pset: classes.PropertySet = list_item.linked_data
    return_str = popups.req_new_name(main_window,selected_pset.name)

    if return_str[1]:
        new_name = return_str[0]
        if new_name in [pset.name for pset in main_window.active_object.property_sets]:
            popups.msg_already_exists()
            return
        list_item.setText(new_name)
        main_window.pset_table.resizeColumnsToContents()
        selected_pset.name = new_name
        main_window.reload_objects()


def text_changed(main_window:MainWindow,text:str) -> None:
    """if name of pset allready exists -> disable add button"""
    if main_window.pset_table.findItems(text, Qt.MatchFlag.MatchExactly):
        main_window.ui.button_Pset_add.setEnabled(False)
    else:
        main_window.ui.button_Pset_add.setEnabled(True)

def set_enable(main_window:MainWindow, value: bool) -> None:
    main_window.ui.tab_property_set.setEnabled(value)

    if not value:
        modify_title(main_window, main_window.ui.tab_code, "Code")
        modify_title(main_window, main_window.ui.tab_property_set, "PropertySet")

        main_window.pset_table.setRowCount(0)
        main_window.ui.table_attribute.setRowCount(0)
        main_window.ui.lineEdit_pSet_name.setText("")


def fill_table(main_window:MainWindow, obj: classes.Object) -> None:

    main_window.set_right_window_enable(True)
    modify_title(main_window, main_window.ui.tab_code, f"{obj.name}: Code")
    modify_title(main_window, main_window.ui.tab_property_set, f"{obj.name}: PropertySets")

    main_window.pset_table.setRowCount(0)
    property_sets = main_window.active_object.property_sets

    # find inherited Psets

    main_window.pset_table.setRowCount(len(property_sets))  # Prepare Table

    for i, pset in enumerate(property_sets):
        table_item = custom_qt.CustomTableItem(pset)
        main_window.pset_table.setItem(i, 0, table_item)
        if pset.is_child:
            if pset.parent.object is not None:
                table_item = QTableWidgetItem(pset.parent.object.name)
            else:
                table_item = QTableWidgetItem(constants.INHERITED_TEXT)
            main_window.pset_table.setItem(i, 1, table_item)

    main_window.pset_table.resizeColumnsToContents()


def left_click(main_window:MainWindow, item: QListWidgetItem) -> None:

    item:custom_qt.CustomTableItem = main_window.pset_table.item(
                                    main_window.pset_table.row(item), 0)

    property_set: classes.PropertySet = item.linked_data
    propertyset_window.fill_attribute_table(main_window.active_object, main_window.ui.table_attribute, property_set)
    main_window.ui.lineEdit_pSet_name.setText(property_set.name)

def attribute_double_click(main_window:MainWindow,item:custom_qt.CustomTableItem) -> None:
    item: custom_qt.CustomTableItem = item.tableWidget().item(item.row(), 0)
    attribute:classes.Attribute = item.linked_data
    property_set = attribute.property_set
    main_window.open_pset_window(property_set, main_window.active_object, None)
    main_window.pset_window.table_clicked(item)


def double_click(main_window:MainWindow, item: QTableWidgetItem) -> None:
    main_window.list_object_clicked(item)
    item:custom_qt.CustomTableItem = main_window.pset_table.item(item.row(), 0)
    property_set: classes.PropertySet = item.linked_data

    # Open New Window
    main_window.open_pset_window(property_set, main_window.active_object, None)


def open_pset_window(main_window:MainWindow, property_set: classes.PropertySet,
                     active_object: classes.Object, window_title=None,) -> None:

    if window_title is None:
        window_title = f"{property_set.object.name}:{property_set.name}"

    window = PropertySetWindow(main_window, property_set, active_object, window_title)
    main_window.pset_window = window


def add_pset(main_window:MainWindow) -> None:
    name = main_window.ui.lineEdit_pSet_name.text()
    obj = main_window.active_object

    new_row_count = main_window.pset_table.rowCount() + 1
    main_window.pset_table.setRowCount(new_row_count)

    inherited = False
    if name in predefined_pset_list(main_window):
        inherited = popups.req_merge_pset()

    if inherited:
        parent = get_parent_by_name(main_window.active_object, name)
        property_set = parent.create_child(name)

        if parent.object is not None:
            item2 = QTableWidgetItem(parent.object.name)
        else:
            item2 = QTableWidgetItem(constants.INHERITED_TEXT)
        main_window.pset_table.setItem(new_row_count-1, 1, item2)

    else:
        property_set = classes.PropertySet(name)

    obj.add_property_set(property_set)
    item = custom_qt.CustomTableItem(property_set)

    main_window.pset_table.setItem(new_row_count - 1, 0, item)
    main_window.text_changed(main_window.ui.lineEdit_pSet_name.text())
    main_window.pset_table.resizeColumnsToContents()


def reload(main_window:MainWindow) -> None:
    if main_window.active_object is not None:
        fill_table(main_window, main_window.active_object)
        propertyset_window.fill_attribute_table(main_window.active_object, main_window.ui.table_attribute, main_window.pset_window.property_set)


def clear_attribute_table(main_window:MainWindow) -> None:
    ui: ui_mainwindow.Ui_MainWindow = main_window.ui
    table_widget = ui.table_attribute
    table_widget.setRowCount(0)