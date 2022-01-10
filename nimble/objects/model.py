from __future__ import annotations
import numpy as np
from typing import Optional, Tuple
import moderngl_window as mglw
import moderngl as mgl
from pyrr import Matrix44, Vector3
from moderngl.program import Program

from nimble.interface.orbit_camera import OrbitCamera
from nimble.common.models.bounding_box import BoundingBox
from nimble.objects.material import Material
from .geometry import Geometry
from nimble.common.shader_manager import Shaders


class Model:
    def __init__(
        self,
        material: Material,
        geometry: Optional[Geometry] = None,
        rotation: Optional[Vector3] = None,
        position: Optional[Vector3] = None,
        scale: Optional[Vector3] = None,
    ):
        if not isinstance(material, Material):
            raise TypeError("`material` must be of type Material")

        self.material = material

        self.rotation = Vector3((0, 0, 0), dtype="f4")
        self.position = Vector3((0, 0, 0), dtype="f4")
        self.scale = Vector3((1, 1, 1), dtype="f4")

        if rotation is not None:
            self.rotation = rotation
        if position is not None:
            self.position = position
        if scale is not None:
            self.scale = scale

        self.model_matrix: Optional[Matrix44] = None

        self.bounding_box_world: BoundingBox = None
        self.bounding_box_buffer = None
        self.vbo_vert = None

        self.geometry = geometry

        indicies = np.array(
            [0, 1, 2, 3, 0, 7, 6, 1, 6, 5, 2, 5, 4, 3, 4, 7], dtype="i4"
        )

        ctx: mgl.Context = mglw.ctx()
        self.verts = ctx.buffer(indicies)
        self.transform_changed()

    def update_bounding_render(self):
        i = self.bounding_box_world[0]
        a = self.bounding_box_world[1]

        # fmt: off
        verts = np.array([
            [i[0], a[1], i[2]],
            [a[0], a[1], i[2]],
            [a[0], a[1], a[2]],
            [i[0], a[1], a[2]],
            [i[0], i[1], a[2]],
            [a[0], i[1], a[2]],
            [a[0], i[1], i[2]],
            [i[0], i[1], i[2]],
        ], dtype="f4")
        # fmt: on

        ctx: mgl.Context = mglw.ctx()
        if self.vbo_vert is None:
            self.vbo_vert = ctx.buffer(verts)
        else:
            self.vbo_vert.write(verts)

        if self.bounding_box_buffer is None:
            self.bounding_box_buffer = ctx.vertex_array(
                Shaders()["bounding_box"],
                [(self.vbo_vert, "3f", "model_position")],
                index_buffer=self.verts,
            )

    def translate(self, translation: Vector3):
        self.position += translation
        self.transform_changed()

    def rotate(self, rotation: Vector3):
        self.rotation += rotation
        self.transform_changed()

    def set_scale(self, scale: Vector3):
        self.scale = scale
        self.transform_changed()

    def set_position(self, position: Vector3):
        self.position = position
        self.transform_changed()

    def transform_changed(self):
        self.model_matrix = (
            Matrix44.from_translation(self.position, dtype="f4")
            * Matrix44.from_eulers(self.rotation, dtype="f4")
            * Matrix44.from_scale(self.scale, dtype="f4")
        )
        if self.geometry is not None:
            self.bounding_box_world = self.geometry.get_world_bounding_box(
                self.model_matrix
            )
            self.update_bounding_render()

    def render(self, camera: OrbitCamera):
        self.material.render(
            camera, self.geometry, self.model_matrix, self.bounding_box_buffer
        )
