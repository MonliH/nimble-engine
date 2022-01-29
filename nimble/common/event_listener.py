from __future__ import annotations
from PyQt5 import QtGui


class InputObserver:
    """A base class for classes that want to be notified when input is captured."""

    def key_released(self, event: QtGui.QKeyEvent):
        pass

    def key_pressed(self, event: QtGui.QKeyEvent):
        pass

    def mouse_pressed(self, event: QtGui.QMouseEvent):
        pass

    def mouse_released(self, event: QtGui.QMouseEvent):
        pass

    def mouse_moved(self, event: QtGui.QMouseEvent):
        pass

    def scrolled(self, event: QtGui.QWheelEvent):
        pass


class WindowObserver:
    """A base class for classes that want to be notified window events occur."""

    def window_resized(self, width: int, height: int):
        pass
