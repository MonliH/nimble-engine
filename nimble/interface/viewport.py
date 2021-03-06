import math
from typing import Callable, Optional, Type
from PyQt5 import QtWidgets
from PyQt5.QtCore import QElapsedTimer, QPoint, QTimer, Qt
from PyQt5.QtWidgets import QAction, QMenu, QOpenGLWidget
from PyQt5 import QtGui
import moderngl_window as mglw
import moderngl as mgl
from moderngl_window.geometry.quad import quad_fs
from pyrr.objects.matrix33 import Matrix33

from nimble.common.models import ray_cast
from nimble.common import current_project, Shaders
from nimble.common.event_listener import InputObserver, WindowObserver
from nimble.common.models.size import ViewportSize
from nimble.interface.orbit_camera import OrbitCamera
from nimble.objects import (
    Cube,
    Cylinder,
    Geometry,
    Plane,
    Sphere,
    Material,
    Model,
    Scene,
)
from nimble.interface.overlays.grid import Grid
from nimble.interface.overlays.object_controls import Axis, TransformTools

new_obj_menu = {"Cube": Cube, "Sphere": Sphere, "Cylinder": Cylinder, "Plane": Plane}


class Viewport(InputObserver, WindowObserver):
    """The main 3D viewport in the nimble editor."""

    def __init__(
        self, scene: Scene, width: int, height: int, parent: QtWidgets.QWidget
    ):
        self.screen_size = ViewportSize(width, height)
        self.camera = OrbitCamera(
            self.screen_size,
            radius=6.0,
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
        """Initialize the viewport after the OpenGl context has been created."""
        self.ctx = ctx

        # Create a grid
        self.grid = Grid(1, self.ctx)
        axis_rel_scale = 0.7

        # Create the transform tools (the arrows)
        self.zoom_to_axis_ratio = axis_rel_scale / self.camera.spherical.radius
        self.active_tools = TransformTools(axis_rel_scale, self.camera)

        self.scene.register_active_obj_observer(self.active_tools, "active_obj_tools")
        self.scene.register_observer(self.active_tools)

        # Create the overlay vertex array, which is just a fullscreen quad
        # This overlay is used to draw the outline of the active object, and
        # to draw 2D overlays in the actual game
        self.overlay_vao = quad_fs()

    def render(self, screen: mgl.Framebuffer):
        mglw.activate_context(ctx=self.ctx)
        self.ctx.enable_only(mgl.DEPTH_TEST | mgl.BLEND)
        self.ctx.clear(0.235, 0.235, 0.235)
        self.active_buffer.use()
        self.ctx.clear()
        screen.use()

        self.scene.render(self.camera, self.active_buffer, screen)
        self.grid.render(self.camera)

        # Draw active object outline to the offscreen buffer
        self.active_buffer.color_attachments[0].use(location=0)
        self.active_buffer.color_attachments[0].repeat_x = False
        self.active_buffer.color_attachments[0].repeat_y = False

        # The "outline_filter" shader creates an outline by blurring the active object
        # then drawing the edge with a solid color that has an alpha based off of the
        # original object's alpha
        Shaders()["outline_filter"]["width"] = self.screen_size.width
        Shaders()["outline_filter"]["height"] = self.screen_size.height
        Shaders()["outline_filter"]["kernel"].write(
            Matrix33([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype="f4") / 16
        )
        screen.use()
        self.overlay_vao.render(Shaders()["outline_filter"])

        # Render the active object tools if there is an active object
        if self.scene.has_object_selected:
            self.ctx.disable(mgl.DEPTH_TEST)
            self.active_tools.render()
            self.ctx.enable(mgl.DEPTH_TEST)

    def regen_active_buffer(self):
        """Regenerate the offscreen buffer used to draw the object overlays.
        Used when the window is resized."""

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
        elif key == Qt.Key_Delete:
            self.scene.delete_obj(self.scene.active_idx)

    def mouse_pressed(self, event: QtGui.QMouseEvent):
        x, y, button = event.x(), event.y(), event.button()
        self.last_mouse_button = button
        if self.last_mouse_button == Qt.LeftButton:
            # Maybe pressed on axis
            axis = None

            if self.scene.has_object_selected:
                # Check if the mouse has pressed any of the transform controls
                ray = ray_cast.get_ray(x, y, self.camera)
                if ray_cast.does_intersect(self.active_tools.x.bounding_box, ray):
                    axis = Axis.X
                elif ray_cast.does_intersect(self.active_tools.y.bounding_box, ray):
                    axis = Axis.Y
                elif ray_cast.does_intersect(self.active_tools.z.bounding_box, ray):
                    axis = Axis.Z

            if axis is not None:
                # Start the transform tool if the mouse is pressed on an axis
                self.active_tools.start_drag(axis)
            else:
                # check if the mouse has hit any other objects, and if so, select them
                ray = ray_cast.get_ray(x, y, self.camera)
                hit_object = self.scene.cast_ray(ray)
                if hit_object is not None:
                    self.scene.set_active(hit_object[1])
                else:
                    self.scene.set_active(-1)

        if self.last_mouse_button != Qt.RightButton:
            self.open_context = None  # Reset the context menu

    def mouse_moved(self, event: QtGui.QMouseEvent):
        last_pos = x, y = event.x(), event.y()
        if self.prev_mouse_pos is not None:
            # Get the mouse delta
            dx, dy = x - self.prev_mouse_pos[0], y - self.prev_mouse_pos[1]
            button = event.buttons()

            if button != Qt.NoButton:
                min_speed = 0.1
                if abs(dx) > min_speed and abs(dx) > min_speed:
                    # Only set drag if the mouse has moved more than a certain threshold
                    self.did_drag = True

            self.active_tools.did_drag(x, y, dx, dy)
            if button == Qt.RightButton:
                if event.modifiers() == Qt.ShiftModifier:
                    # Pan the camera if the shift key is held down
                    self.camera.pan(dx, dy)
                else:
                    # Otherwise rotate the camera
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
                # Show object specific context menu if the mouse is released on an object
                self.open_context = hit_object[1]
            else:
                # Show context menu if the mouse is released outside of any objects
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
                # Zoom in or out if the mouse wheel is scrolled on the y axis
                self.camera.zoom(y_offset * self.camera.radius / 10)
                self.active_tools.set_scale(
                    self.camera.radius * self.zoom_to_axis_ratio
                )

    def create_menu_items(self, parent: QtWidgets.QWidget):
        self.general_actions = []
        self.obj_selected_actions = []

        for disp_name, obj in new_obj_menu.items():
            action = QAction(disp_name, parent)
            self.general_actions.append(action)
            action.triggered.connect(
                lambda _, disp_name=disp_name, obj=obj: self.add_obj(disp_name, obj)
            )

        delete = QAction("Delete", parent)
        self.obj_selected_actions.append(delete)
        delete.triggered.connect(self.delete_current)

    def add_obj(self, name: str, cons: Type[Geometry]):
        self.scene.add_obj(Model(Material("viewport"), geometry=cons(), name=name))

    def delete_current(self):
        self.scene.delete_obj(self.open_context)

    def show_context(self, x: int, y: int, parent: QtWidgets.QWidget):
        menu = QMenu("Context Menu", parent)
        clicked_object = self.open_context
        if clicked_object == -1:
            # No selected object, show general menu
            menu.addSection("General actions")
            for action in self.general_actions:
                menu.addAction(action)
        else:
            menu.addSection(f'"{self.scene.get_obj_name(clicked_object)}" actions')
            for action in self.obj_selected_actions:
                menu.addAction(action)

        menu.popup(parent.mapToGlobal(QPoint(x, y)))

    def window_resized(self, width: int, height: int):
        self.screen_size.set_dims(width, height)
        self.regen_active_buffer()
        self.camera.window_resized()


class ViewportWidget(QOpenGLWidget):
    def __init__(
        self,
        parent=None,
        on_gl_init: Optional[Callable[[], None]] = None,
        viewport: Type[Viewport] = None,
        scene: Optional[Scene] = None,
    ):
        super().__init__(parent)

        # Set opengl parameters for this Qt widget
        fmt = QtGui.QSurfaceFormat()
        fmt.setVersion(4, 3)
        fmt.setProfile(QtGui.QSurfaceFormat.CoreProfile)
        fmt.setSamples(8)
        self.setFormat(fmt)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.timer = QElapsedTimer()
        self.timer.restart()
        self.timer_update = QTimer()
        self.timer_update.timeout.connect(self.update)
        self.timer_update.start(0)

        self.on_gl_init = on_gl_init

        self.last_mouse = None
        self.shift = False

        self.did_drag = False
        self.open_context = None
        self.last_mouse_button = Qt.NoButton

        try:
            self.ctx = mglw.ctx()
        except ValueError:
            self.ctx = None

        if viewport is None:
            self.manager = Viewport(
                current_project.scene, self.width(), self.height(), self
            )
        else:
            self.manager = viewport(
                scene if scene is not None else current_project.scene,
                self.width(),
                self.height(),
                self,
            )

    def initializeGL(self):
        if self.ctx is None:
            self.ctx = mgl.create_context(require=430)
        mglw.activate_context(ctx=self.ctx)
        self.init()

    def init(self):
        Shaders().load_defaults()
        self.ctx.viewport = (0, 0, self.width(), self.height())
        self.manager.init(self.ctx)

        if self.on_gl_init is not None:
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
        # This is called 60 times per second
        mglw.activate_context(ctx=self.ctx)

        # Get the current framebuffer
        self.screen = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        self.screen.use()
        self.makeCurrent()

        # Render onto the framebuffer
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
