import math
from typing import Callable, Optional
from PySide2 import QtCore
from PySide2.QtCore import Qt
from PySide2.QtGui import QSurfaceFormat
import moderngl_window as mglw
import moderngl as mgl
from moderngl_window.geometry import quad_fs
from pyrr import Matrix33
from PySide2.QtCore import QElapsedTimer,  QTimer, Qt
from PySide2.QtWidgets import QDockWidget, QMainWindow, QOpenGLWidget
from PySide2 import QtGui
import PySide2

from common.shader_manager import global_sm, init_shaders
import common.ray_cast as ray_cast

from interface.grid import Grid
from interface.orbit_camera import OrbitCamera
from interface.object_controls import Axis, AxisArrows

from userspace.object_manager import global_om
from userspace.model import Model
from userspace.geometry import Cube, Cylinder, Sphere


new_obj_menu = [("Cube", Cube), ("Sphere", Sphere), ("Cylinder", Cylinder)]
class ActionType:
    KEY_PRESS = 0
    KEY_RELEASE = 1


class QModernGLWidget(QOpenGLWidget):
    keyPressed = QtCore.Signal(QtCore.QEvent)
    keyReleased = QtCore.Signal(QtCore.QEvent)
    mouseMoved = QtCore.Signal(QtCore.QEvent)
    mousePressed = QtCore.Signal(QtCore.QEvent)
    mouseReleased = QtCore.Signal(QtCore.QEvent)
    scrolled = QtCore.Signal(QtCore.QEvent)

    def __init__(self, parent=None, on_gl_init: Optional[Callable[[], None]] = None):
        super().__init__(parent)  # fmt, None)
        fmt = QSurfaceFormat()
        fmt.setVersion(4, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setSamples(8)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.keyPressed.connect(self.on_key_press)
        self.keyReleased.connect(self.on_key_release)

        self.mouseMoved.connect(self.on_mouse_move)
        self.mousePressed.connect(self.on_mouse_press)
        self.mouseReleased.connect(self.on_mouse_release)

        self.scrolled.connect(self.on_scroll)

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

        self.last_mouse = None
        self.last_mouse_button = None
        self.shift = False

    def initializeGL(self):
        self.ctx = mgl.create_context(require=430)
        mglw.activate_context(ctx=self.ctx)
        self.init()

    def restart(self, w, h):
        self.resize(w, h)
        self.resizeGL(w, h)
        self.ctx.viewport = (0, 0, w, h)

    def resizeGL(self, w: int, h: int):
        if self.camera:
            self.camera.set_window_size(w, h)
        if self.ctx:
            self.regen_active_buffer()
            self.ctx.viewport = (0, 0, w, h)

    def paintGL(self):
        mglw.activate_context(ctx=self.ctx)
        self.screen = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        self.screen.use()
        self.makeCurrent()
        self.render(self.timer.elapsed() / 1000, 0)

    def render(self, _time: float, _frametime: float):
        mglw.activate_context(ctx=self.ctx)
        self.ctx.enable_only(mgl.CULL_FACE | mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.clear(0.235, 0.235, 0.235)
        self.active_buffer.use()
        self.ctx.clear()
        self.screen.use()

        global_om.render(self.camera, self.active_buffer, self.screen)
        self.grid.render(self.camera)

        # Draw active object outline with offscreen buffer
        self.active_buffer.color_attachments[0].use(location=0)
        self.active_buffer.color_attachments[0].repeat_x = False
        self.active_buffer.color_attachments[0].repeat_y = False
        global_sm["outline_filter"]["width"] = self.camera.width
        global_sm["outline_filter"]["height"] = self.camera.height
        global_sm["outline_filter"]["kernel"].write(
            Matrix33([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype="f4") / 16
        )
        self.screen.use()
        self.active_vao.render(global_sm["outline_filter"])

        if global_om.has_object_selected:
            self.ctx.disable(mgl.DEPTH_TEST)
            self.axis.render(self.camera)
            self.ctx.enable(mgl.DEPTH_TEST)

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
            self.active_buffer = None
        self.active_buffer = self.ctx.framebuffer(
            (self.ctx.texture((self.camera.width, self.camera.height), 4, samples=4),),
        )

    def key_press_event(self, key, action: ActionType):
        if action == ActionType.KEY_RELEASE:
            if key == Qt.Key_Shift:
                self.shift = False
        if action == ActionType.KEY_PRESS:
            if key == Qt.Key_Shift:
                self.shift = True
            elif key == Qt.Key_Delete:
                global_om.delete_obj(global_om.active_idx)
            if key == Qt.Key_1:
                # Make camera look from x axis
                self.camera.spherical.phi = math.pi / 2
                self.camera.spherical.theta = math.pi / 2
            elif key == Qt.Key_2:
                # Y axis
                self.camera.spherical.phi = 0.000000000001
                self.camera.spherical.theta = 0
            elif key == Qt.Key_3:
                # Z axis
                self.camera.spherical.phi = math.pi / 2
                self.camera.spherical.theta = 0
            elif key == Qt.Key_T:
                # T for translate
                self.axis.start_translate({Axis.X, Axis.Y, Axis.Z})
            elif key == Qt.Key_R:
                # R for rotate
                pass
            elif key == Qt.Key_S:
                # S for scale
                pass

    def on_key_press(self, event: QtGui.QKeyEvent):
        self.key_press_event(event.key(), ActionType.KEY_PRESS)

    def on_key_release(self, event: QtGui.QKeyEvent):
        self.key_press_event(event.key(), ActionType.KEY_RELEASE)

    def on_mouse_press(self, event: QtGui.QMouseEvent):
        x, y, button = event.x(), event.y(), event.button()
        self.last_mouse_button = button
        if self.last_mouse_button == Qt.LeftButton:
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
        if self.last_mouse_button != Qt.RightButton:
            self.open_context = None
    
    def on_mouse_move(self, event: QtGui.QMouseEvent):
        last_pos = x, y = event.x(), event.y()
        if self.last_mouse is not None:
            dx, dy = x - self.last_mouse[0], y - self.last_mouse[1]
            self.did_drag = True
            if self.last_mouse_button == Qt.LeftButton:
                self.axis.did_drag(self.camera, x, y, dx, dy)
            elif self.last_mouse_button == Qt.RightButton:
                if self.shift:
                    self.camera.pan(dx, dy)
                else:
                    self.camera.rotate(dx, dy)
            self.open_context = None
        self.last_mouse = last_pos

    def on_mouse_release(self, event: QtGui.QMouseEvent):
        x, y, button = event.x(), event.y(), event.button()
        if button == Qt.RightButton and not self.did_drag:
            hit_object = global_om.cast_ray(x, y, self.camera)
            self.context_menu_pos = (x, y)
            if hit_object is not None:
                self.open_context = hit_object[1]
            else:
                # Show context menu
                self.open_context = -1
        self.did_drag = False
        self.last_mouse = None
        self.last_mouse_button = None
        self.axis.stop_drag()

    def on_scroll(self, event: QtGui.QWheelEvent):
        y_offset = event.angleDelta().y()/120
        if y_offset:
            if y_offset > 0 or self.camera.radius < 100:
                self.camera.zoom(y_offset * self.camera.radius / 10)
                self.axis.set_scale(self.camera.radius * self.zoom_to_axis_ratio)
    
    def keyPressEvent(self, event: PySide2.QtGui.QKeyEvent):
        super().keyPressEvent(event)
        self.keyPressed.emit(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        super().keyReleaseEvent(event)
        self.keyReleased.emit(event)
    
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super().mousePressEvent(event)
        self.mousePressed.emit(event)
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        super().mouseReleaseEvent(event)
        self.mouseReleased.emit(event)
    
    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super().mouseMoveEvent(event)
        self.mouseMoved.emit(event)
    
    def wheelEvent(self, event: QtGui.QWheelEvent):
        super().wheelEvent(event)
        self.scrolled.emit(event)
    
    def contextMenuEvent(self, event: PySide2.QtGui.QContextMenuEvent):
        print("hi")
        super().contextMenuEvent(event)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(100, 100, 1080, 720)
        self.show()

        self.dock = QDockWidget("Scene Viewer")
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.widget = QModernGLWidget(
            self.dock,
            on_gl_init=self.init_viewport,
        )
        self.dock.setWidget(self.widget)
        self.dock.setMinimumWidth(300)

        self.last_mouse_button = None

        self.shift = False
        self.did_drag = False
        self.open_context = None
        self.context_menu_pos = (0, 0)
        self._modifiers = mglw.context.base.KeyModifiers()
    
    def init_viewport(self):
        global_om.add_obj( "Cube", Model(global_sm["viewport"], Cube()))

    def closeEvent(self, event):
        event.accept()
