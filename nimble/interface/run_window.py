from typing import Callable, Optional, cast, Type
import moderngl_window as mglw
import moderngl as mgl
from PyQt5.QtWidgets import QWidget, QPushButton, QMainWindow
from PyQtAds.QtAds import ads
from PyQt5 import QtGui

from nimble.common import current_project, World
from nimble.common.keys import Key, PressedKeys, is_key
from nimble.common.resources import load_ui
from nimble.common.serialize import serialize_scene, unserialize_scene
from nimble.interface.viewport import ViewportWidget, Viewport
from nimble.objects import PhysicsProcessor, ScriptProcessor, Scene, Geometry


class GameViewport(Viewport):
    def __init__(self, *args):
        super().__init__(*args)
        self.world = World()
        self.keys = PressedKeys()
        custom_components = []
        for model in self.scene.objects.values():
            entity_id = self.world.create_entity()
            model.entity_id = entity_id
            for component in model.components:
                self.world.add_component(
                    entity_id, component, type_alias=component.type_alias
                )
                if (
                    component.type_alias is not None
                    and component.type_alias.startswith("custom_")
                ):
                    custom_components.append(component)

        custom_script_processor = ScriptProcessor(custom_components)
        self.world.add_processor(custom_script_processor)
        custom_script_processor.add_keys_attr(self.keys)

        physics_processor = PhysicsProcessor()
        self.world.add_processor(physics_processor)

    def render(self, screen: mgl.Framebuffer):
        self.world.process()

        mglw.activate_context(ctx=self.ctx)
        self.ctx.enable_only(mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.clear(0.235, 0.235, 0.235)
        self.active_buffer.use()
        self.ctx.clear()
        screen.use()

        self.scene.render(self.camera, self.active_buffer, screen)

    def key_released(self, event: QtGui.QKeyEvent):
        key = event.key()
        if is_key(key):
            self.keys[Key(event.key())] = False

    def key_pressed(self, event: QtGui.QKeyEvent):
        key = event.key()
        if is_key(key):
            self.keys[Key(event.key())] = True

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


class GameWindow(QMainWindow):
    def __init__(
        self,
        scene: Scene,
        on_close: Callable[[], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Game")
        self.scene = ViewportWidget(self, viewport=GameViewport, scene=scene)
        self.setCentralWidget(self.scene)
        self.on_close = on_close

        self.resize(1280, 720)

    def closeEvent(self, event):
        self.on_close()


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
        self.window = None

        self.open_window = open_window
        self.setContentsMargins(0, 0, 0, 0)

    def start_game(self):
        self.run.setEnabled(False)
        self.temp_scene = unserialize_scene(serialize_scene(current_project.scene))
        self.window = GameWindow(self.temp_scene, self.stop_game)
        self.window.show()

    def stop_game(self):
        self.window = None
        self.temp_scene = None
        self.run.setEnabled(True)
