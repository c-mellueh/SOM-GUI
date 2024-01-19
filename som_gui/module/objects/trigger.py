import som_gui
from som_gui.tool import Project, Objects, Search
from som_gui.core import objects as core
from PySide6.QtWidgets import QTreeWidget
from som_gui.module.objects.prop import ObjectProperties, ObjectInfoWidgetProperties
from som_gui.module.objects.ui import ObjectInfoWidget
from som_gui.icons import get_search_icon
def connect():
    widget: QTreeWidget = Objects.get_object_tree()
    widget.itemChanged.connect(lambda item: core.item_changed(item, Objects))
    widget.itemSelectionChanged.connect(lambda: core.item_selection_changed(Objects))
    widget.itemDoubleClicked.connect(item_double_clicked)
    widget.customContextMenuRequested.connect(lambda p: core.create_context_menu(p, Objects))
    widget.expanded.connect(lambda: core.resize_columns(Objects))
    som_gui.MainUi.ui.button_search.pressed.connect(lambda: core.search_object(Search, Objects))

    core.load_context_menus(Objects)
    core.add_shortcuts(Objects, Project, Search)
    som_gui.MainUi.ui.button_search.setIcon(get_search_icon())

def item_double_clicked():
    core.create_object_info_widget(mode=1, object_tool=Objects)

def item_copy_event():
    core.create_object_info_widget(mode=2, object_tool=Objects)

def object_info_paint_event():
    core.object_info_refresh(Objects)
    pass

def repaint_event():
    core.refresh_object_tree(Objects, Project)


def change_event():
    core.item_changed(Objects)


def drop_event(event):
    print(F"DROP EVENT")
    core.item_dropped_on(event.pos(), Objects)


def on_new_project():
    core.reset_tree(Objects)