import numpy as np
import moderngl as mgl
from pyrr import Matrix44

from nimble.objects import Vector3, Material, Model
from nimble.interface.orbit_camera import OrbitCamera


class Grid(Model):
    def __init__(self, grid_size, ctx):
        super().__init__(Material("grid", pass_model_matrix=False))
        self.grid_size = grid_size
        self.shader = self.material.shader

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
        self.vao = ctx.vertex_array(self.shader, [(vbo, "3f", "in_position")])

        self.base_transform = Matrix44.from_translation(
            (0.0, 0.0, 0.0), dtype="f4"
        ) * Matrix44.from_eulers((np.pi / 2, 0.0, 0.0), dtype="f4")
        self.transform = self.base_transform
        self.ctx = ctx

    def render(self, camera: OrbitCamera):
        self.shader["zoom_level"] = camera.radius

        diff_center = float(
            np.absolute(Vector3((0, 0, 0), dtype="f4") - camera.target).max()
        )
        visible_grid_radius = camera.radius * 5
        grid_size = visible_grid_radius + diff_center
        self.transform = self.base_transform * Matrix44.from_scale(
            (grid_size, grid_size, 1),
            dtype="f4",
        )

        self.shader["model"].write(self.transform)
        self.shader["grid_radius"] = visible_grid_radius
        self.shader["camera_target"].write(camera.target)

        self.ctx.disable(mgl.CULL_FACE)
        self.material.write_matrix(camera)
        self.vao.render()
