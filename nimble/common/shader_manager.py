import moderngl as mgl
from moderngl_window.resources.programs import Programs
from moderngl.program import Program
from moderngl_window.meta.program import ProgramDescription

from nimble.common.resources import shader
from nimble.common.singleton import Singleton


class Shaders(metaclass=Singleton):
    def __init__(self):
        self.shaders = {}
        self.programs = Programs()

    def load_defaults(self):
        self.load("viewport", shader("viewport.glsl"))
        self.load("grid", shader("grid.glsl"))
        self.load("constant_color", shader("constant_color.glsl"))
        self.load("bounding_box", shader("bounding_box.glsl"))
        self.load("outline_filter", shader("outline_filter.glsl"))
        self.load("ray", shader("ray.glsl"))
        self.load("texture", shader("texture.glsl"))

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
