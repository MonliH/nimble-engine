from typing import Optional, cast
from PyQt5.QtGui import QFont, QFontDatabase
import moderngl_window as mglw
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu
from PyQt5.QtCore import QSettings, Qt
from pyrr.objects.vector3 import Vector3
from PyQtAds.QtAds import ads
from nimble.common.resources import load_ui

from nimble.interface.entity_inspector import EntityInspector
from nimble.interface.file_explorer import FileExplorer
from nimble.interface.outline import OutlineWidget
from nimble.interface.project_ui import SaveProjectAs

from nimble.interface.viewport import ViewportWidget

from nimble.objects.scene import active_scene
from nimble.objects.model import Model
from nimble.objects.geometry import Cube, Plane


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        font_id = QFontDatabase().addApplicationFont(":/fonts/OpenSans-Regular.ttf")
        family = QFontDatabase().applicationFontFamilies(font_id)[0]
        QApplication.setFont(QFont(family))

        self.setWindowState(Qt.WindowMaximized)
        self.show()
        self.setWindowTitle("Nimble Engine")

        load_ui(":/ui/main_window.ui", self)
        self.actionNew.triggered.connect(self.new_project)

        self.dock_manager = ads.CDockManager(self)

        self.viewport_dock = ads.CDockWidget("Scene Viewer")
        self.dock_manager.addDockWidget(ads.RightDockWidgetArea, self.viewport_dock)
        self.viewport = ViewportWidget(
            self.viewport_dock,
            on_gl_init=self.init_viewport,
        )
        self.viewport_dock.setWidget(self.viewport)

        self.outline_dock = ads.CDockWidget("Outline")
        self.dock_manager.addDockWidget(ads.LeftDockWidgetArea, self.outline_dock)
        self.outline = OutlineWidget(self.outline_dock)
        self.outline_dock.setWidget(self.outline)

        self.entity_dock = ads.CDockWidget("Entity Inspector")
        self.dock_manager.addDockWidget(ads.RightDockWidgetArea, self.entity_dock)
        self.entity = EntityInspector()
        self.entity_dock.setWidget(self.entity)

        self.file_explorer_dock = ads.CDockWidget("File Explorer")
        self.file_explorer = FileExplorer()
        self.file_explorer_dock.setWidget(self.file_explorer)
        self.dock_manager.addDockWidget(
            ads.RightDockWidgetArea, self.file_explorer_dock
        )

        self.last_mouse_button = None

        self.shift = False
        self.did_drag = False
        self.open_context = None
        self.context_menu_pos = (0, 0)
        self._modifiers = mglw.context.base.KeyModifiers()

        self.actionSave_Layout.triggered.connect(self.save_perspectives)
        self.actionReset_Layout.triggered.connect(self.restore_perspectives)

        self.menuWindow = cast(QMenu, self.menuWindow)
        self.menuWindow.addAction(self.viewport_dock.toggleViewAction())
        self.menuWindow.addAction(self.outline_dock.toggleViewAction())
        self.menuWindow.addAction(self.entity_dock.toggleViewAction())
        self.menuWindow.addAction(self.file_explorer_dock.toggleViewAction())

        self.restore_perspectives()

    def init_viewport(self):
        material = self.viewport.manager.viewport_material
        active_scene.add_obj(
            Model(material, geometry=Cube(), name="Cube", position=Vector3((0, 0.5, 0)))
        )
        active_scene.add_obj(
            Model(
                material,
                geometry=Plane(),
                name="Plane",
                scale=Vector3((3, 1, 3)),
                position=Vector3((0, -0.001, 0)),
            )
        )

    def closeEvent(self, event):
        event.accept()

    def save_perspectives(self):
        settings = QSettings("UserPrefs.ini", QSettings.IniFormat)
        self.dock_manager.addPerspective("default")
        self.dock_manager.savePerspectives(settings)

    def restore_perspectives(self):
        settings = QSettings("UserPrefs.ini", QSettings.IniFormat)
        self.dock_manager.loadPerspectives(settings)
        self.dock_manager.openPerspective("default")

    def new_project(self):
        dialog = SaveProjectAs(self, new_project=True)
        dialog.exec()
