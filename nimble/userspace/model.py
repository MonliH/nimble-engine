from __future__ import annotations
import numpy as np
from typing import Optional, Tuple
import moderngl_window as mglw
import moderngl as mgl
from pyrr import Matrix44, Vector3
from moderngl.program import Program

from interface.orbit_camera import OrbitCamera
from common.bounding_box import BoundingBox
from .geometry import Geometry
from common.shader_manager import global_sm


class Model:
    def __init__(
        self,
        shader: Program,
        geometry: Optional[Geometry] = None,
        rotation: Optional[Vector3] = None,
        position: Optional[Vector3] = None,
        scale: Optional[Vector3] = None,
        draw_bounding_box: bool = False,
        model: bool = True,
        lines: bool = False,
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

        self.bounding_box_world: BoundingBox = None
        self.model: Optional[Matrix44] = None
        self.bounding_box_buffer = None
        self.draw_bounding_box = draw_bounding_box

        self.geometry = geometry

        self.transform_changed()
        self.pass_model = model
        self.draw_lines = lines
        self.red = red

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

        indicies = np.array(
            [0, 1, 2, 3, 0, 7, 6, 1, 6, 5, 2, 5, 4, 3, 4, 7], dtype="i4"
        )

        ctx = mglw.ctx()
        vbo_vert = ctx.buffer(verts)
        vbo_ind = ctx.buffer(indicies)

        self.bounding_box_buffer = ctx.vertex_array(
            global_sm["bounding_box"],
            [(vbo_vert, "3f", "model_position")],
            index_buffer=vbo_ind,
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

    def write_matrix(self, camera: OrbitCamera, model: bool = True, mvp: bool = False):
        if mvp:
            self.shader["mvp"].write(camera.proj * camera.view * self.model)
            return

        self.shader["view"].write(camera.view)
        self.shader["proj"].write(camera.proj)

        if model and self.pass_model:
            self.shader["model"].write(self.model)

    def transform_changed(self):
        self.model = (
            Matrix44.from_translation(self.position, dtype="f4")
            * Matrix44.from_eulers(self.rotation, dtype="f4")
            * Matrix44.from_scale(self.scale, dtype="f4")
        )
        if self.geometry is not None:
            self.bounding_box_world = self.geometry.get_world_bounding_box(self.model)
            self.update_bounding_render()

    def render(self, camera: OrbitCamera, mvp: bool = False, bounding: bool = True):
        self.write_matrix(camera, mvp=mvp)
        self.geometry.vao.render(
            self.shader, mode=mgl.TRIANGLES if not self.draw_lines else mgl.LINES
        )
        if self.draw_bounding_box and self.bounding_box_buffer is not None and bounding:
            self.render_bounding_box(camera)

    def render_bounding_box(
        self,
        camera: OrbitCamera,
        color: Tuple[float, float, float] = (1, 1, 1),
    ):
        self.bounding_box_buffer.program["color"] = color
        self.bounding_box_buffer.program["vp"].write(camera.proj * camera.view)
        self.bounding_box_buffer.render(mgl.LINE_LOOP)
