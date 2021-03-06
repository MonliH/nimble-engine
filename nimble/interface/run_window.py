from typing import Callable, Optional, cast, Type
import moderngl_window as mglw
import moderngl as mgl
from PyQt5.QtWidgets import QWidget, QPushButton, QMainWindow
from PyQtAds.QtAds import ads
from PyQt5 import QtGui

from nimble.common import current_project, Key, PressedKeys, is_key
from nimble.common.overlay.overlay import OverlayProcessor
from nimble.common.shader_manager import Shaders
from nimble.common.world import World
from nimble.common.resources import load_ui
from nimble.common.serialize import serialize_scene, unserialize_scene
from nimble.interface.viewport import ViewportWidget, Viewport
from nimble.objects import PhysicsProcessor, ScriptProcessor, Scene, Geometry
from nimble.objects.component import CameraComponent


class GameViewport(Viewport):
    """A subclass of the viewport for the actual game, without a
    grid or active object indicator."""

    def __init__(self, *args):
        super().__init__(*args)
        self.world = World()
        camera = self.world.create_entity()
        self.world.add_component(camera, CameraComponent(self.camera))

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
        self.world.add_processor(custom_script_processor, priority=1)
        custom_script_processor.add_keys_attr(self.keys)

        physics_processor = PhysicsProcessor()
        self.world.add_processor(physics_processor)

        self.overlay_buffer = None
        self.overlay_processor = OverlayProcessor(self.overlay_buffer)
        self.world.add_processor(self.overlay_processor)

    def regen_active_buffer(self):
        super().regen_active_buffer()
        if self.overlay_buffer:
            self.overlay_buffer.release()
            self.overlay_buffer = None

        self.overlay_buffer = self.ctx.texture(self.screen_size.as_tuple, 4)
        self.overlay_processor.texture_resized(self.overlay_buffer)

    def render(self, screen: mgl.Framebuffer):
        self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        self.world.process()
        mglw.activate_context(ctx=self.ctx)
        self.ctx.enable(mgl.BLEND | mgl.DEPTH_TEST)
        self.ctx.clear(0.235, 0.235, 0.235)
        screen.use()

        self.scene.render(self.camera, self.active_buffer, screen)
        self.overlay_buffer.use(location=0)
        self.overlay_buffer.repeat_x = False
        self.overlay_buffer.repeat_y = False
        texture_shader = Shaders()["texture"]

        self.ctx.enable(mgl.BLEND)
        self.overlay_vao.render(texture_shader)

    def key_released(self, event: QtGui.QKeyEvent):
        key = event.key()
        if is_key(key):
            self.keys[Key(event.key())] = False

    def key_pressed(self, event: QtGui.QKeyEvent):
        key = event.key()
        if is_key(key):
            self.keys[Key(event.key())] = True

    # Ignore all of these events for now
    # fmt: off
    def mouse_pressed(self, event: QtGui.QMouseEvent): pass
    def mouse_moved(self, event: QtGui.QMouseEvent): pass
    def mouse_released(self, event: QtGui.QMouseEvent): pass
    def scrolled(self, event: QtGui.QWheelEvent): pass
    def create_menu_items(self, parent: QWidget): pass
    def add_obj(self, name: str, cons: Type[Geometry]): pass
    def delete_current(self): pass
    def show_context(self, x: int, y: int, parent: QWidget): pass
    # fmt: on


class GameWindow(QMainWindow):
    """A Qt window that contains a viewport for the game."""

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
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        load_ui(":/ui/run_tools.ui", self)
        self.run = cast(QPushButton, self.run)
        self.run.pressed.connect(self.start_game)
        self.temp_scene: Optional[Scene] = None
        self.window = None

        self.setContentsMargins(0, 0, 0, 0)

    def start_game(self):
        self.run.setEnabled(False)

        # Create a new copy of the scene by serializing it then unserializing it
        self.temp_scene = unserialize_scene(serialize_scene(current_project.scene))

        self.window = GameWindow(self.temp_scene, self.stop_game)
        self.window.show()

    def stop_game(self):
        self.window = None
        self.temp_scene = None
        self.run.setEnabled(True)
