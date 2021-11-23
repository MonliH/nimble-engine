from resources import resource_dir
from moderngl_window.resources.programs import Programs
from moderngl.program import Program
from moderngl_window.meta.program import ProgramDescription


class ShaderManager:
    def __init__(self):
        self.shaders = {}
        self.programs = Programs()

    def load(self, name: str, path: str) -> Program:
        shader = self.programs.load(ProgramDescription(path=str(path)))
        self.shaders[name] = shader
        return shader

    def _get(self, name: str) -> Program:
        return self.shaders[name]

    def __getitem__(self, name: str) -> Program:
        return self._get(name)


global_sm = ShaderManager()
