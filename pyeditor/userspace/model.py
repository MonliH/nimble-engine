from __future__ import annotations
from typing import Tuple
from pyrr import Matrix44, Vector3
import moderngl_window as mglw
from moderngl_window.scene import Camera
from moderngl.program import Program
import moderngl as mgl
from math import pi
import numpy as np


BoundingBox = Tuple[Vector3, Vector3]


def render_model(
    model: Model,
    view: Matrix44,
    proj: Matrix44,
    shader: Program,
    model_matrix: Matrix44,
):
    pass


class Model:
    def __init__(self, shader: Program, bounding_box: BoundingBox = None):
        self.shader = shader
        self.rotation = Vector3((0, 0, 0), dtype="f4")
        self.translation = Vector3((0, 0, 0), dtype="f4")
        self.scale = Vector3((1, 1, 1), dtype="f4")

        if bounding_box is None:
            self.bounding_box = (
                Vector3((0, 0, 0), dtype="f4"),
                Vector3((0, 0, 0), dtype="f4"),
            )
        else:
            self.bounding_box = bounding_box

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
        return (world_transform * self.bounding_box[0]), (
            world_transform * self.bounding_box[1]
        )

    def render(self, camera: Camera):
        self.write_matrix(camera)


class Cube(Model):
    def __init__(self, prog):
        super().__init__(
            prog,
            bounding_box=(Vector3((-0.5, -0.5, -0.5)), Vector3((0.5, 0.5, 0.5))),
        )
        self.cube = mglw.geometry.cube(size=(1, 1, 1))

    def render(self, camera: Camera):
        super().render(camera)
        self.shader["color"].value = (
            0.1,
            0.1,
            0.1,
        )
        self.cube.render(self.shader)


class Sphere(Model):
    def __init__(self, prog):
        super().__init__(prog)
        self.sphere = mglw.geometry.sphere()

    def render(self, camera: Camera):
        super().render(camera)
        self.shader["color"].value = (
            0.1,
            0.1,
            0.1,
        )
        self.sphere.render(self.shader)


class Cylinder(Model):
    def __init__(self, camera, prog, ctx: mgl.Context):
        super().__init__(camera, prog)
        n = 32
        t = 2 * pi * np.arange(0, n) / n
        circle = np.array([np.cos(t), np.sin(t), np.ones_like(t) * -0.5]).transpose()
        vertices = np.vstack(
            (circle, circle, np.array([(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)]))
        )
        vertices[n:-2, 2] = 0.5

        # create segments
        s = [(i, (i + 1) % n) for i in range(n)]
        s.extend([(i + n, (i + 1) % n + n) for i in range(n)])
        if vertical_segs:
            s.extend([(i, i + n) for i in range(n)])
        segments = np.array(s)

        # create faces
        f = []
        for i in range(n):
            f.append([i, (i + 1) % n, i + n])  # vertical face 1
            f.append([i + n, (i + 1) % n + n, (i + 1) % n])  # vertical face 2
            f.append([i, (i + 1) % n, 2 * n])  # bottom plate
            f.append([i + n, (i + 1) % n + n, 2 * n + 1])  # top plate
        faces = np.array(f)

        vbo = ctx.buffer(faces)
        self.cylinder = ctx.vertex_array()
