from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTableWidget, QLabel
from SOMcreator import classes

import som_gui
from som_gui import tool
from som_gui.windows.aggregation_view import aggregation_window
from . import icons, settings, __version__
from .filehandling import open_file, save_file, export
from .qt_designs.ui_mainwindow import Ui_MainWindow
from .widgets import property_widget, object_widget
from .windows import (
    predefined_psets_window,
    propertyset_window,
    mapping_window,
    popups,
    grouping_window,
)
from .module.project import ui
from .windows.project_phases import gui as project_phase_window
from .windows.modelcheck import modelcheck_window
from .windows.attribute_import.gui import AttributeImport

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from som_gui.module.objects.ui import ObjectTreeWidget


class MainWindow(QMainWindow):
    def __init__(self, application):
        def connect_actions():
            # connect Menubar signals
            self.ui.action_file_new.triggered.connect(
                lambda: popups.new_file_clicked(self)
            )
            self.ui.action_file_Save.triggered.connect(
                lambda: save_file.save_clicked(self)
            )
            self.ui.action_file_Save_As.triggered.connect(
                lambda: save_file.save_as_clicked(self)
            )
            # Export

            self.ui.action_export_bs.triggered.connect(
                lambda: export.export_building_structure(self)
            )
            self.ui.action_export_bookmarks.triggered.connect(
                lambda: export.export_bookmarks(self)
            )
            self.ui.action_export_boq.triggered.connect(
                lambda: export.export_bill_of_quantities(self)
            )
            self.ui.action_vestra.triggered.connect(
                lambda: export.export_vestra_mapping(self)
            )
            self.ui.action_card1.triggered.connect(lambda: export.export_card_1(self))
            self.ui.action_excel.triggered.connect(lambda: export.export_excel(self))
            self.ui.action_mapping_script.triggered.connect(
                lambda: export.export_mapping_script(self)
            )
            self.ui.action_allplan.triggered.connect(
                lambda: export.export_allplan_excel(self)
            )
            self.ui.action_abbreviation_json.triggered.connect(
                lambda: export.export_desite_abbreviation(self)
            )
            # Windows

            self.ui.action_show_list.triggered.connect(self.open_predefined_pset_window)
            self.ui.action_modelcheck.triggered.connect(
                lambda: modelcheck_window.ModelcheckWindow(self)
            )
            self.ui.action_create_groups.triggered.connect(self.open_grouping_window)
            self.ui.action_model_control.triggered.connect(
                self.open_attribute_import_window
            )
            self.ui.action_project_phase.triggered.connect(
                lambda: project_phase_window.ProjectPhaseWindow(self)
            )
            self.ui.action_show_graphs.triggered.connect(self.open_aggregation_window)
            self.ui.action_mapping.triggered.connect(self.open_mapping_window)

        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.app = application
        som_gui.MainUi.ui = self.ui
        som_gui.MainUi.window = self

        # variables
        self.active_object: classes.Object | None = None
        self.active_property_set: classes.PropertySet | None = None
        self.project = None
        self.permanent_status_text = QLabel()

        # Windows
        self.group_window: grouping_window.GroupingWindow | None = None
        self.model_control_window: AttributeImport | None = None
        self.project_phase_window: project_phase_window.ProjectPhaseWindow | None = None
        self.graph_window = aggregation_window.AggregationWindow(self)
        self.mapping_window = None
        self.modelcheck_window: modelcheck_window.ModelcheckWindow | None = None
        self.search_ui: popups.SearchWindow | None = None
        self.predefined_pset_window: predefined_psets_window.PropertySetInherWindow | None = (
            None
        )
        self.property_set_window: None | propertyset_window.PropertySetWindow = None

        # init Object- and PropertyWidget
        # object_widget.init(self)
        # property_widget.init(self)
        connect_actions()
        settings.reset_save_path()
        self.ui.statusbar.addWidget(self.permanent_status_text)
        self.generate_window_title()

        # Icons
        self.setWindowIcon(icons.get_icon())
        self.ui.button_search.setIcon(icons.get_search_icon())

    # Windows

    def open_mapping_window(self):
        self.mapping_window = mapping_window.MappingWindow(self)
        self.mapping_window.show()

    def open_grouping_window(self):
        if self.group_window is None:
            self.group_window = grouping_window.GroupingWindow(self)
        else:
            self.group_window.show()

    def open_attribute_import_window(self):
        if self.model_control_window is None:
            self.model_control_window = AttributeImport(self)
        else:
            self.model_control_window.show()

    def open_predefined_pset_window(self):
        if self.predefined_pset_window is None:
            self.predefined_pset_window = (
                predefined_psets_window.PropertySetInherWindow(self)
            )
        self.predefined_pset_window.show()

    def open_aggregation_window(self):
        self.graph_window.show()

    @property
    def object_tree(self) -> ObjectTreeWidget:
        return tool.Object.get_object_tree()

    @property
    def pset_table(self) -> QTableWidget:
        return self.ui.table_pset

    # Open / Close windows
    def closeEvent(self, event):
        action = save_file.close_event(self)

        if action:
            self.app.closeAllWindows()
            event.accept()
        else:
            event.ignore()

    # Main
    def clear_all(self):
        property_widget.clear_all(self)
        if self.predefined_pset_window is not None:
            self.predefined_pset_window.clear_all()
        self.project.clear()

    def reload(self):
        object_widget.reload(self)
        predefined_psets_window.reload(self)
        property_widget.reload(self)
        self.generate_window_title()

    def generate_window_title(self) -> str:
        text = f"SOM-Toolkit v{__version__}"
        self.setWindowTitle(text)
        if self.project:
            self.permanent_status_text.setText(
                f"{self.project.name} v{self.project.version}"
            )
        return text
