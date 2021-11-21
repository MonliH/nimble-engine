import numpy as np
from model import Model
import moderngl as mgl
from shader_manager import global_sm
from pyrr import Matrix44


class Grid(Model):
    def __init__(self, camera, grid_size, ctx):
        super().__init__(camera, global_sm.get("grid"))
        self.grid_size = grid_size

        # fmt: off
        plane = np.array(
            [
                1, 1, 0,
                -1, -1, 0,
                -1, 1, 0,

                -1, -1, 0,
                1, 1, 0,
                1, -1, 0,
            ]
        )

        # fmt: on
        vbo = ctx.buffer(plane.astype("f4").tobytes())
        self.vao = ctx.vertex_array(self.prog, [(vbo, "3f", "vert")])
        self.transform = (
            Matrix44.from_translation((0.0, 0.0, 0.0), dtype="f4")
            * Matrix44.from_eulers((np.pi / 2, 0.0, 0.0), dtype="f4")
            * Matrix44.from_scale((1000, 1000, 1), dtype="f4")
        )
        self.prog["model"].write(self.transform)
        self.prog["zoom_level"] = self.camera.radius
        self.ctx = ctx

    def render(self):
        self.prog["zoom_level"] = self.camera.radius
        self.prog["camera_target"] = self.camera.target
        self.ctx.disable(mgl.CULL_FACE)
        self.write_camera_matrix()
        self.vao.render()
