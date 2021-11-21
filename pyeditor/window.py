import moderngl_window as mglw
import moderngl as mgl
import imgui
from moderngl_window.integrations.imgui import ModernglWindowRenderer
from moderngl_window.opengl.projection import Projection3D
from moderngl_window.scene import camera
from pyrr import Vector3, Matrix44
from model import Cube, Sphere
from shader_manager import global_sm
from resources import resource_dir
from grid import Grid


class WindowEvents(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Py3ditor"
    cursor = True
    vsync = True
    samples = 4

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        imgui.create_context()
        self.imgui_io = imgui.get_io()
        self.imgui_io.fonts.add_font_from_file_ttf(
            str(resource_dir / "fonts/Roboto-Regular.ttf"), 16
        )

        self.last_key = None

        self.imgui = ModernglWindowRenderer(self.wnd)
        self.imgui.refresh_font_texture()

        self.camera = camera.OrbitCamera(
            target=(0.0, 0.0, 0.0),
            radius=2.0,
            aspect_ratio=self.wnd.aspect_ratio,
            near=0.01,
            far=500.0,
        )

        global_sm.load("viewport", str(resource_dir / "shaders/viewport.glsl"))
        global_sm.load("grid", str(resource_dir / "shaders/grid.glsl"))
        self.objects = [Cube(self.camera, global_sm.get("viewport"))]

        self.camera.look_at(vec=Vector3([0.0, 0.0, 0.0]))
        self.camera.angle_x = 90
        self.camera.angle_y = -45

        self.camera.mouse_sensitivity = 1.5

        self.shift = False

        self.grid = Grid(self.camera, 1, self.ctx)

    def render(self, time: float, frametime: float):
        self.ctx.enable_only(mgl.CULL_FACE | mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.clear(0.25, 0.25, 0.25)

        for object in self.objects:
            object.render()
        self.grid.render()

        self.render_ui()

    def render_ui(self):
        imgui.new_frame()
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):

                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", "Cmd+Q", False, True
                )

                if clicked_quit:
                    exit(1)

                imgui.end_menu()
            imgui.end_main_menu_bar()

        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def close(self):
        print("Window is closing")

    def resize(self, width: int, height: int):
        self.camera.projection.update(aspect_ratio=width / height)
        self.imgui.resize(width, height)

    def key_event(self, key, action, modifiers):
        if key == 65505:
            if action == "ACTION_PRESS":
                self.shift = True
            elif action == "ACTION_RELEASE":
                self.shift = False
        self.imgui.key_event(key, action, modifiers)

    def mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        if self.last_key == 2:
            if self.shift:
                # TODO: Fix this
                pass
            else:
                self.camera.rot_state(dx, dy)
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        if y_offset:
            if y_offset > 0 or self.camera.radius < 100:
                self.camera.zoom_state(y_offset * self.camera.radius / 10)
        self.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.last_key = button
        self.imgui.mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)
