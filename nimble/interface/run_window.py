from typing import Callable, Optional, cast, Type
import moderngl_window as mglw
import moderngl as mgl
from PyQt5.QtWidgets import QWidget, QPushButton
from PyQtAds.QtAds import ads
from PyQt5 import QtGui

from nimble.common.resources import load_ui
from nimble.common.serialize import serialize_scene, unserialize_scene
from nimble.interface.viewport import ViewportWidget, Viewport
from nimble.objects.project import current_project
from nimble.objects.scene import Scene
from nimble.objects.geometry import Geometry


class GameViewport(Viewport):
    def render(self, screen: mgl.Framebuffer):
        for model in self.scene.objects.values():
            for component in model.components:
                if not component.inited:
                    component.init()
                    component.inited = True
                component.tick()

        mglw.activate_context(ctx=self.ctx)
        self.ctx.enable_only(mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.clear(0.235, 0.235, 0.235)
        self.active_buffer.use()
        self.ctx.clear()
        screen.use()

        self.scene.render(self.camera, self.active_buffer, screen)

    def key_released(self, event: QtGui.QKeyEvent):
        pass

    def key_pressed(self, event: QtGui.QKeyEvent):
        pass

    def mouse_pressed(self, event: QtGui.QMouseEvent):
        pass

    def mouse_moved(self, event: QtGui.QMouseEvent):
        pass

    def mouse_released(self, event: QtGui.QMouseEvent):
        pass

    def scrolled(self, event: QtGui.QWheelEvent):
        pass

    def create_menu_items(self, parent: QWidget):
        pass

    def add_obj(self, name: str, cons: Type[Geometry]):
        pass

    def delete_current(self):
        pass

    def show_context(self, x: int, y: int, parent: QWidget):
        pass


class RunWindow(QWidget):
    def __init__(
        self,
        open_window: Callable[[ads.CDockWidget], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        load_ui(":/ui/run_tools.ui", self)
        self.run = cast(QPushButton, self.run)
        self.run.pressed.connect(self.start_game)
        self.temp_scene: Optional[Scene] = None
        self.temp_window = None

        self.open_window = open_window

    def start_game(self):
        self.temp_scene = unserialize_scene(serialize_scene(current_project.scene))
        self.dock_widget = ads.CDockWidget("Game")
        self.temp_window = ViewportWidget(viewport=GameViewport, scene=self.temp_scene)
        self.dock_widget.setWidget(self.temp_window)
        self.open_window(self.dock_widget)
