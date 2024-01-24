from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit, QDialog, QListWidgetItem, QCompleter
from SOMcreator import classes

from .. import icons
from ..icons import get_icon
from ..qt_designs import ui_delete_request, ui_attribute_mapping


def msg_close():
    icon = icons.get_icon()
    text = "Möchten Sie ihr Projekt vor dem Verlassen speichern?"
    msg_box = QMessageBox(QMessageBox.Icon.Warning,
                          "Message",
                          text,
                          QMessageBox.StandardButton.Cancel |
                          QMessageBox.StandardButton.Save |
                          QMessageBox.StandardButton.No)

    msg_box.setWindowIcon(icon)
    reply = msg_box.exec()
    return reply


def msg_del_items(string_list, item_type=1) -> (bool, bool):
    """
    item_type 1= Object,2= Node, 3 = PropertySet, 4 = Attribute
    """
    parent = QDialog()
    widget = ui_delete_request.Ui_Dialog()
    widget.setupUi(parent)
    parent.setWindowIcon(get_icon())
    if len(string_list) <= 1:
        if item_type == 1:
            widget.label.setText("Dieses Objekt löschen?")
        if item_type == 2:
            widget.label.setText("Diese Node löschen?")
        if item_type == 3:
            widget.label.setText("Dieses PropertySet löschen?")
        if item_type == 4:
            widget.label.setText("Dieses Attribut löschen?")
    else:
        if item_type == 1:
            widget.label.setText("Diese Objekte löschen?")
        if item_type == 2:
            widget.label.setText("Diese Nodes öschen?")
        if item_type == 3:
            widget.label.setText("Diese PropertySets löschen?")
        if item_type == 4:
            widget.label.setText("Diese Attribute löschen?")

    for text in string_list:
        widget.listWidget.addItem(QListWidgetItem(text))
    result = parent.exec()
    check_box_state = True if widget.check_box_recursion.checkState() == Qt.CheckState.Checked else False
    return bool(result), check_box_state


def req_boq_pset(main_window, words):
    input_dialog = QInputDialog(main_window)
    input_dialog.setWindowTitle("Bill of Quantities")
    input_dialog.setLabelText("BoQ PropertySet Name")
    input_dialog.setTextValue("BoQ")
    line_edit: QLineEdit = input_dialog.findChild(QLineEdit)

    completer = QCompleter(words)
    line_edit.setCompleter(completer)
    ok = input_dialog.exec()
    if ok == 1:
        return True, input_dialog.textValue()
    else:
        return False, None


def attribute_mapping(attribute: classes.Attribute):
    parent = QDialog()
    widget = ui_attribute_mapping.Ui_Dialog()
    parent.setWindowIcon(get_icon())
    widget.setupUi(parent)
    widget.label_name.setText(f"RevitMapping {attribute.name}")
    widget.line_edit_revit_mapping.setText(attribute.revit_name)

    if parent.exec():
        attribute.revit_name = widget.line_edit_revit_mapping.text()


def req_export_pset_name(main_window):
    return QInputDialog.getText(main_window, "PropertySet name", "What's the name of the Export PropertySet?")
