from __future__ import annotations
from typing import Optional
from pyrr import Vector3
import moderngl_window as mglw
import moderngl as mgl
from math import pi, sin, cos
import numpy as np
from moderngl_window.geometry.attributes import AttributeNames
from moderngl_window.opengl.vao import VAO
from pyrr.objects.matrix44 import Matrix44

from nimble.common.models.bounding_box import (
    BoundingBox,
    apply_world_transform,
    vao2bounding_box,
)
from nimble.objects.draw_primitive import sphere


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

    def get_world_bounding_box(self, model: Matrix44) -> BoundingBox:
        return apply_world_transform(
            self.bounding_box,
            model.T,
        )

    def create_collision_shape(self, scale: Vector3, p) -> Optional[int]:
        return None


class Cube(Geometry):
    def __init__(self, **kwargs):
        if "size" not in kwargs:
            kwargs["size"] = (1, 1, 1)

        size = kwargs["size"]
        self.kwargs = kwargs

        super().__init__(
            mglw.geometry.cube(**kwargs),
            bounding_box=(
                Vector3(tuple(-a / 2 for a in size), dtype="f4"),
                Vector3(tuple(a / 2 for a in size), dtype="f4"),
            ),
        )

    def create_collision_shape(self, scale: Vector3, p) -> Optional[int]:
        return p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=tuple(
                s / 2 * scale[i] for i, s in enumerate(self.kwargs["size"])
            ),
        )


class Sphere(Geometry):
    def __init__(self, **kwargs):
        if "radius" not in kwargs:
            kwargs["radius"] = 0.5

        radius = kwargs["radius"]
        self.kwargs = kwargs

        vao, self.verts, self.idx = sphere(**kwargs)
        super().__init__(
            vao,
            bounding_box=(
                Vector3((-radius,) * 3, dtype="f4"),
                Vector3((radius,) * 3, dtype="f4"),
            ),
        )

    def get_world_bounding_box(self, model: Matrix44) -> BoundingBox:
        # Special, just give direct bounding box without rotation
        (s, _, t) = model.decompose()
        new = Matrix44.from_translation(t, dtype="f4") * Matrix44.from_scale(
            s, dtype="f4"
        )
        return apply_world_transform(
            (
                (self.bounding_box[0]),
                (self.bounding_box[1]),
            ),
            new.T,
        )

    def create_collision_shape(self, scale: Vector3, p) -> Optional[int]:
        return p.createCollisionShape(
            p.GEOM_MESH, vertices=self.verts * scale[np.newaxis, :], indices=self.idx
        )


class Ray(Geometry):
    def __init__(self, start: Vector3, ray: Vector3):
        if not isinstance(start, Vector3):
            start = Vector3(start)
        if not isinstance(ray, Vector3):
            ray = Vector3(ray)

        self.ray = ray
        self.kwargs = {"start": start, "ray": ray}
        vao = VAO()
        vao.buffer(
            np.array([start, start + ray]),
            "3f",
            [AttributeNames.POSITION],
        )
        super().__init__(vao)


class Cylinder(Geometry):
    def __init__(
        self,
        radial_segments: int = 32,
        height_segments: int = 1,
        height: float = 1.0,
        radius_top: float = 0.5,
        radius_bottom: float = 0.5,
        theta_start: float = 0.0,
        theta_length: float = 2 * pi,
        height_offset: float = 0.0,
    ):
        self.kwargs = {
            "radial_segments": radial_segments,
            "height_segments": height_segments,
            "height": height,
            "radius_top": radius_top,
            "radius_bottom": radius_bottom,
            "theta_start": theta_start,
            "theta_length": theta_length,
            "height_offset": height_offset,
        }

        half_height = height / 2

        slope = (radius_bottom - radius_top) / height
        verticies = []
        normals = []
        uvs = []

        # Create torso verticies, uvs, and normals
        index_array = []
        index = 0
        for y in range(height_segments + 1):
            index_row = []
            v = y / height_segments
            radius = v * (radius_bottom - radius_top) + radius_top

            for x in range(radial_segments + 1):
                u = x / radial_segments
                theta = u * theta_length + theta_start
                sin_theta = sin(theta)
                cos_theta = cos(theta)
                verticies.append(
                    [
                        radius * sin_theta,
                        -v * height + half_height + height_offset,
                        radius * cos_theta,
                    ]
                )
                normals.append(
                    Vector3((sin_theta, slope, cos_theta), dtype="f4").normalized
                )
                uvs.append([u, 1 - v])
                index_row.append(index)
                index += 1

            index_array.append(index_row)

        indicies = []
        for x in range(radial_segments):
            for y in range(height_segments):
                a = index_array[y][x]
                b = index_array[y + 1][x]
                c = index_array[y + 1][x + 1]
                d = index_array[y][x + 1]

                indicies.extend([a, b, d, b, c, d])

        def generate_cap(index, top, verticies, normals, uvs, indicies) -> int:
            center_index_start = index
            radius = radius_top if top else radius_bottom
            sign = 1 if top else -1
            for x in range(radial_segments + 1):
                verticies.append([0, half_height * sign + height_offset, 0])
                normals.append([0, sign, 0])
                uvs.append([0.5, 0.5])
                index += 1

            center_index_end = index

            for x in range(radial_segments + 1):
                u = x / radial_segments
                theta = u * theta_length + theta_start
                cos_theta = cos(theta)
                sin_theta = sin(theta)
                verticies.append(
                    [
                        radius * sin_theta,
                        sign * half_height + height_offset,
                        radius * cos_theta,
                    ]
                )
                normals.append([0, sign, 0])
                uvs.append([cos_theta * 0.5 + 0.5, sin_theta * 0.5 * sign + 0.5])
                index += 1

            # Gernerate indicies
            for x in range(radial_segments):
                c = center_index_start + x
                i = center_index_end + x
                if top:
                    indicies.extend([i, i + 1, c])
                else:
                    indicies.extend([i + 1, i, c])

            return index

        if radius_top != 0:
            index = generate_cap(index, True, verticies, normals, uvs, indicies)
        if radius_bottom != 0:
            index = generate_cap(index, False, verticies, normals, uvs, indicies)

        np_indicies = np.array(indicies, dtype="i4")
        np_verts = np.array(verticies, dtype="f4")
        normals = np.array(normals, dtype="f4")
        uvs = np.array(uvs, dtype="f4")

        vao = VAO()
        vao.buffer(np_verts, "3f", [AttributeNames.POSITION])
        vao.buffer(normals, "3f", [AttributeNames.NORMAL])
        vao.buffer(uvs, "2f", [AttributeNames.TEXCOORD_0])

        vao.index_buffer(np_indicies)

        max_radius = max(radius_top, radius_bottom)
        self.verts = verticies
        self.idx = indicies

        super().__init__(
            vao,
            (
                Vector3(
                    (-max_radius, -half_height + height_offset, -max_radius), dtype="f4"
                ),
                Vector3(
                    (max_radius, half_height + height_offset, max_radius), dtype="f4"
                ),
            ),
        )

    def create_collision_shape(self, scale: Vector3, p) -> Optional[int]:
        return p.createCollisionShape(
            p.GEOM_MESH, vertices=self.verts * scale[np.newaxis, :], indices=self.idx
        )


class Plane(Geometry):
    def __init__(self):
        self.kwargs = {}

        vao = VAO()
        # fmt: off
        verticies = np.array([
            -0.5, 0, -0.5,
            -0.5, 0, 0.5,
            0.5, 0, 0.5,
            0.5, 0, -0.5,
        ], dtype="f4")
        normals = np.array([0, 1, 0] * 4, dtype="f4")
        uvs = np.array([
            0, 1,
            0, 0,
            1, 0,
            1, 1,
        ], dtype="f4")
        # fmt: on

        vao.buffer(verticies, "3f", [AttributeNames.POSITION])
        vao.buffer(normals, "3f", [AttributeNames.NORMAL])
        vao.buffer(uvs, "2f", [AttributeNames.TEXCOORD_0])

        vao.index_buffer(np.array([0, 1, 2, 0, 2, 3], dtype="i4"))

        super().__init__(
            vao,
            (Vector3((-0.5, 0, -0.5), dtype="f4"), Vector3((0.5, 0, 0.5), dtype="f4")),
        )

    def create_collision_shape(self, scale: Vector3, p) -> Optional[int]:
        return p.createCollisionShape(
            p.GEOM_BOX, halfExtents=[scale[0], 0.01, scale[2]]
        )
