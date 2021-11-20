import numpy as np
from model import Model
from shader_manager import global_sm
from pyrr import Matrix44


class Grid(Model):
    def __init__(self, camera, grid_size, ctx):
        super().__init__(camera, global_sm.get("grid"))
        self.grid_size = grid_size

        plane = np.array(
            [
                -1,
                1,
                0,
                -1,
                -1,
                0,
                1,
                1,
                0,
                1,
                -1,
                0,
                1,
                1,
                0,
                -1,
                -1,
                0,
            ]
        )
        vbo = ctx.buffer(plane.astype("f4").tobytes())
        self.vao = ctx.vertex_array(self.prog, [(vbo, "3f", "vert")])

    def render(self):
        self.write_camera_matrix()
        self.vao.render()
