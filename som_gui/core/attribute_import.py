from __future__ import annotations
from typing import Type, TYPE_CHECKING
import os
import logging
import ifcopenshell
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from som_gui import tool
    from som_gui.tool.ifc_importer import IfcImportRunner
import time


def open_import_window(attribute_import: Type[tool.AttributeImport], ifc_importer: Type[tool.IfcImporter]):
    if attribute_import.is_window_allready_build():
        attribute_import.get_attribute_widget().show()
        return

    window = attribute_import.create_window()
    ifc_import_widget = ifc_importer.create_importer()
    attribute_import.add_ifc_importer_to_window(ifc_import_widget)
    attribute_import.connect_import_buttons()
    window.show()


def open_results_window(attribute_import: Type[tool.AttributeImport]):
    attribute_import_widget = attribute_import.create_import_widget()
    attribute_import.connect_update_trigger(attribute_import_widget)
    attribute_import_widget.show()


def update_results_window(attribute_import: Type[tool.AttributeImport],
                          attribute_import_sql: Type[tool.AttributeImportSQL]):
    widget = attribute_import.get_attribute_widget().widget
    widget.combo_box_name.repaint()
    widget.combo_box_group.repaint()
    paint_property_set_table(attribute_import, attribute_import_sql)
    widget.label_object_count.repaint()


def update_ifctype_combobox(attribute_import: Type[tool.AttributeImport],
                            attribute_import_sql: Type[tool.AttributeImportSQL], project: Type[tool.Project]):
    combobox = attribute_import.get_ifctype_combo_box()
    wanted_ifc_types = set(attribute_import_sql.get_wanted_ifc_types())
    wanted_ifc_types.add(attribute_import.get_all_keyword())
    attribute_import.update_combobox(combobox, wanted_ifc_types)
    update_somtype_combobox(attribute_import, attribute_import_sql, project)


def update_somtype_combobox(attribute_import: Type[tool.AttributeImport],
                            attribute_import_sql: Type[tool.AttributeImportSQL], project: Type[tool.Project]):
    combobox = attribute_import.get_somtype_combo_box()
    ifc_type = attribute_import.get_ifctype_combo_box().currentText()
    object_list = list(project.get().get_all_objects())

    wanted_som_types = set(attribute_import_sql.get_identifier_types(ifc_type, attribute_import.get_all_keyword()))
    attribute_import.update_som_combobox(combobox, wanted_som_types, object_list)


def run_clicked(attribute_import: Type[tool.AttributeImport], ifc_importer: Type[tool.IfcImporter],
                attribute_import_sql: Type[tool.AttributeImportSQL], project: Type[tool.Project],
                util: Type[tool.Util]):
    ifc_import_widget = attribute_import.get_ifc_import_widget()
    ifc_paths = ifc_importer.get_ifc_paths(ifc_import_widget)
    main_pset_name = ifc_importer.get_main_pset(ifc_import_widget)
    main_attribute_name = ifc_importer.get_main_attribute(ifc_import_widget)

    if not ifc_importer.check_inputs(ifc_paths, main_pset_name, main_attribute_name):
        return

    attribute_import.reset_abort()

    ifc_importer.set_run_button_enabled(ifc_import_widget, False)
    ifc_importer.set_close_button_text(ifc_import_widget, "Abbrechen")
    attribute_import.set_main_pset(main_pset_name)
    attribute_import.set_main_attribute(main_attribute_name)
    pool = ifc_importer.create_thread_pool()
    pool.setMaxThreadCount(3)
    ifc_importer.set_progressbar_visible(ifc_import_widget, True)
    ifc_importer.set_progress(ifc_import_widget, 0)
    sql_init_database(attribute_import, attribute_import_sql, project, util)
    for path in ifc_paths:
        ifc_importer.set_status(ifc_import_widget, f"Import '{os.path.basename(path)}'")
        runner = attribute_import.create_import_runner(path)
        attribute_import.connect_ifc_import_runner(runner)
        pool.start(runner)


def sql_init_database(attribute_import: Type[tool.AttributeImport], attribute_import_sql: Type[tool.AttributeImportSQL],
                      project: Type[tool.Project], util: Type[tool.Util]):
    proj = project.get()
    db_path = util.create_tempfile(".db")
    attribute_import_sql.init_database(db_path)
    all_attributes = list(proj.get_all_attributes())
    attribute_count = len(all_attributes)
    attribute_import_sql.connect_to_data_base(db_path)
    status_text = "Attribute aus SOM importieren:"

    for index, attribute in enumerate(all_attributes):
        if index % 100 == 0:
            attribute_import.set_progress(int(index / attribute_count * 100))
            attribute_import.set_status(f"{status_text} {index}/{attribute_count}")

        if not attribute.property_set.object:
            continue

        if not attribute.value:
            attribute_import_sql.add_attribute_without_value(attribute)
        else:
            attribute_import_sql.add_attribute_with_value(attribute)

    attribute_import_sql.disconnect_from_database()
    attribute_import.set_progress(100)
    attribute_import.set_status(f"{status_text} {attribute_count}/{attribute_count}")


def accept_clicked():
    pass


def abort_clicked():
    pass


def close_clicked():
    pass


def paint_property_set_table(attribute_import: Type[tool.AttributeImport],
                             attribute_import_sql: Type[tool.AttributeImportSQL]):
    if attribute_import.is_table_editing():
        return
    ifc_type = attribute_import.get_ifctype_combo_box().currentText()
    som_object = attribute_import.get_somtype_combo_box().currentData(Qt.ItemDataRole.UserRole)
    all_keyword = attribute_import.get_all_keyword()
    if ifc_type is None or som_object is None:
        return
    property_set_list = attribute_import_sql.get_property_sets(ifc_type, som_object, all_keyword)
    table_widget = attribute_import.get_pset_table()
    attribute_import.update_table_widget(set(property_set_list), table_widget, [str, int])
    paint_attribute_table(attribute_import, attribute_import_sql)


def paint_attribute_table(attribute_import: Type[tool.AttributeImport],
                          attribute_import_sql: Type[tool.AttributeImportSQL]):
    if attribute_import.is_table_editing():
        return
    table_widget = attribute_import.get_attribute_table()
    ifc_type = attribute_import.get_ifctype_combo_box().currentText()
    som_object = attribute_import.get_somtype_combo_box().currentData(Qt.ItemDataRole.UserRole)
    property_set = attribute_import.get_selected_property_set()
    all_keyword = attribute_import.get_all_keyword()

    if None in [ifc_type, som_object, property_set]:
        attribute_import.disable_table(table_widget)
        return
    else:
        table_widget.setDisabled(False)

    attribute_list = attribute_import_sql.get_attributes(ifc_type, som_object, property_set, all_keyword)
    attribute_import.update_table_widget(set(attribute_list), table_widget, [str, int, int])
    paint_value_table(attribute_import, attribute_import_sql)


def paint_value_table(attribute_import: Type[tool.AttributeImport],
                      attribute_import_sql: Type[tool.AttributeImportSQL]):
    if attribute_import.is_table_editing():
        return
    table_widget = attribute_import.get_value_table()
    ifc_type = attribute_import.get_ifctype_combo_box().currentText()
    som_object = attribute_import.get_somtype_combo_box().currentData(Qt.ItemDataRole.UserRole)
    property_set = attribute_import.get_selected_property_set()
    attribute = attribute_import.get_selected_attribute()
    all_keyword = attribute_import.get_all_keyword()

    if None in [ifc_type, som_object, property_set, attribute]:
        attribute_import.disable_table(table_widget)
        return
    else:
        table_widget.setDisabled(False)

    value_list = attribute_import_sql.get_values(ifc_type, som_object, property_set, attribute, all_keyword)
    if not value_list:
        return
    table_values = set(v[:-2] for v in value_list)
    attribute_import.update_table_widget(table_values, table_widget, [str, int], add_checkbox=True)
    check_state_dict = attribute_import.get_value_checkstate_dict(value_list)
    attribute_import.update_valuetable_checkstate(check_state_dict)


def ifc_import_started(runner, attribute_import: Type[tool.AttributeImport],
                       ifc_importer: Type[tool.IfcImporter]):
    widget = attribute_import.get_ifc_import_widget()
    ifc_importer.set_progressbar_visible(widget, True)
    ifc_importer.set_status(widget, f"Import '{os.path.basename(runner.path)}'")
    ifc_importer.set_progress(widget, 0)


def ifc_import_finished(runner: IfcImportRunner, attribute_import: Type[tool.AttributeImport],
                        ifc_importer: Type[tool.IfcImporter]):
    """
    creates and runs Modelcheck Runnable
    """

    attribute_import.destroy_import_runner(runner)
    ifc_import_widget = attribute_import.get_ifc_import_widget()
    ifc_importer.set_status(ifc_import_widget, f"Import Abgeschlossen")
    attribute_import_runner = attribute_import.create_attribute_import_runner(runner)
    attribute_import.connect_attribute_import_runner(attribute_import_runner)
    attribute_import.set_current_runner(attribute_import_runner)
    attribute_import.get_attribute_import_threadpool().start(attribute_import_runner)


def start_attribute_import(file: ifcopenshell.file, path, attribute_import: Type[tool.AttributeImport],
                           attribute_import_sql: Type[tool.AttributeImportSQL]):
    attribute_import.set_ifc_path(path)
    pset_name, attribute_name = attribute_import.get_main_pset(), attribute_import.get_main_attribute()
    attribute_import_sql.connect_to_data_base(attribute_import_sql.get_database_path())
    entity_list = list(file.by_type("IfcObject"))
    entity_count = len(entity_list)
    status_text = "Entität aus Datei importieren:"
    for index, entity in enumerate(entity_list):
        if index % 100 == 0:
            attribute_import.set_progress(int(index / entity_count * 100))
            attribute_import.set_status(f"{status_text} {index}/{entity_count}")
        attribute_import_sql.add_entity(entity, pset_name, attribute_name, os.path.basename(path))
        attribute_import_sql.import_entity_attributes(entity, file)
    attribute_import_sql.disconnect_from_database()


def attribute_import_finished(attribute_import: Type[tool.AttributeImport], ifc_importer: Type[tool.IfcImporter]):
    ifc_import_widget = attribute_import.get_ifc_import_widget()

    if attribute_import.is_aborted():
        ifc_importer.set_progressbar_visible(ifc_import_widget, False)
        ifc_importer.set_close_button_text(ifc_import_widget, "Close")
        ifc_importer.set_run_button_enabled(ifc_import_widget, True)
        return

    time.sleep(0.2)
    if not attribute_import.attribute_import_is_running():
        ifc_importer.set_close_button_text(ifc_import_widget, f"Close")
        ifc_importer.set_run_button_enabled(ifc_import_widget, True)
        attribute_import.last_import_finished()
    else:
        logging.info(f"Prüfung von Datei abgeschlossen, nächste Datei ist dran.")


def last_import_finished(attribute_import: Type[tool.AttributeImport]):
    attribute_import.get_window().close()
    open_results_window(attribute_import)
