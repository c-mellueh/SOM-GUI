from __future__ import annotations  # make own class referencable

from typing import TYPE_CHECKING

from PySide6 import QtGui, QtCore
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QWheelEvent, QMouseEvent,QTransform,QShortcut,QKeySequence
from PySide6.QtWidgets import QGraphicsItem, QWidget, QGraphicsScene, QGraphicsView,QApplication,QMenu,QRubberBand
from SOMcreator import classes

from som_gui.qt_designs import ui_GraphWindow
from .node import NodeProxy, Header, Frame, Connection,Circle
from ...data import constants
from ...windows import popups
from ...icons import get_icon,get_reload_icon,get_search_icon
if TYPE_CHECKING:
    from som_gui.main_window import MainWindow

LEFT = 1
RIGHT = 2
TOP = 3
BOTTOM = 6
TOLERANCE = 5

CURSOR_DICT = {
    1: Qt.CursorShape.SizeHorCursor,  # Left
    2: Qt.CursorShape.SizeHorCursor,  # right
    3: Qt.CursorShape.SizeVerCursor,  # Top
    6: Qt.CursorShape.SizeVerCursor,  # Bottom
    4: Qt.CursorShape.SizeFDiagCursor,  # TOP Left
    7: Qt.CursorShape.SizeBDiagCursor,  # Bottom Left
    5: Qt.CursorShape.SizeBDiagCursor,  # Top Right
    8: Qt.CursorShape.SizeFDiagCursor,  # Bottom Right
    9: Qt.CursorShape.OpenHandCursor,
    10: Qt.CursorShape.ClosedHandCursor,
    11: Qt.CursorShape.ArrowCursor,
}


class AggregationScene(QGraphicsScene):
    def __init__(self, aggregation_window: AggregationWindow, name:str):
        super(AggregationScene, self).__init__()
        self.node_pos = QPointF(50, 50)
        self._name = name
        self.aggregation_window = aggregation_window
        self.setSceneRect(1, 1, 100_000, 100_000)
        self.selected_nodes:set[NodeProxy] = set()

    def get_items_bounding_rect(self,items) -> QRectF:
        b_min = [None, None]
        b_max = [None, None]
        for item in items:
            if not item.isVisible() and isinstance(item,NodeProxy):
                continue

            rect = item.sceneBoundingRect()
            tl = rect.topLeft()
            br = rect.bottomRight()
            r_min = [tl.x(), tl.y()]
            r_max = [br.x(), br.y()]

            for index, (extreme, value) in enumerate(zip(b_min, r_min)):
                if extreme is None or value < extreme:
                    b_min[index] = value

            for index, (extreme, value) in enumerate(zip(b_max, r_max)):
                if extreme is None or value > extreme:
                    b_max[index] = value

        if None in b_max or None in b_min:
            return QRectF(0, 0, 0, 0)

        b1 = QPointF(b_min[0], b_min[1])
        b2 = QPointF(b_max[0], b_max[1])

        return QRectF(b1, b2)

    def views(self) -> list[AggregationView]:
        return super(AggregationScene, self).views()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        old_name = self._name
        values = self.aggregation_window.scene_dict[old_name]
        self.aggregation_window.scene_dict[new_name] = values
        self.aggregation_window.scene_dict.pop(old_name)
        self._name = new_name

    @property
    def nodes(self) -> set[NodeProxy]:
        return set(node for node in self.items() if isinstance(node, NodeProxy))

    def add_node(self, node_proxy: NodeProxy, recursive=False):
        node_proxy.setZValue(self.max_z_value() + 1)
        self.addItem(node_proxy)

        node_proxy.show()
        self.aggregation_window.scene_dict[self.name][constants.NODES].append(node_proxy.aggregation.uuid)
        if recursive:
            uuid_dict = {node.aggregation.uuid: node for node in self.aggregation_window.nodes}
            child: classes.Aggregation
            for child in node_proxy.aggregation.children:
                child_node = uuid_dict.get(child.uuid)
                self.add_node(child_node, recursive=True)

    def remove_node(self, node_proxy: NodeProxy):
        self.removeItem(node_proxy)
        self.aggregation_window.scene_dict[self.name][constants.NODES].append(node_proxy.aggregation.uuid)
        node_proxy.delete()

    def max_z_value(self):
        return max((item.zValue() for item in self.items()), default=0)

    def fill_connections(self):
        node_dict = {node.aggregation:node for node in self.nodes}
        for node in self.nodes:
            aggregation = node.aggregation
            sub_elements = aggregation.children

            for sub_aggregation in sub_elements:

                sub_node:NodeProxy = node_dict.get(sub_aggregation)
                if sub_node is None:
                    print(f"{aggregation} -> {sub_aggregation} missing")
                    continue
                self.add_connection(node,sub_node,sub_node.aggregation.parent_connection)

    def add_connection(self,top_node:NodeProxy,bottom_node:NodeProxy,connection_type = constants.AGGREGATION):
        con = Connection(bottom_node,top_node,Connection.NORMAL_MODE,connection_type)

    def delete(self):
        for node in self.nodes:
            node.delete()
        self.aggregation_window.scenes.remove(self)
        self.aggregation_window.scene_dict.pop(self.name)

class AggregationView(QGraphicsView):
    def __init__(self) -> None:
        super(AggregationView, self).__init__()
        self.focus_node: NodeProxy | None = None  # which Node is being resized
        self.resize_orientation: int | None = None  # which edge of Node is being resized
        self.last_pos: QPointF | None = None  # last mouse pos to calculate difference
        self.mouse_mode = 0  # 0=moveCursor 1=resize 2 = drag 3 = plus click 4 = draw connection 5 = rubber_band
        self.mouse_is_pressed = False
        self.setDragMode(self.DragMode.ScrollHandDrag)
        self.right_click_menu:QMenu|None = None
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_click)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.drawn_connection:Connection|None = None
        self.rubber_band:QRubberBand|None = None
        self.setInteractive(True)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.ContainsItemBoundingRect)


    def window(self) -> AggregationWindow:
        return super(AggregationView, self).window()

    def items_under_mouse(self) -> set[QGraphicsItem]:
        return set(item for item in self.scene().items() if item.isUnderMouse())

    def scene(self) -> AggregationScene:  # for typing
        return super(AggregationView, self).scene()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super(AggregationView, self).resizeEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:

        """
        Resizes the MainView based on Scrollwheel and Keyboard Input
        :param event:
        :type event:
        :return:
        :rtype:
        """

        point = event.angleDelta() / 4
        val = point.y()

        modifier = QApplication.keyboardModifiers()

        if bool(modifier == Qt.ControlModifier):

            if val < 0:
                self.scale(1 - constants.SCALING_FACTOR, 1 - constants.SCALING_FACTOR)
            else:
                self.scale(1 + constants.SCALING_FACTOR, 1 + constants.SCALING_FACTOR)

        elif bool(modifier == Qt.ShiftModifier):
            hor = self.horizontalScrollBar()
            hor.setValue(hor.value() - val)

        else:
            ver = self.verticalScrollBar()
            ver.setValue(ver.value() - val)
        self.update()

    def get_focus_and_cursor(self, pos: QPointF) -> (int,NodeProxy):
        """return cursor style and Node that will be in focus"""
        for node in self.scene().nodes:
            if node.circle.isUnderMouse():
                return 11,node

        frames = [node.frame for node in self.scene().nodes if self.cursor_on_border(pos, node) != 0]
        headers = [item for item in self.items_under_mouse() if isinstance(item, Header)]

        frames.sort(key=lambda x: x.node_proxy.zValue())
        headers.sort(key=lambda x: x.node_proxy.zValue())

        max_frame = max({frame.node_proxy.zValue() for frame in frames}, default=0)
        max_header = max({header.node_proxy.zValue() for header in headers}, default=0)

        if not (frames or headers):
            cursor_style = 0
            node = None

        elif max_header >= max_frame:
            header = sorted(headers, key=lambda x: x.node_proxy.zValue())[-1]
            node = header.node_proxy
            if self.mouse_is_pressed:
                cursor_style = 10
            else:
                cursor_style = 9

        else:
            frame: Frame = sorted(frames, key=lambda x: x.node_proxy.zValue())[-1]
            node = frame.node_proxy
            cursor_style = self.cursor_on_border(pos, node)

        return cursor_style, node

    def mousePressEvent(self, event: QMouseEvent) -> None:

        self.mouse_is_pressed = True

        modifier = QApplication.keyboardModifiers()
        if bool(modifier == Qt.KeyboardModifier.ShiftModifier):
            self.mouse_mode = 5
            self.setDragMode(self.DragMode.RubberBandDrag)

            return super(AggregationView, self).mousePressEvent(event)

        if event.button() == Qt.MouseButton.RightButton:
            super(AggregationView, self).mousePressEvent(event)
            return

        self.resize_orientation, self.focus_node = self.get_focus_and_cursor(self.mapToScene(event.pos()))

        if self.resize_orientation == 0:
            self.unsetCursor()

        elif self.resize_orientation == 10: #Drag
            self.mouse_mode = 2
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.focus_node.setZValue(self.scene().max_z_value()+1)
        elif 1<= self.resize_orientation <=9:
            self.setCursor(CURSOR_DICT[self.resize_orientation])    #resize
            self.mouse_mode = 1
            self.focus_node.setZValue(self.scene().max_z_value() + 1)

        else:
            self.setCursor(CURSOR_DICT[self.resize_orientation])
            self.mouse_mode = 3
            self.focus_node.setZValue(self.scene().max_z_value()+1)

        super(AggregationView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.mouse_mode == 0:
            cursor_style, focus_node = self.get_focus_and_cursor(self.mapToScene(event.pos()))
            if cursor_style == 0:
                self.setDragMode(self.DragMode.ScrollHandDrag)
                self.unsetCursor()
            else:
                self.setDragMode(self.DragMode.NoDrag)
                self.setCursor(CURSOR_DICT[cursor_style])

        if self.mouse_mode == 1:
            old_pos = self.last_pos
            new_pos = self.mapToScene(event.pos())
            if old_pos is None:
                old_pos = new_pos
            self.last_pos = new_pos
            self.focus_node.resize_by_cursor(old_pos, new_pos, self.resize_orientation)

        if self.mouse_mode == 2:
            new_pos = self.mapToScene(event.pos())

            old_pos = self.last_pos or new_pos
            self.last_pos = new_pos
            delta = new_pos - old_pos

            if self.focus_node in self.scene().selected_nodes:
                for node in self.scene().selected_nodes:
                    node.moveBy(delta.x(), delta.y())
            else:
                self.focus_node.moveBy(delta.x(), delta.y())

        if self.mouse_mode == 3:
            self.drawn_connection = Connection(None, self.focus_node, Connection.DRAW_MODE)
            self.mouse_mode = 4

        if self.mouse_mode ==4 :
            self.drawn_connection.update_line(self.mapToScene(event.pos()))

        for node in self.scene().nodes: #change Style if selected
            node.update()

        return super(AggregationView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        old_mouse_mode = self.mouse_mode
        self.mouse_is_pressed = False
        self.mouse_mode = 0
        self.last_pos = None
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        if old_mouse_mode in (1,2):
            pass
        elif old_mouse_mode ==3:
            self.focus_node.widget().button_clicked()

        elif old_mouse_mode == 4:
            self.draw_connection_mouse_release(event)


        for node in self.scene().nodes:
            node.update()

        if event.button() != Qt.MouseButton.RightButton:
            self.scene().selected_nodes = set(item for item in self.scene().selectedItems() if isinstance(item, NodeProxy))

        return super(AggregationView, self).mouseReleaseEvent(event)

    def right_click(self,pos:QPointF):
        def rc_add_node():
            search = popups.ObjectSearchWindow(self.window().main_window)
            if not search.exec():
                return
            obj = search.selected_object
            aggregation = classes.Aggregation(obj)
            node = self.window().create_node(aggregation,node_pos,self.scene())

        def rc_set_info():
            search = popups.AttributeSearchWindow(self.window().main_window)
            if search.exec():
                pset_name = search.selected_pset_name
                attribute_name = search.selected_attribute_name
                self.window().set_info(pset_name,attribute_name)

        def rc_delete_node():
            if focus_node in self.scene().selected_nodes:
                for node in list(self.scene().selected_nodes):
                    self.scene().remove_node(node)
            else:
                self.scene().remove_node(focus_node)

        def set_connection(connection_type:int):
            focus_node.aggregation.set_parent(focus_node.aggregation.parent,connection_type)
            for con in focus_node.top_connection.top_node.bottom_connections:
                con.update_line()

        if self.right_click_menu is not None:
            pass
        self.right_click_menu = QMenu()
        node_pos = self.mapToScene(pos)
        style:int
        focus_node:NodeProxy
        style,focus_node = self.get_focus_and_cursor(pos)

        if style ==9:
            self.action_add_node = self.right_click_menu.addAction("Node löschen")
            self.action_add_node.triggered.connect(rc_delete_node)
            if focus_node.aggregation.parent is not None:
                self.menu_connection = self.right_click_menu.addMenu("Verbindungsart")
                self.action_set_aggregation = self.menu_connection.addAction("Aggregation")
                self.action_set_aggregation.triggered.connect(lambda : set_connection(constants.AGGREGATION))
                self.action_set_aggregation = self.menu_connection.addAction("Vererbung")
                self.action_set_aggregation.triggered.connect(lambda : set_connection(constants.INHERITANCE))
                self.action_set_aggregation = self.menu_connection.addAction("Aggregation+Vererbung")
                self.action_set_aggregation.triggered.connect(lambda : set_connection(
                    constants.INHERITANCE + constants.AGGREGATION))

        def rc_reset_info():
            self.window().reset_info()

        self.action_add_node = self.right_click_menu .addAction("Node hinzufügen")
        self.action_add_node.triggered.connect(rc_add_node)

        self.action_modify_info = self.right_click_menu.addAction("Info Anpassen")
        self.action_modify_info.triggered.connect(rc_set_info)

        self.action_reset_info = self.right_click_menu.addAction("Info Zurücksetzen")
        self.action_reset_info.triggered.connect(rc_reset_info)
        global_pos = self.viewport().mapToGlobal(pos)
        self.right_click_menu.exec(global_pos)

    def draw_connection_mouse_release(self,event:QMouseEvent):
        """if the user draws a line and the mouse was released this event should be called to determine if a new Connection gets established"""
        item_under_mouse = self.scene().itemAt(self.mapToScene(event.pos()), QTransform())

        if isinstance(item_under_mouse, Connection):
            self.drawn_connection.delete()
            self.drawn_connection = None
            return super(AggregationView, self).mouseReleaseEvent(event)

        if isinstance(item_under_mouse, (Header, Frame, Circle)):
            node_proxy = item_under_mouse.node_proxy
        elif isinstance(item_under_mouse, NodeProxy):
            node_proxy = item_under_mouse
        else:
            return super(AggregationView, self).mouseReleaseEvent(event)

        allowed = True
        if node_proxy in self.drawn_connection.top_node.child_nodes():
            allowed = False

        if allowed:
            allowed = self.drawn_connection.top_node.aggregation.add_child(node_proxy.aggregation)

        if not allowed:
            self.drawn_connection.delete()
            self.drawn_connection = None
        else:
            self.drawn_connection.add_bottom_node(node_proxy,constants.AGGREGATION)
            self.drawn_connection.update_line()
            self.drawn_connection = None
        node_proxy.refresh_title()
        return super(AggregationView, self).mouseReleaseEvent(event)

    def cursor(self) -> QtGui.QCursor:
        return self.viewport().cursor()

    def cursor_on_border(self, pos, proxy: NodeProxy):
        """checks if Cursor is on border of Node and returns the Border orientation"""

        border = proxy.sceneBoundingRect()

        mouse_x = pos.x()
        mouse_y = pos.y()
        frame_x = border.x()
        frame_y = border.y()
        frame_height = border.height()
        frame_width = border.width()
        min_y = frame_y - TOLERANCE
        max_y = frame_y + TOLERANCE
        min_x = frame_x - TOLERANCE
        max_x = frame_x + TOLERANCE

        def check_vert():

            if min_y <= mouse_y <= max_y + frame_height:
                if min_x <= mouse_x <= max_x:
                    return LEFT
                elif min_x + frame_width <= mouse_x <= max_x + frame_width:
                    return RIGHT
            return 0

        def check_hor():
            if min_x <= mouse_x <= max_x + frame_width:
                if min_y <= mouse_y <= max_y:
                    return TOP
                elif min_y + frame_height <= mouse_y <= max_y + frame_height:
                    return BOTTOM
            return 0

        frame_pos = check_vert() + check_hor()
        return frame_pos

    def setCursor(self, arg__1: QtGui.QCursor | QtCore.Qt.CursorShape | QtGui.QPixmap) -> None:
        """the Viewport is handling the Cursor if you call setCursor as is nothing will be changing"""
        if isinstance(arg__1, Qt.CursorShape):
            self.viewport().setCursor(arg__1)
        else:
            super(AggregationView, self).setCursor(arg__1)

    def unsetCursor(self) -> None:
        self.viewport().unsetCursor()


class AggregationWindow(QWidget):

    def __init__(self, main_window: MainWindow) -> None:
        super(AggregationWindow, self).__init__()
        self.main_window = main_window
        self.widget = ui_GraphWindow.Ui_GraphView()
        self.widget.setupUi(self)

        self.view = AggregationView()
        self.widget.gridLayout.removeWidget(self.widget.graphicsView)
        self.widget.gridLayout.addWidget(self.view, 1, 0, 1, 2)
        self.widget.graphicsView.deleteLater()
        self.scenes: set[AggregationScene] = set()
        self.scene_dict:dict[str,dict[str,list]] = {}  # used for import and export

        self.setWindowIcon(get_icon())

        self._active_scene = None
        self.is_initial_opening = True

        self.widget.combo_box.currentIndexChanged.connect(self.combo_box_index_changed)
        self.widget.button_filter.clicked.connect(self.filter_object)
        self.widget.button_delete.clicked.connect(self.delete_active_scene)
        self.widget.button_add.clicked.connect(self.add_scene_button_pressed)
        self.widget.combo_box.setEditable(True)
        self.widget.combo_box.lineEdit().textEdited.connect(self.combo_box_edited)
        self.widget.button_filter.setIcon(get_search_icon())
        self.is_in_filter_mode = False
        self.copy_shortcut = QShortcut(QKeySequence('Ctrl+C'), self)
        self.copy_shortcut.activated.connect(self.copy_selected_nodes)
        self.copied_nodes:set[NodeProxy] = set()

        self.paste_shortcut = QShortcut(QKeySequence('Ctrl+V'), self)
        self.paste_shortcut.activated.connect(self.paste_nodes)

    def copy_selected_nodes(self):
        self.copied_nodes = self.view.scene().selected_nodes

    def paste_nodes(self):
        scene = self.view.scene()
        if len(self.copied_nodes) == 0:
            return

        old_scene = list(self.copied_nodes)[0].scene()
        bounding_rect = old_scene.get_items_bounding_rect(self.copied_nodes)
        base_pos  = bounding_rect.topLeft()
        cursor_pos = self.view.mapToScene(self.mapFromGlobal(self.cursor().pos()))

        node_dict = dict()
        for node in self.copied_nodes:
            dif = node.sceneBoundingRect().topLeft()-base_pos
            old_aggregation = node.aggregation
            aggregation = classes.Aggregation(node.aggregation.object,description=old_aggregation.description,optional=old_aggregation.optional)
            new_node = NodeProxy(aggregation, cursor_pos+dif)
            node_dict[node] = new_node
            scene.add_node(new_node)

            for child_node in node.child_nodes():
                if child_node in node_dict:
                    self.view.scene().add_connection(new_node,node_dict[child_node])
            if node.parent_node() in node_dict:
                self.view.scene().add_connection(node_dict[node.parent_node()],new_node)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        super(AggregationWindow, self).closeEvent(event)
        self.close()

        for scene in list(self.scenes):
            if not scene.nodes:
                self.delete_scene(scene)

    def set_info(self,pset_name,attribute_name):
        for node in self.nodes:
            node.set_title_by_attribute(pset_name,attribute_name)

    def reset_info(self):
        for node in self.nodes:
            node.reset_title()

    def aggregation_dict(self) -> dict[classes.Aggregation,NodeProxy]:
        return {node.aggregation:node for node in self.nodes}

    def delete_active_scene(self):
        scene = self.active_scene
        if len(self.scenes) <=1:
            self.create_new_scene("UNDEF")
        self.delete_scene(scene)

    def delete_scene(self,scene:AggregationScene):
        name = scene.name
        scene.delete()
        index = self.widget.combo_box.findText(name)
        self.widget.combo_box.removeItem(index)

    def reset_filter(self):
        self.widget.button_filter.setIcon(get_search_icon())
        self.is_in_filter_mode = False
        self.widget.button_filter.setToolTip("Diagramme Filtern")
        for scene in self.scenes:
            index = self.widget.combo_box.findText(scene.name)
            if index == -1:
                self.add_scene_to_combobox(scene)

    def filter_object(self):
        if self.is_in_filter_mode:
            self.reset_filter()
            return


        search = popups.ObjectSearchWindow(self.main_window)
        if not search.exec():
            return

        obj = search.selected_object
        for scene in self.scenes:
            nodes = scene.nodes
            objects = [node.aggregation.object for node in nodes]
            if not obj in objects:
                self.remove_scene_from_combobox(scene)

        self.is_in_filter_mode = True
        self.widget.button_filter.setIcon(get_reload_icon())
        self.widget.button_filter.setToolTip("Filter zurücksetzen")
        self.widget.button_filter.setToolTip("Filter zurücksetzen")

    def remove_scene_from_combobox(self, scene:AggregationScene):
        index = self.widget.combo_box.findText(scene.name)
        self.widget.combo_box.removeItem(index)

    def add_scene_to_combobox(self, scene:AggregationScene):
        self.widget.combo_box.addItem(scene.name)
        self.widget.combo_box.model().sort(0)

    @property
    def nodes(self) -> set[NodeProxy]:
        return NodeProxy._registry

    def create_missing_scenes(self):
        """the scene_dict is in the best case written in the SOMjson and allows to save which Nodes are in a Scene
        This allows for saving multiple rootnodes in one scene.
        If no scenes are defined there will be created a scene for each rootnode"""

        scene_dict = self.scene_dict
        node_dict:dict[str,NodeProxy] = {node.uuid: node for node in self.nodes}
        for name, uuid_dict in tuple(scene_dict.items()):
            scene_nodes = set()

            scene = self.create_new_scene(name)
            uuid_nodes = uuid_dict.get(constants.NODES)
            for uuid in uuid_nodes:
                if uuid in node_dict:
                    node = node_dict.pop(uuid)
                    scene_nodes.add(node)
                    scene.add_node(node)
            scene.fill_connections()

        remaining_nodes: list[NodeProxy] = node_dict.values()
        root_nodes = set(node for node in remaining_nodes if node.aggregation.is_root)
        for node in sorted(root_nodes, key=lambda x: x.name):
            scene = self.create_new_scene(node.aggregation.name)
            scene.add_node(node, recursive=True)
            scene.fill_connections()

        first_scene = sorted([scene for scene in self.scenes],key=lambda x:x.name)[0]
        self.active_scene = first_scene

    def show(self) -> None:
        if not self.is_initial_opening and len(self.scenes) >0 :
            super(AggregationWindow, self).show()
            return

        if len(self.scene_dict) == 0 and len(self.nodes) == 0:
            self.active_scene = self.create_new_scene()
        else:
            self.create_missing_scenes()
        super(AggregationWindow, self).show()
        self.fit_view()
        self.widget.combo_box.setCurrentIndex(0)
        self.is_initial_opening = False

    def add_scene_button_pressed(self):
        scene = self.create_new_scene()
        self.select_scene(scene)

    def select_scene(self,scene:AggregationScene):
        index = self.widget.combo_box.findText(scene.name)
        self.widget.combo_box.setCurrentIndex(index)

    def create_new_scene(self, name="UNDEF") -> AggregationScene:
        def loop_name(index:int):
            new_name = f"{name}_{str(index).zfill(2)}"
            if new_name in names:
                index+=1
                return loop_name(index)
            return new_name

        names = [scene.name for scene in self.scenes]
        if name in names:
            name = loop_name(1)

        scene = AggregationScene(self, name)
        self.scenes.add(scene)
        self.scene_dict[scene.name] = {constants.NODES: list()}
        self.add_scene_to_combobox(scene)
        return scene

    def create_node(self, aggregation: classes.Aggregation, pos: QPointF, scene: AggregationScene = None) -> NodeProxy:
        node = NodeProxy(aggregation, pos)
        if scene is not None:
            scene.add_node(node)
        return node

    def combo_box_index_changed(self):
        if not self.nodes:
            return

        text = self.widget.combo_box.currentText()
        scene = {scene.name: scene for scene in self.scenes}.get(text)
        self.active_scene = scene
        self.fit_view()
        self.widget.combo_box.model().sort(0)

    def combo_box_edited(self, val):
        if self.active_scene is not None:
            self.active_scene.name = val
            index = self.widget.combo_box.currentIndex()
            self.widget.combo_box.setItemText(index,val)

    def fit_view(self):
        bounding_rect = self.active_scene.get_items_bounding_rect(self.active_scene.items())
        sr_center = self.active_scene.sceneRect().center()
        br_center = bounding_rect.center()
        dif = sr_center - br_center
        for item in self.active_scene.items():
            if isinstance(item, (NodeProxy)):
                item.moveBy(dif.x(), dif.y())

        bounding_rect = self.active_scene.get_items_bounding_rect(self.active_scene.items())
        marg = constants.SCENE_MARGIN
        self.view.fitInView(bounding_rect.adjusted(-marg,-marg,marg,marg),
                            aspectRadioMode=Qt.AspectRatioMode.KeepAspectRatio)

    @property
    def active_scene(self) -> AggregationScene:
        if self._active_scene is None:
            if self.is_in_filter_mode:
                self.reset_filter()
        if self._active_scene is None:
            self.active_scene = self.create_new_scene()
        return self._active_scene

    @active_scene.setter
    def active_scene(self, value: AggregationScene) -> None:
        self._active_scene = value
        self.view.setScene(self.active_scene)
