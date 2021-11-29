from __future__ import annotations
from typing import Optional
from pyrr import Matrix44, Vector3
from moderngl_window.scene import Camera
from moderngl.program import Program
from .geometry import Geometry


class Model:
    def __init__(self, shader: Program, geometry: Optional[Geometry] = None):
        self.shader = shader
        self.rotation = Vector3((0, 0, 0), dtype="f4")
        self.translation = Vector3((0, 0, 0), dtype="f4")
        self.scale = Vector3((1, 1, 1), dtype="f4")

        if geometry is not None:
            self.geometry = geometry

    def write_matrix(self, camera: Camera, model: bool = True):
        self.shader["view"].write(camera.view)
        self.shader["proj"].write(camera.proj)

        if model:
            self.shader["model"].write(self.model)

    @property
    def model(self):
        return (
            Matrix44.from_eulers(self.rotation, dtype="f4")
            * Matrix44.from_translation(self.translation, dtype="f4")
            * Matrix44.from_scale(self.scale, dtype="f4")
        )

    @property
    def bounding_box_world(self):
        world_transform = self.model
        return (world_transform * self.geometry.bounding_box[0]), (
            world_transform * self.geometry.bounding_box[1]
        )

    def render(self, camera: Camera):
        self.write_matrix(camera)
        self.geometry.vao.render(self.shader)
