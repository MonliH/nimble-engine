from PyQt5.QtCore import Qt
import moderngl_window as mglw
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDockWidget,
    QListView,
    QMainWindow,
)

from nimble.common.shader_manager import Shaders

from nimble.interface.viewport import ViewportWidget

from nimble.objects.scene import active_scene
from nimble.objects.model import Model
from nimble.objects.geometry import Cube


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(100, 100, 1080, 720)
        self.show()
        self.setWindowTitle("Nimble Engine")

        self.isDockNestingEnabled = True

        self.viewport_dock = QDockWidget("Scene Viewer")
        self.addDockWidget(Qt.RightDockWidgetArea, self.viewport_dock)
        self.viewport = ViewportWidget(
            self.viewport_dock,
            on_gl_init=self.init_viewport,
        )
        self.viewport_dock.setWidget(self.viewport)

        self.outline_dock = QDockWidget("Outline")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.outline_dock)
        self.outline = QListView(self.outline_dock)
        self.outline.setModel(active_scene)
        self.outline_dock.setWidget(self.outline)

        self.last_mouse_button = None

        self.shift = False
        self.did_drag = False
        self.open_context = None
        self.context_menu_pos = (0, 0)
        self._modifiers = mglw.context.base.KeyModifiers()

    def init_viewport(self):
        active_scene.add_obj("Cube", Model(Shaders()["viewport"], Cube()))

    def closeEvent(self, event):
        event.accept()
