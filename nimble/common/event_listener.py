from __future__ import annotations
from PyQt5 import QtGui


class InputObserver:
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
    def window_resized(self, width: int, height: int):
        pass
