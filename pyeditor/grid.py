import numpy as np
from pyrr.objects.vector4 import Vector3
from model import Model
import moderngl as mgl
from orbit_camera import OrbitCamera
from resources import shader
from shader_manager import global_sm
from pyrr import Matrix44
import transform_matrix


class Grid(Model):
    def __init__(self, camera: OrbitCamera, grid_size, ctx):
        super().__init__(camera, global_sm["grid"])
        self.grid_size = grid_size
        self.axis_prog = global_sm["line"]

        # fmt: off
        plane = np.array(
            [
                1, 1, 0,
                -1, -1, 0,
                -1, 1, 0,

                -1, -1, 0,
                1, 1, 0,
                1, -1, 0,
            ],
            dtype="f4"
        )

        # fmt: on
        vbo = ctx.buffer(plane.tobytes())
        self.vao = ctx.vertex_array(self.prog, [(vbo, "3f", "vert")])

        self.base_transform = Matrix44.from_translation(
            (0.0, 0.0, 0.0), dtype="f4"
        ) * Matrix44.from_eulers((np.pi / 2, 0.0, 0.0), dtype="f4")
        self.transform = self.base_transform
        self.ctx = ctx

    def render(self):
        self.prog["zoom_level"] = self.camera.radius

        diff_center = float(
            np.absolute(Vector3((0, 0, 0), dtype="f4") - self.camera.target).max()
        )
        visible_grid_radius = self.camera.radius * 5
        grid_size = visible_grid_radius + diff_center
        self.transform = self.base_transform * Matrix44.from_scale(
            (grid_size, grid_size, 1),
            dtype="f4",
        )
        self.prog["model"].write(self.transform)
        self.prog["grid_radius"] = visible_grid_radius
        self.prog["camera_target"].write(self.camera.target)

        self.ctx.disable(mgl.CULL_FACE)
        self.write_camera_matrix()
        self.vao.render()
