from resources import resource_dir
from moderngl_window.resources.programs import Programs
from moderngl_window.meta.program import ProgramDescription


class ShaderManager:
    def __init__(self):
        self.shaders = {}
        self.programs = Programs()

    def load(self, name: str, path: str):
        self.shaders[name] = self.programs.load(ProgramDescription(path=path))

    def get(self, name: str):
        return self.shaders[name]


global_sm = ShaderManager()
