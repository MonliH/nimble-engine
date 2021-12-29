import math
from typing import Callable, Optional
from PySide2.QtCore import SIGNAL, QObject, QPoint, Qt
from PySide2.QtGui import QSurfaceFormat
import moderngl_window as mglw
import moderngl as mgl
from moderngl_window.geometry import quad_fs
from PySide2.QtCore import QElapsedTimer, QTimer, Qt
from PySide2.QtWidgets import QAction, QDockWidget, QMainWindow, QMenu, QOpenGLWidget
from PySide2 import QtGui

from nimble.common.shader_manager import Shaders
import nimble.common.models.ray_cast as ray_cast

from nimble.interface.overlays.object_controls import Axis
from nimble.interface.viewport_manager import Viewport

from nimble.objects.object_manager import active_scene
from nimble.objects.model import Model
from nimble.objects.geometry import Cube


class QModernGLWidget(QOpenGLWidget):
    def __init__(self, parent=None, on_gl_init: Optional[Callable[[], None]] = None):
        super().__init__(parent)  # fmt, None)
        fmt = QSurfaceFormat()
        fmt.setVersion(4, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
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


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(100, 100, 1080, 720)
        self.show()
        self.setWindowTitle("Nimble Engine")

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
        active_scene.add_obj("Cube", Model(Shaders()["viewport"], Cube()))

    def closeEvent(self, event):
        event.accept()
