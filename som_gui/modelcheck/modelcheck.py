from __future__ import annotations

import os
import re
import sqlite3
import tempfile
from typing import TYPE_CHECKING

import SOMcreator
import ifcopenshell
import tqdm
from PySide6.QtCore import QRunnable, QThreadPool
from SOMcreator import Project
from SOMcreator import constants as som_constants
from ifcopenshell import entity_instance
from ifcopenshell.util import element as ifc_el

from . import issues
from .output import create_issues
from .sql import db_create_entity, remove_existing_issues, create_tables,guids
from . import sql
from ..windows.modelcheck_window import ModelcheckWindow

if TYPE_CHECKING:
    from ..main_window import MainWindow
from datetime import datetime

GROUP = "Gruppe"
ELEMENT = "Element"


def run_modelcheck(main_window: MainWindow):
    sql.guids = dict()
    project = main_window.project
    dialog = ModelcheckWindow(main_window)
    answer = dialog.exec()
    if not answer:
        return
    ifc_paths = dialog.get_ifc_path()
    export_path = dialog.widget.line_edit_export.text()

    if dialog.data_base_path is None:
        db_path = tempfile.NamedTemporaryFile().name
    else:
        db_path = dialog.data_base_path

    property_set = dialog.widget.line_edit_ident_pset.text()
    attribute = dialog.widget.line_edit_ident_attribute.text()
    main_window.running_modelcheck = MainRunnable(ifc_paths, main_window.project, db_path, property_set, attribute,
                                                  export_path, project.name)
    main_window.running_modelcheck.start()


def check_file(file_path, proj, ag, bk, db_name, p_name):
    file_name, extension = os.path.splitext(file_path)
    if extension.lower() != ".ifc":
        return

    file = os.path.split(file_path)[1]

    ifc = ifcopenshell.open(file_path)
    check_all_elements(proj, ifc, file, db_name, ag, bk, p_name)


class MainRunnable(QRunnable):
    def __init__(self, *args):
        super(MainRunnable, self).__init__()
        self.target = main
        self.args = args

    def run(self) -> None:
        self.target(*self.args)

    def start(self):
        QThreadPool.globalInstance().start(self)


def main(file_paths, proj: Project, db_path, ag, bk, issue_path, p_name):
    create_tables(db_path)

    if not isinstance(file_paths, list):
        if not isinstance(file_paths, str):
            return
        if not os.path.isfile(file_paths):
            return
        check_file(file_paths, proj, ag, bk, db_path, p_name)
        return

    for path in file_paths:
        if os.path.isdir(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                check_file(file_path, proj, ag, bk, db_path, p_name)
        else:
            check_file(path, proj, ag, bk, db_path, p_name)

    create_issues(db_path, issue_path)


def get_identifier(el: entity_instance, main_pset: str, main_attribute: str) -> str | None:
    return ifc_el.get_pset(el, main_pset, main_attribute)


def check_element(element, ag, bk, cursor, file_name, ident_dict, element_type, project_name):
    def check_values(cursor, value, attribute: SOMcreator.Attribute, guid, element_type):
        check_dict = {som_constants.LIST: check_list, som_constants.RANGE: check_range,
                      som_constants.FORMAT: check_format}
        func = check_dict[attribute.value_type]
        func(cursor, value, attribute, guid, element_type)

    def check_format(cursor, value, attribute, guid, element_type):
        is_ok = False
        for form in attribute.value:
            if re.match(form, value) is not None:
                is_ok = True
        if not is_ok:
            issues.format_issue(cursor, guid, attribute, element_type)

    def check_list(cursor, value, attribute, guid, element_type):
        if not attribute.value:
            return
        if value not in attribute.value:
            issues.list_issue(cursor, guid, attribute, element_type)

    def check_range(cursor, value, attribute, guid, element_type):
        is_ok = False
        for possible_range in attribute:
            if min(possible_range) <= value <= max(possible_range):
                is_ok = True
        if not is_ok:
            issues.range_issue(cursor, guid, attribute, element_type)

    def check_for_attributes(cursor, element, pset_dict, obj: SOMcreator.Object, element_type):
        guid = element.GlobalId
        for property_set in obj.property_sets:
            pset_name = property_set.name
            if pset_name not in pset_dict:
                issues.property_set_issue(cursor, guid, pset_name, element_type)
                continue

            for attribute in property_set.attributes:
                attribute_name = attribute.name
                if attribute.name not in pset_dict[pset_name]:
                    issues.attribute_issue(cursor, guid, pset_name, attribute_name, element_type)
                    continue

                value = pset_dict[pset_name][attribute_name]
                check_values(cursor, value, attribute, guid, element_type)

    guid = element.GlobalId
    psets = ifc_el.get_psets(element)
    ag_pset = psets.get(ag)
    group_assignment = [assignment for assignment in getattr(element, "HasAssignments", []) if
                        assignment.is_a("IfcRelAssignsToGroup")]
    if not group_assignment:
        issues.no_group_issue(cursor, element)

    if ag_pset is None:
        issues.ident_pset_issue(cursor, guid, ag, element_type)
        db_create_entity(element, cursor, project_name, file_name, "")
        return

    bauteil_klassifikation = ag_pset.get(bk)
    if bauteil_klassifikation is None:
        issues.ident_issue(cursor, guid, ag, bk, element_type)
        db_create_entity(element, cursor, project_name, file_name, "")
        return
    obj_rep = ident_dict.get(bauteil_klassifikation)
    db_create_entity(element, cursor, project_name, file_name, bauteil_klassifikation)
    if obj_rep is None:
        issues.ident_unknown(cursor, guid, ag, bk, element_type, bauteil_klassifikation)
        return

    check_for_attributes(cursor, element, psets, obj_rep, element_type)


SUBGROUPS = "subgroups"
SUBELEMENT = "subelement"


def build_group_structure(focus_group: ifcopenshell.entity_instance, group_dict: dict, ag: str, bk: str, group_parent_dict:dict):
    group_dict[SUBGROUPS] = dict()
    group_dict[SUBELEMENT] = set()


    relationships = getattr(focus_group, "IsGroupedBy", [])
    for relationship in relationships:
        for sub_element in relationship.RelatedObjects:  # IfcGroup or IfcElement
            sub_element: ifcopenshell.entity_instance
            if sub_element.is_a("IfcElement"):
                group_dict[SUBELEMENT].add(sub_element)
            else:
                group_parent_dict[sub_element] = focus_group
                group_dict[SUBGROUPS][sub_element] = dict()
                build_group_structure(sub_element, group_dict[SUBGROUPS][sub_element], ag, bk,group_parent_dict)

def check_group_structure(group, group_dict: dict, layer_index, ag, bk, cursor, file_name, project_name, ident_dict,group_parent_dict:dict[ifcopenshell.entity_instance,ifcopenshell.entity_instance]):
    def check_collector_group():
        db_create_entity(group, cursor, project_name, file_name, identifier)
        for sub_ident in sub_idents:
            if sub_ident != identifier:
                issues.subgroup_issue(cursor, group.GlobalId, sub_ident)

    def check_real_group():
        def loop_parent(element:SOMcreator.classes.Aggregation) -> SOMcreator.classes.Aggregation:
            if element.parent_connection != som_constants.INHERITANCE:
                return element.parent
            else:
                return loop_parent(element.parent)

        object_rep: SOMcreator.classes.Object = ident_dict.get(identifier)
        check_element(group, ag, bk, cursor, file_name, ident_dict, GROUP, project_name)
        if len(sub_idents) != len([get_identifier(sub_group, ag, bk) for sub_group in group_dict[group][SUBGROUPS]]):
            issues.repetetive_group_issue(cursor, group)

        if object_rep is None:
            return

        parent_group = group_parent_dict.get(group_parent_dict.get(group))
        if parent_group is None:
            return
        parent_object = ident_dict.get(get_identifier(parent_group,ag,bk))
        if parent_object is None:
            return

        parent_is_allowed = False

        for aggreg in object_rep.aggregations:
            allowed_parent = loop_parent(aggreg)

            if parent_object == allowed_parent.object:
                parent_is_allowed = True

        if not parent_is_allowed:
            issues.parent_issue(cursor, group, parent_group, ag, bk)

    identifier = get_identifier(group, ag, bk)
    sub_entities = set(group_dict[group][SUBGROUPS].keys()).union(group_dict[group][SUBELEMENT])

    sub_idents = {get_identifier(sub_group, ag, bk) for sub_group in group_dict[group][SUBGROUPS]}
    even_layer = layer_index % 2 == 0
    if even_layer:
        check_collector_group()
    else:
        check_real_group()

    if len(sub_entities) == 0:
        issues.empty_group_issue(cursor, group)

    for sub_group in group_dict[group][SUBGROUPS]:
        check_group_structure(sub_group, group_dict[group][SUBGROUPS], layer_index + 1, ag, bk, cursor, file_name,
                              project_name, ident_dict,group_parent_dict)


def get_parent_group(group: entity_instance) -> list[entity_instance]:
    parent_assignment: list[entity_instance] = [assignment for assignment in getattr(group, "HasAssignments", []) if
                                                assignment.is_a("IfcRelAssignsToGroup")]
    if not parent_assignment:
        return []
    return [assignment.RelatingGroup for assignment in parent_assignment]


def check_all_elements(proj: Project, ifc: ifcopenshell.file, file_name: str, db_name: str, ag: str, bk: str,
                       project_name: str):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    remove_existing_issues(cursor, project_name, datetime.today(), file_name)

    ident_dict = {obj.ident_value: obj for obj in proj.objects}
    for element in tqdm.tqdm(ifc.by_type("IfcElement"), desc=f"[{ELEMENT}] {file_name}"):
        check_element(element, ag, bk, cursor, file_name, ident_dict, ELEMENT, project_name)

    root_groups = [group for group in ifc.by_type("IfcGroup") if not get_parent_group(group)]

    group_dict = dict()
    group_parent_dict = dict()
    for element in root_groups:
        group_dict[element] = dict()
        build_group_structure(element, group_dict[element], ag, bk,group_parent_dict)

    for group in tqdm.tqdm(group_dict.keys(), desc=f"[{GROUP}] {file_name}"):
        check_group_structure(group, group_dict, 0, ag, bk, cursor, file_name, project_name, ident_dict,group_parent_dict)

    conn.commit()
    conn.close()
