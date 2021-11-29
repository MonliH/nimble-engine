from __future__ import annotations
from pyrr import Vector3
import moderngl_window as mglw
import moderngl as mgl
from math import pi
import numpy as np
from moderngl_window.geometry.attributes import AttributeNames
from moderngl_window.opengl.vao import VAO

from .bounding_box import BoundingBox, vao2bounding_box


class Geometry:
    def __init__(
        self,
        vao: mgl.VertexArray,
        bounding_box: BoundingBox = None,
    ):
        self.vao = vao

        if bounding_box is None:
            # Create bounding box from vertices
            bounding_box = vao2bounding_box(self.vao)

        self.bounding_box = bounding_box


class Cube(Geometry):
    def __init__(self, **kwargs):
        if "size" not in kwargs:
            kwargs["size"] = (1, 1, 1)

        size = kwargs["size"]

        super().__init__(
            mglw.geometry.cube(**kwargs),
            bounding_box=(
                Vector3(tuple(-a / 2 for a in size), dtype="f4"),
                Vector3(tuple(a / 2 for a in size), dtype="f4"),
            ),
        )


class Sphere(Geometry):
    def __init__(self, **kwargs):
        if "radius" not in kwargs:
            kwargs["radius"] = 0.5

        radius = kwargs["radius"]

        super().__init__(
            mglw.geometry.sphere(**kwargs),
            bounding_box=(
                Vector3((-radius,) * 3, dtype="f4"),
                Vector3((radius,) * 3, dtype="f4"),
            ),
        )


class Cylinder(Geometry):
    def __init__(self, n=32, vertical_segs=1):
        t = 2 * pi * np.arange(0, n) / n
        circle = np.array([np.cos(t), np.sin(t), np.ones_like(t) * -0.5]).transpose()
        vertices = np.vstack(
            (circle, circle, np.array([(-0.5, -0.5, -0.5), (0.5, 0.5, 0.5)]))
        )
        vertices[n:-2, 2] = 0.5

        vao = VAO()
        vao.buffer(vertices, "3f", [AttributeNames.POSITION])

        super().__init__(vao)
