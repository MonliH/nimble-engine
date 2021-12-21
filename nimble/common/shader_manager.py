import moderngl as mgl
from moderngl_window.resources.programs import Programs
from moderngl.program import Program
from moderngl_window.meta.program import ProgramDescription

from common.resources import shader


class ShaderManager:
    def __init__(self):
        self.shaders = {}
        self.programs = Programs()

    def load(self, name: str, path: str) -> Program:
        if name in self.shaders:
            return self.shaders[name]
        else:
            self.overwrite(name, path)

    def overwrite(self, name: str, path: str) -> Program:
        shader = self.programs.load(ProgramDescription(path=str(path)))
        self.shaders[name] = shader
        return shader

    def _get(self, name: str) -> Program:
        return self.shaders[name]

    def __getitem__(self, name: str) -> Program:
        return self._get(name)


global_sm = ShaderManager()


def init_shaders():
    global_sm.load("viewport", shader("viewport.glsl"))
    global_sm.load("grid", shader("grid.glsl"))
    global_sm.load("constant_color", shader("constant_color.glsl"))
    global_sm.load("bounding_box", shader("bounding_box.glsl"))
    global_sm.load("outline_filter", shader("outline_filter.glsl"))
    global_sm.load("ray", shader("ray.glsl"))
