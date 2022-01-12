from PyQt5 import uic
import moderngl_window as mglw
from PyQt5.QtWidgets import QMainWindow, QSizePolicy
from PyQt5.QtCore import QSettings, Qt
from PyQtAds.QtAds import ads
from nimble.common.resources import ui_file

from nimble.common.shader_manager import Shaders
from nimble.interface.entity_inspector import ModelWidget
from nimble.interface.outline import OutlineWidget

from nimble.interface.viewport import ViewportWidget
from nimble.objects.material import Material

from nimble.objects.scene import active_scene
from nimble.objects.model import Model
from nimble.objects.geometry import Cube


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowState(Qt.WindowMaximized)
        self.show()
        self.setWindowTitle("Nimble Engine")

        uic.loadUi(ui_file("main_window.ui"), self)

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

        self.entity_dock = ads.CDockWidget("Entity")
        self.dock_manager.addDockWidget(ads.RightDockWidgetArea, self.entity_dock)
        self.entity = ModelWidget()
        self.entity_dock.setWidget(self.entity)

        self.last_mouse_button = None

        self.shift = False
        self.did_drag = False
        self.open_context = None
        self.context_menu_pos = (0, 0)
        self._modifiers = mglw.context.base.KeyModifiers()

        self.actionSave_Layout.triggered.connect(self.save_perspectives)

        self.restore_perspectives()

    def init_viewport(self):
        active_scene.add_obj(
            Model(Material(Shaders()["viewport"]), geometry=Cube(), name="Cube")
        )

    def closeEvent(self, event):
        event.accept()

    def save_perspectives(self):
        settings = QSettings("UserPrefs.ini", QSettings.IniFormat)
        self.dock_manager.savePerspectives(settings)

    def restore_perspectives(self):
        settings = QSettings("UserPrefs.ini", QSettings.IniFormat)
        self.dock_manager.loadPerspectives(settings)
        self.dock_manager.openPerspective("default")
