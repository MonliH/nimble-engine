import math
from typing import Callable, Optional
from PySide2.QtGui import QSurfaceFormat
import moderngl_window as mglw
import moderngl as mgl
import moderngl_window.context.pyside2
from moderngl_window.geometry import quad_fs
from pyrr import Matrix33
from PySide2.QtCore import QElapsedTimer, QSize, QTimer, Qt
from PySide2.QtWidgets import QDockWidget, QMainWindow, QOpenGLWidget
import PySide2
import logging

from common.shader_manager import global_sm, init_shaders
from common.resources import shader
import common.ray_cast as ray_cast

from interface.grid import Grid
from interface.orbit_camera import OrbitCamera
from interface.object_controls import Axis, AxisArrows

from userspace.object_manager import global_om
from userspace.model import Model
from userspace.geometry import Cube, Cylinder, Sphere


new_obj_menu = [("Cube", Cube), ("Sphere", Sphere), ("Cylinder", Cylinder)]


class QModernGLWidget(QOpenGLWidget):
    def __init__(self, parent=None, on_gl_init: Optional[Callable[[], None]] = None):
        super().__init__(parent)  # fmt, None)
        fmt = QSurfaceFormat()
        fmt.setVersion(4, 1)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setSamples(0)
        self.setFormat(fmt)

        self.timer = QElapsedTimer()
        self.timer.restart()
        self.timer_update = QTimer()
        self.timer_update.timeout.connect(self.update)
        self.timer_update.start(0)

        self.standalone_ctx = mgl.create_standalone_context()
        self.on_gl_init = on_gl_init

        self.camera = None
        self.ctx = None
        self.active_buffer = None
        self.new_active_buffer = None

    def initializeGL(self):
        self.ctx = mgl.create_context()
        mglw.activate_context(ctx=self.ctx)
        self.init()

    def restart(self, w, h):
        self.resize(w, h)
        self.resized(w, h)
        self.ctx.viewport = (0, 0, w, h)
        self.scene = self.__class__.SceneClass(self.ctx, self)

    def resized(self, w: int, h: int):
        if self.camera:
            self.camera.set_window_size(w, h)
        if self.ctx:
            self.new_active_buffer = self.ctx.framebuffer(
                (self.ctx.texture((self.camera.width, self.camera.height), 4)),
            )

    def resizeEvent(self, e: PySide2.QtGui.QResizeEvent):
        size = e.size()
        self.resized(size.width(), size.height())

    def paintGL(self):
        self.screen = self.ctx.detect_framebuffer()
        self.screen.use()
        self.makeCurrent()
        self.render(self.timer.elapsed() / 1000, 0)

    def render(self, _time: float, _frametime: float):
        mglw.activate_context(ctx=self.ctx)
        self.ctx.enable_only(mgl.CULL_FACE | mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.clear(0.235, 0.235, 0.235)
        self.active_buffer.clear()

        global_om.render(self.camera, self.active_buffer, self.ctx.screen)
        self.grid.render(self.camera)

        # Draw active object outline with offscreen buffer
        self.active_buffer.color_attachments[0].use()
        self.active_buffer.color_attachments[0].repeat_x = False
        self.active_buffer.color_attachments[0].repeat_y = False
        global_sm["outline_filter"]["kernel"].write(
            Matrix33([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype="f4") / 16
        )
        self.active_vao.render(global_sm["outline_filter"])

        if global_om.has_object_selected:
            self.ctx.disable(mgl.DEPTH_TEST)
            self.axis.render(self.camera)
            self.ctx.enable(mgl.DEPTH_TEST)
        
        if self.new_active_buffer is not None:
            self.active_buffer = self.new_active_buffer
            self.new_active_buffer = None

    def init(self):
        init_shaders()
        self.ctx.viewport = (0, 0, self.width(), self.height())
        self.grid = Grid(1, self.ctx)

        window_size = self.size()
        self.camera = OrbitCamera(
            window_size.width(),
            window_size.height(),
            radius=3.0,
            near=0.01,
            far=500.0,
        )

        self.regen_active_buffer()

        self.active_vao = quad_fs()
        axis_rel_scale = 0.6
        self.zoom_to_axis_ratio = axis_rel_scale / self.camera.spherical.radius
        self.axis = AxisArrows(axis_rel_scale)

        self.on_gl_init()

    def regen_active_buffer(self):
        mglw.activate_context(ctx=self.ctx)
        if self.active_buffer:
            self.active_buffer.color_attachments[0].release()
            self.active_buffer.release()
        self.active_buffer = self.ctx.framebuffer(
            (self.ctx.texture((self.camera.width, self.camera.height), 4)),
        )

    def key_press_event(self, key, action):
        keys = mglw.context.pyside2.Keys()
        if key == 65505:
            if action == "ACTION_PRESS":
                self.shift = True
            elif action == "ACTION_RELEASE":
                self.shift = False
        elif key == 65535 and action == "ACTION_PRESS":
            global_om.delete_obj(global_om.active_idx)
        elif (keys.NUMBER_1 <= key <= keys.NUMBER_3) and action == "ACTION_PRESS":
            if key == keys.NUMBER_1:
                # Make camera look from x axis
                self.camera.spherical.phi = math.pi / 2
                self.camera.spherical.theta = math.pi / 2
            elif key == keys.NUMBER_2:
                # Y axis
                self.camera.spherical.phi = 0.000000000001
                self.camera.spherical.theta = 0
            elif key == keys.NUMBER_3:
                # Z axis
                self.camera.spherical.phi = math.pi / 2
                self.camera.spherical.theta = 0
        elif key == keys.T and action == "ACTION_PRESS":
            # T for translate
            self.axis.start_translate({Axis.X, Axis.Y, Axis.Z})
        elif key == keys.R and action == "ACTION_PRESS":
            # R for rotate
            pass
        elif key == keys.S and action == "ACTION_PRESS":
            # S for scale
            pass


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(100, 100, 1080, 720)
        self.show()

        self.dock = QDockWidget("Scene Viewer")
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.widget = QModernGLWidget(
            self.dock,
            on_gl_init=lambda: global_om.add_obj(
                "Cube", Model(global_sm["viewport"], Cube())
            ),
        )
        self.dock.setWidget(self.widget)
        self.dock.setMinimumWidth(300)

        self.last_mouse_button = None

        self.mouse = (0, 0)

        self.shift = False
        self.did_drag = False
        self.open_context = None
        self.context_menu_pos = (0, 0)
        self._modifiers = mglw.context.base.KeyModifiers()

    def closeEvent(self, event):
        event.accept()

    def keyPressEvent(self, event: PySide2.QtGui.QKeyEvent):
        self.widget.key_press_event(event.key(), "ACTION_PRESS")

    def keyReleaseEvent(self, event: PySide2.QtGui.QKeyEvent):
        self.widget.key_press_event(event.key(), "ACTION_RELEASE")


class WindowEvents(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Nimble Engine"
    cursor = True
    vsync = True
    samples = 8

    aspect_ratio = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def close(self):
        print("Window is closing")

    def mouse_position_event(self, x, y, dx, dy):
        self.mouse = (x, y)
        if self.axis.translating:
            self.axis.did_drag(self.camera, x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.did_drag = True
        if self.last_mouse_button == 1:
            self.axis.did_drag(self.camera, x, y, dx, dy)
        elif self.last_mouse_button == 2:
            if self.shift:
                self.camera.pan(dx, dy)
            else:
                self.camera.rotate(dx, dy)
        self.open_context = None

    def mouse_scroll_event(self, x_offset, y_offset):
        if y_offset:
            if y_offset > 0 or self.camera.radius < 100:
                self.camera.zoom(y_offset * self.camera.radius / 10)
                self.axis.set_scale(self.camera.radius * self.zoom_to_axis_ratio)

    def mouse_press_event(self, x, y, button):
        self.last_mouse_button = button
        if self.last_mouse_button == 1:
            # Maybe pressed on axis
            axis = None

            if global_om.has_object_selected:
                ray = ray_cast.get_ray(x, y, self.camera)
                if ray_cast.does_intersect(self.axis.x.bounding_box, ray):
                    axis = Axis.X
                elif ray_cast.does_intersect(self.axis.y.bounding_box, ray):
                    axis = Axis.Y
                elif ray_cast.does_intersect(self.axis.z.bounding_box, ray):
                    axis = Axis.Z

            if axis is not None:
                self.axis.start_drag(axis)
            else:
                hit_object = global_om.cast_ray(x, y, self.camera)
                if hit_object is not None:
                    global_om.set_active(hit_object[1])
                    self.axis.set_active(global_om.get_active(), self.camera)
                else:
                    global_om.set_active(-1)
        if self.last_mouse_button != 2:
            self.open_context = None

    def mouse_release_event(self, x: int, y: int, button: int):
        if button == 2 and not self.did_drag:
            hit_object = global_om.cast_ray(x, y, self.camera)
            self.context_menu_pos = self.mouse
            if hit_object is not None:
                self.open_context = hit_object[1]
            else:
                # Show context menu
                self.open_context = -1
        self.did_drag = False
        self.axis.stop_drag()
