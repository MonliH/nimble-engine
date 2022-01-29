from moderngl_window.resources.programs import Programs
from moderngl_window.meta.program import ProgramDescription
from moderngl_window import opengl
from moderngl_window.opengl import program

from moderngl.program import Program
import moderngl as mgl

from nimble.common.resources import shader
from nimble.common.singleton import Singleton


class Shaders(metaclass=Singleton):
    """A global shader manager to load OpenGL shaders."""

    def __init__(self):
        self.shaders = {}

    def load_defaults(self):
        self.load("viewport", shader("viewport.glsl"))
        self.load("grid", shader("grid.glsl"))
        self.load("constant_color", shader("constant_color.glsl"))
        self.load("bounding_box", shader("bounding_box.glsl"))
        self.load("outline_filter", shader("outline_filter.glsl"))
        self.load("ray", shader("ray.glsl"))
        self.load("texture", shader("texture.glsl"))

    def load(self, name: str, source: str) -> Program:
        if name in self.shaders:
            return self.shaders[name]
        else:
            self.overwrite(name, source)

    def overwrite(self, name: str, source: str) -> Program:
        shader = self.load_source(source)
        self.shaders[name] = shader
        return shader

    def load_source(self, source: str) -> mgl.Program:
        shaders = program.ProgramShaders.from_single(ProgramDescription(), source)
        prog = shaders.create()

        return prog

    def _get(self, name: str) -> Program:
        return self.shaders[name]

    def __getitem__(self, name: str) -> Program:
        return self._get(name)
