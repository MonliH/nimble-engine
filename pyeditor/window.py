import math
import moderngl_window as mglw
import moderngl as mgl
from moderngl_window.geometry import quad_fs
import imgui
from moderngl_window.integrations.imgui import ModernglWindowRenderer
from userspace.shader_manager import global_sm
from common.resources import resource_dir, shader
from interface.grid import Grid
from interface.orbit_camera import OrbitCamera
from userspace.object_manager import ObjectManager
from userspace.model import Model
from userspace.geometry import Cube, Cylinder, Sphere
from pyrr import Matrix33


new_obj_menu = [("Cube", Cube), ("Sphere", Sphere)]


class WindowEvents(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Py3ditor"
    cursor = True
    vsync = True
    samples = 8

    aspect_ratio = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        imgui.create_context()
        self.imgui_io = imgui.get_io()
        self.imgui_io.fonts.add_font_from_file_ttf(
            str(resource_dir / "fonts/Roboto-Regular.ttf"), 16
        )

        self.last_mouse_button = None

        self.imgui = ModernglWindowRenderer(self.wnd)
        self.imgui.refresh_font_texture()
        self.mouse = (0, 0)

        self.camera = OrbitCamera(
            self.wnd.width,
            self.wnd.height,
            radius=3.0,
            near=0.01,
            far=500.0,
        )

        global_sm.load("viewport", shader("viewport.glsl"))
        global_sm.load("grid", shader("grid.glsl"))
        global_sm.load("line", shader("line.glsl"))
        global_sm.load("filter", shader("filter.glsl"))
        global_sm.load("line", shader("line.glsl"))
        self.object_manager = ObjectManager()
        self.active_buffer = self.ctx.framebuffer(
            (self.ctx.texture((self.camera.width, self.camera.height), 4)),
        )

        self.object_manager.add_obj(
            "Cube",
            Model(global_sm["viewport"], Cylinder()),
        )

        self.shift = False
        self.grid = Grid(1, self.ctx)

        self.active_vao = quad_fs()
        self.did_drag = False
        self.open_context = None
        self.context_menu_pos = (0, 0)

    def render(self, time: float, frametime: float):
        self.ctx.enable_only(mgl.CULL_FACE | mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.clear(0.235, 0.235, 0.235)

        self.object_manager.render(self.camera, self.active_buffer, self.ctx.screen)
        self.grid.render(self.camera)

        # Draw active object outline with offscreen buffer
        self.active_buffer.color_attachments[0].use(location=0)
        self.active_buffer.color_attachments[0].repeat_x = False
        self.active_buffer.color_attachments[0].repeat_y = False
        global_sm["filter"]["kernel"].write(
            Matrix33([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype="f4") / 16
        )
        self.active_vao.render(global_sm["filter"])

        self.render_ui()

    def render_ui(self):
        imgui.new_frame()
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):
                clicked_quit, _ = imgui.menu_item("Quit", "Ctrl Q", False, True)

                if clicked_quit:
                    exit(1)

                imgui.end_menu()
            if imgui.begin_menu("Viewport", True):
                clicked_reset_camera_pos, _ = imgui.menu_item(
                    "Reset Camera Position", None, False, True
                )

                if clicked_reset_camera_pos:
                    self.camera.reset_position()

                imgui.end_menu()
            imgui.end_main_menu_bar()

        imgui.begin("Outline")
        imgui.listbox_header("", 200, 100)

        for i, item in enumerate(self.object_manager.objects_list):
            pressed, selected = imgui.selectable(
                item, item == self.object_manager.active
            )

            if pressed and selected:
                self.object_manager.set_active(i)

        imgui.listbox_footer()
        imgui.end()

        if self.open_context is not None:
            imgui.set_next_window_position(
                self.context_menu_pos[0], self.context_menu_pos[1]
            )
            flags = (
                imgui.WINDOW_NO_MOVE
                | imgui.WINDOW_ALWAYS_AUTO_RESIZE
                | imgui.WINDOW_NO_TITLE_BAR
                | imgui.WINDOW_NO_SCROLLBAR
                | imgui.WINDOW_NO_RESIZE
            )
            if self.open_context >= 0:
                if imgui.begin("object-context-menu", flags=flags):
                    imgui.text(
                        f"{self.object_manager.get_obj_name(self.open_context)} Actions"
                    )
                    imgui.separator()
                    _, delete = imgui.selectable("Delete")
                    if delete:
                        self.object_manager.delete_obj(self.open_context)
                        self.open_context = None
                    imgui.end()
            else:
                if imgui.begin("general-context-menu", flags=flags):
                    imgui.text("General Actions")
                    imgui.separator()
                    if imgui.begin_menu("New Object", True):
                        for name, Constructor in new_obj_menu:
                            _, add_obj = imgui.selectable(name)
                            if add_obj:
                                self.object_manager.add_obj(
                                    name,
                                    Model(global_sm["viewport"], Constructor()),
                                )
                                self.open_context = None
                        imgui.end_menu()
                    imgui.end()

        imgui.render()
        self.imgui.render(imgui.get_draw_data())

    def close(self):
        print("Window is closing")

    def resize(self, width: int, height: int):
        self.camera.set_window_size(width, height)
        self.imgui.resize(width, height)

    def key_event(self, key, action, modifiers):
        if not self.imgui_io.want_capture_keyboard:
            if key == 65505:
                if action == "ACTION_PRESS":
                    self.shift = True
                elif action == "ACTION_RELEASE":
                    self.shift = False
            elif key == 65535 and action == "ACTION_PRESS":
                self.object_manager.delete_obj(self.object_manager.active_idx)
            elif (49 <= key <= 51) and action == "ACTION_PRESS":
                if key == 49:
                    # Make camera look from x axis
                    self.camera.spherical.phi = math.pi / 2
                    self.camera.spherical.theta = math.pi / 2
                elif key == 50:
                    # Y axis
                    self.camera.spherical.phi = 0.000000000001
                    self.camera.spherical.theta = 0
                elif key == 51:
                    # Z axis
                    self.camera.spherical.phi = math.pi / 2
                    self.camera.spherical.theta = 0
        self.imgui.key_event(key, action, modifiers)

    def mouse_position_event(self, x, y, dx, dy):
        self.mouse = (x, y)
        self.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.did_drag = True
        if not self.imgui_io.want_capture_mouse:
            if self.last_mouse_button == 2:
                if self.shift:
                    self.camera.pan(dx, dy)
                else:
                    self.camera.rotate(dx, dy)
            self.open_context = None
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        if not self.imgui_io.want_capture_mouse:
            if y_offset:
                if y_offset > 0 or self.camera.radius < 100:
                    self.camera.zoom(y_offset * self.camera.radius / 10)
        self.imgui.mouse_scroll_event(x_offset, y_offset)

    def mouse_press_event(self, x, y, button):
        self.last_mouse_button = button
        if not self.imgui_io.want_capture_mouse:
            if self.last_mouse_button == 1:
                hit_object = self.object_manager.cast_ray(x, y, self.camera)
                if hit_object is not None:
                    self.object_manager.set_active(hit_object[1])
                else:
                    self.object_manager.set_active(-1)
            if self.last_mouse_button != 2:
                self.open_context = None
        self.imgui.mouse_press_event(x, y, button)

    def mouse_release_event(self, x: int, y: int, button: int):
        if not self.imgui_io.want_capture_mouse:
            if button == 2 and not self.did_drag:
                hit_object = self.object_manager.cast_ray(x, y, self.camera)
                self.context_menu_pos = self.mouse
                if hit_object is not None:
                    self.open_context = hit_object[1]
                else:
                    # Show context menu
                    self.open_context = -1
        self.did_drag = False
        self.imgui.mouse_release_event(x, y, button)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)
