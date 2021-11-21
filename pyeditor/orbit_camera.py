from __future__ import annotations
from moderngl_window.opengl.projection import Projection3D
from moderngl_window.scene.camera import Camera
from pyrr import Vector3, Matrix44
from math import acos, atan2, radians, sqrt, cos, sin, tan, pi
import numpy as np
import copy


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


class Spherical:
    def __init__(self, radius=1, phi=0, theta=0) -> None:
        self.radius = radius
        self.phi = phi
        self.theta = theta

    def set_from_vector(self, vec: Vector3) -> Spherical:
        return self.set_from_cartesian(vec.x, vec.y, vec.z)

    def set_from_cartesian(self, x, y, z) -> Spherical:
        self.radius = sqrt(x * x + y * y + z * z)
        if self.radius == 0:
            self.theta = 0
            self.phi = 0
        else:
            self.theta = acos(z / self.radius)
            self.phi = atan2(y, x)

        return self

    def to_cartesian(self) -> Vector3:
        sin_phi_radius = sin(self.phi) * self.radius
        return Vector3(
            (
                sin_phi_radius * sin(self.theta),
                cos(self.phi) * self.radius,
                sin_phi_radius * cos(self.theta),
            )
        )


class OrbitCamera(Camera):
    def __init__(self, width, height, radius=2, fov=60.0, near=1.0, far=100.0) -> None:
        self.width = width
        self.height = height
        self.aspect_ratio = width / height
        self._projection = Projection3D(
            fov=fov, aspect_ratio=self.aspect_ratio, near=near, far=far
        )
        self.up = Vector3((0, 1, 0), dtype="f4")
        self.target = Vector3((0, 0, 0), dtype="f4")
        self.spherical = Spherical(radius, radians(60), radians(45))

        self.original_target = copy.deepcopy(self.target)
        self.original_spherical = copy.deepcopy(self.spherical)

    def reset_position(self):
        self.target = self.original_target
        self.spherical = self.original_spherical

    def set_window_size(self, width, height):
        self.width = width
        self.height = height
        self.aspect_ratio = width / height
        self._projection.update(aspect_ratio=self.aspect_ratio)

    @property
    def radius(self):
        return self.spherical.radius

    @property
    def proj(self):
        return self.projection.matrix

    @property
    def position(self):
        return self.target + self.spherical.to_cartesian()

    @property
    def view(self) -> Matrix44:
        return Matrix44.look_at(
            self.position,
            self.target,
            self.up,
            dtype="f4",
        )

    def rotate_left(self, angle):
        self.spherical.theta -= angle

    def rotate_up(self, angle):
        self.spherical.phi -= angle
        self.spherical.phi = clamp(self.spherical.phi, 0.000000001, pi)

    def rotate(self, dx, dy):
        self.rotate_left(dx * 0.01)
        self.rotate_up(dy * 0.01)

    def zoom(self, amount):
        self.spherical.radius -= amount

    def pan(self, dx, dy):
        offset = self.position - self.target
        distance = offset.length
        distance *= tan(self._projection.fov / 2 * pi / 180)
        self.pan_left(2 * dx * distance / self.height)
        self.pan_up(2 * dy * distance / self.height)

    def pan_left(self, distance):
        vector = np.array(self.view.c1)[:-1] * (-distance)
        self.target += vector

    def pan_up(self, distance):
        vector = np.array(self.view.c2)[:-1] * distance
        self.target += vector
