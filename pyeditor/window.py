import math
import moderngl_window
import random


class WindowEvents(moderngl_window.WindowConfig):
    """
    Demonstrates handling mouse, keyboard, render and resize events
    """

    gl_version = (3, 3)
    title = "Py3ditor"
    cursor = True
    vsync = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.wnd.exit_key = None

    def render(self, time: float, frametime: float):
        # self.ctx.clear(0.25, 0.25, 0.25)
        pass

    def close(self):
        print("Window is closing")

    def resize(self, width: int, height: int):
        self.size = (width, height)
