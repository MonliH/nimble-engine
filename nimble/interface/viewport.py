import math
from typing import Callable, Optional
from PySide2 import QtWidgets
from PySide2.QtCore import SIGNAL, QElapsedTimer, QObject, QPoint, QTimer, Qt
from PySide2.QtWidgets import QAction, QMenu, QOpenGLWidget
import moderngl_window as mglw
import moderngl as mgl
from moderngl_window.geometry.quad import quad_fs
from pyrr.objects.matrix33 import Matrix33
from PySide2 import QtGui

from nimble.common.models import ray_cast
from nimble.common.shader_manager import Shaders
from nimble.common.event_listener import InputObserver, WindowObserver
from nimble.common.models.size import ViewportSize
from nimble.interface.orbit_camera import OrbitCamera
from nimble.objects.geometry import Cube, Cylinder, Geometry, Sphere
from nimble.objects.model import Model
from nimble.objects.scene import Scene, active_scene
from nimble.interface.overlays.grid import Grid
from nimble.interface.overlays.object_controls import Axis, TransformTools

new_obj_menu = [("Cube", Cube), ("Sphere", Sphere), ("Cylinder", Cylinder)]


class Viewport(InputObserver, WindowObserver):
    def __init__(
        self, scene: Scene, width: int, height: int, parent: QtWidgets.QWidget
    ):
        self.screen_size = ViewportSize(width, height)
        self.camera = OrbitCamera(
            self.screen_size,
            radius=3.0,
            near=0.01,
            far=500.0,
        )

        self.scene = scene
        self.active_buffer = None
        self.prev_mouse_pos = None
        self.did_drag = False

        self.parent = parent

        self.create_menu_items(self.parent)

    def init(self, ctx: mgl.Context):
        self.ctx = ctx
        self.grid = Grid(1, self.ctx)
        axis_rel_scale = 0.6
        self.zoom_to_axis_ratio = axis_rel_scale / self.camera.spherical.radius
        self.active_tools = TransformTools(0.6)
        self.active_vao = quad_fs()

    def render(self, screen: mgl.Framebuffer):
        mglw.activate_context(ctx=self.ctx)
        self.ctx.enable_only(mgl.CULL_FACE | mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.clear(0.235, 0.235, 0.235)
        self.active_buffer.use()
        self.ctx.clear()
        screen.use()

        self.scene.render(self.camera, self.active_buffer, screen)
        self.grid.render(self.camera)

        # Draw active object outline with offscreen buffer
        self.active_buffer.color_attachments[0].use(location=0)
        self.active_buffer.color_attachments[0].repeat_x = False
        self.active_buffer.color_attachments[0].repeat_y = False
        Shaders()["outline_filter"]["width"] = self.screen_size.width
        Shaders()["outline_filter"]["height"] = self.screen_size.height
        Shaders()["outline_filter"]["kernel"].write(
            Matrix33([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype="f4") / 16
        )
        screen.use()
        self.active_vao.render(Shaders()["outline_filter"])

        if self.scene.has_object_selected:
            self.ctx.disable(mgl.DEPTH_TEST)
            self.active_tools.render(self.camera)
            self.ctx.enable(mgl.DEPTH_TEST)

    def regen_active_buffer(self):
        mglw.activate_context(ctx=self.ctx)
        if self.active_buffer:
            self.active_buffer.color_attachments[0].release()
            self.active_buffer.release()
            self.active_buffer = None
        self.active_buffer = self.ctx.framebuffer(
            (self.ctx.texture(self.screen_size.as_tuple, 4, samples=4),),
        )

    def window_resized(self, width: int, height: int):
        self.screen_size.set_dims(width, height)
        self.regen_active_buffer()

    def key_released(self, event: QtGui.QKeyEvent):
        pass

    def key_pressed(self, event: QtGui.QKeyEvent):
        key = event.key()
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
            self.active_tools.start_translate({Axis.X, Axis.Y, Axis.Z})
        elif key == Qt.Key_R:
            # R for rotate
            pass
        elif key == Qt.Key_S:
            # S for scale
            pass

    def mouse_pressed(self, event: QtGui.QMouseEvent):
        x, y, button = event.x(), event.y(), event.button()
        self.last_mouse_button = button
        if self.last_mouse_button == Qt.LeftButton:
            # Maybe pressed on axis
            axis = None

            if self.scene.has_object_selected:
                ray = ray_cast.get_ray(x, y, self.camera)
                if ray_cast.does_intersect(self.active_tools.x.bounding_box, ray):
                    axis = Axis.X
                elif ray_cast.does_intersect(self.active_tools.y.bounding_box, ray):
                    axis = Axis.Y
                elif ray_cast.does_intersect(self.active_tools.z.bounding_box, ray):
                    axis = Axis.Z

            if axis is not None:
                self.active_tools.start_drag(axis)
            else:
                ray = ray_cast.get_ray(x, y, self.camera)
                hit_object = self.scene.cast_ray(ray)
                if hit_object is not None:
                    self.scene.set_active(hit_object[1])
                    self.active_tools.set_active(self.scene.get_active(), self.camera)
                else:
                    self.scene.set_active(-1)
        if self.last_mouse_button != Qt.RightButton:
            self.open_context = None

    def mouse_moved(self, event: QtGui.QMouseEvent):
        last_pos = x, y = event.x(), event.y()
        if self.prev_mouse_pos is not None:
            dx, dy = x - self.prev_mouse_pos[0], y - self.prev_mouse_pos[1]
            button = event.buttons()
            if button != Qt.NoButton:
                if abs(dx) > 0.1 and abs(dx) > 0.1:
                    self.did_drag = True

            if button == Qt.LeftButton:
                self.active_tools.did_drag(self.camera, x, y, dx, dy)
            elif button == Qt.RightButton:
                if event.modifiers() == Qt.ShiftModifier:
                    self.camera.pan(dx, dy)
                else:
                    self.camera.rotate(dx, dy)
            self.open_context = None
        self.prev_mouse_pos = last_pos

    def mouse_released(self, event: QtGui.QMouseEvent):
        x, y, button = event.x(), event.y(), event.button()
        if button == Qt.RightButton and not self.did_drag:
            ray = ray_cast.get_ray(x, y, self.camera)
            hit_object = self.scene.cast_ray(ray)
            self.context_menu_pos = (x, y)
            if hit_object is not None:
                self.open_context = hit_object[1]
            else:
                # Show context menu
                self.open_context = -1
            self.show_context(x, y, self.parent)
        self.did_drag = False
        self.prev_mouse_pos = None
        self.last_mouse_button = Qt.NoButton
        self.active_tools.stop_drag()

    def scrolled(self, event: QtGui.QWheelEvent):
        y_offset = event.angleDelta().y() / 120
        if y_offset:
            if y_offset > 0 or self.camera.radius < 100:
                self.camera.zoom(y_offset * self.camera.radius / 10)
                self.active_tools.set_scale(
                    self.camera.radius * self.zoom_to_axis_ratio
                )

    def create_menu_items(self, parent: QtWidgets.QWidget):
        self.act_add_cube = QAction("Add Cube", parent)
        self.act_add_sphere = QAction("Add Sphere", parent)
        self.act_add_cylinder = QAction("Add Cylinder", parent)
        QObject.connect(
            self.act_add_cube,
            SIGNAL("triggered()"),
            lambda: self.add_obj(Cube(), "Cube"),
        )
        QObject.connect(
            self.act_add_sphere,
            SIGNAL("triggered()"),
            lambda: self.add_obj(Sphere(), "Sphere"),
        )
        QObject.connect(
            self.act_add_cylinder,
            SIGNAL("triggered()"),
            lambda: self.add_obj(Cylinder(), "Cylinder"),
        )

        self.act_delete_current = QAction("Delete", parent)
        QObject.connect(
            self.act_delete_current, SIGNAL("triggered()"), self.delete_current
        )

    def add_obj(self, geometry: Geometry, name: str):
        self.scene.add_obj(name, Model(Shaders()["viewport"], geometry))

    def delete_current(self):
        self.scene.delete_obj(self.open_context)

    def show_context(self, x: int, y: int, parent: QtWidgets.QWidget):
        menu = QMenu("Context Menu", parent)
        clicked_object = self.open_context
        if clicked_object == -1:
            # No selected object, show general menu
            menu.addSection("General actions")
            menu.addAction(self.act_add_cube)
            menu.addAction(self.act_add_sphere)
            menu.addAction(self.act_add_cylinder)
        else:
            menu.addSection(f'"{self.scene.get_obj_name(clicked_object)}" actions')
            menu.addAction(self.act_delete_current)

        menu.popup(parent.mapToGlobal(QPoint(x, y)))

    def window_resized(self, width: int, height: int):
        self.screen_size.set_dims(width, height)
        self.regen_active_buffer()
        self.camera.window_resized()


class ViewportWidget(QOpenGLWidget):
    def __init__(self, parent=None, on_gl_init: Optional[Callable[[], None]] = None):
        super().__init__(parent)  # fmt, None)
        fmt = QtGui.QSurfaceFormat()
        fmt.setVersion(4, 3)
        fmt.setProfile(QtGui.QSurfaceFormat.CoreProfile)
        fmt.setSamples(8)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.setFormat(fmt)

        self.timer = QElapsedTimer()
        self.timer.restart()
        self.timer_update = QTimer()
        self.timer_update.timeout.connect(self.update)
        self.timer_update.start(0)

        self.standalone_ctx = mgl.create_standalone_context()
        self.on_gl_init = on_gl_init

        self.ctx = None

        self.last_mouse = None
        self.shift = False

        self.did_drag = False
        self.open_context = None
        self.last_mouse_button = Qt.NoButton

        self.manager = Viewport(active_scene, self.width(), self.height(), self)

    def initializeGL(self):
        self.ctx = mgl.create_context(require=430)
        mglw.activate_context(ctx=self.ctx)
        self.init()

    def init(self):
        Shaders().load_defaults()
        self.ctx.viewport = (0, 0, self.width(), self.height())
        self.manager.init(self.ctx)

        self.on_gl_init()

    def restart(self, w, h):
        self.resize(w, h)
        self.resizeGL(w, h)
        self.ctx.viewport = (0, 0, w, h)

    def resizeGL(self, w: int, h: int):
        if self.ctx:
            self.ctx.viewport = (0, 0, w, h)

        self.manager.window_resized(w, h)

    def paintGL(self):
        mglw.activate_context(ctx=self.ctx)
        self.screen = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        self.screen.use()
        self.makeCurrent()
        self.render(self.timer.elapsed() / 1000, 0)

    def render(self, _time: float, _frametime: float):
        self.manager.render(self.screen)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        super().keyPressEvent(event)
        self.manager.key_pressed(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        super().keyReleaseEvent(event)
        self.manager.key_released(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super().mousePressEvent(event)
        self.manager.mouse_pressed(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        super().mouseReleaseEvent(event)
        self.manager.mouse_released(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super().mouseMoveEvent(event)
        self.manager.mouse_moved(event)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        super().wheelEvent(event)
        self.manager.scrolled(event)
