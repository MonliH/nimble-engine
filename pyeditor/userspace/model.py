from __future__ import annotations
from typing import Optional
from pyrr import Matrix44, Vector3
from moderngl.program import Program
import moderngl as mgl

from interface.orbit_camera import OrbitCamera
from userspace.bounding_box import apply_world_transform
from .geometry import Geometry


class Model:
    def __init__(
        self,
        shader: Program,
        geometry: Optional[Geometry] = None,
        rotation: Optional[Vector3] = None,
        position: Optional[Vector3] = None,
        scale: Optional[Vector3] = None,
        draw_bounding_box: bool = False,
    ):
        self.shader = shader

        self.rotation = Vector3((0, 0, 0), dtype="f4")
        self.position = Vector3((0, 0, 0), dtype="f4")
        self.scale = Vector3((1, 1, 1), dtype="f4")

        if rotation is not None:
            self.rotation = rotation
        if position is not None:
            self.position = position
        if scale is not None:
            self.scale = scale

        if geometry is not None:
            self.geometry = geometry

        self.bounding_box_verts = []
        self.bounding_box_indices = []

    def translate(self, translation: Vector3):
        self.position += translation

    def write_matrix(self, camera: OrbitCamera, model: bool = True, mvp: bool = False):
        if mvp:
            self.shader["mvp"].write(camera.proj * camera.view * self.model)
            return

        self.shader["view"].write(camera.view)
        self.shader["proj"].write(camera.proj)

        if model:
            self.shader["model"].write(self.model)

    @property
    def model(self):
        return (
            Matrix44.from_eulers(self.rotation, dtype="f4")
            * Matrix44.from_translation(self.position, dtype="f4")
            * Matrix44.from_scale(self.scale, dtype="f4")
        )

    @property
    def bounding_box_world(self):
        return apply_world_transform(
            (
                (self.geometry.bounding_box[0]),
                (self.geometry.bounding_box[1]),
            ),
            self.model,
        )

    def render(self, camera: OrbitCamera, mvp: bool = False):
        self.write_matrix(camera, mvp=mvp)
        self.geometry.vao.render(self.shader)
