from __future__ import annotations
import typing
from moderngl_window.opengl.projection import Projection3D
from moderngl_window.scene.camera import Camera
from pyrr import Vector3, Matrix44
from math import atan2, radians, sqrt, cos, sin, tan, pi
import numpy as np
import copy

from nimble.common.event_listener import InputObserver, WindowObserver
from nimble.common.models.size import Size


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


class Spherical:
    """A spherical coordinate helper."""

    def __init__(self, radius=1, phi=0, theta=0) -> None:
        self.radius = radius
        self.phi = phi
        self.theta = theta

    def set_from_vector(self, vec: Vector3) -> Spherical:
        """Set the spherical coordinates from 3D cartesian coordinates."""
        return self.set_from_cartesian(vec.x, vec.y, vec.z)

    def set_from_cartesian(self, x, y, z) -> Spherical:
        self.radius = sqrt(x * x + y * y + z * z)
        if self.radius == 0:
            self.theta = 0
            self.phi = 0
        else:
            self.theta = atan2(sqrt(x * x + y * y), z)
            self.phi = atan2(y, x)

        return self

    def to_cartesian(self) -> Vector3:
        """Convert these spherical coordinates to 3D cartesian coordinates."""
        sin_phi_radius = sin(self.phi) * self.radius
        return Vector3(
            (
                sin_phi_radius * sin(self.theta),
                cos(self.phi) * self.radius,
                sin_phi_radius * cos(self.theta),
            )
        )


class OrbitCamera(Camera, InputObserver, WindowObserver):
    """An camera that orbits around a target point."""

    def __init__(self, size: Size, radius=2, fov=60.0, near=1.0, far=100.0) -> None:
        self.size = size
        self._projection = Projection3D(
            fov=fov, aspect_ratio=self.size.aspect_ratio, near=near, far=far
        )
        self.up = Vector3((0, 1, 0), dtype="f4")
        self.target = Vector3((0, 0, 0), dtype="f4")
        self.spherical = Spherical(radius, radians(65), radians(45))

        self.original_target = copy.deepcopy(self.target)
        self.original_spherical = copy.deepcopy(self.spherical)

    def reset_position(self):
        self.target = copy.deepcopy(self.original_target)
        self.spherical = copy.deepcopy(self.original_spherical)

    def window_resized(self):
        self._projection.update(aspect_ratio=self.size.aspect_ratio)

    @property
    def viewport(self) -> typing.Tuple[float, float]:
        return (self.size.width, self.szie.height)

    @property
    def radius(self):
        return self.spherical.radius

    @property
    def proj(self):
        """The projection matrix of the camera."""
        return self.projection.matrix

    @property
    def position(self):
        return self.target + self.spherical.to_cartesian()

    @property
    def view(self) -> Matrix44:
        """Get the view matrix of the camera."""
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
        self.pan_left(2 * dx * distance / self.size.height)
        self.pan_up(2 * dy * distance / self.size.height)

    def pan_left(self, distance):
        vector = np.array(self.view.c1)[:-1] * (-distance)
        self.target += vector

    def pan_up(self, distance):
        vector = np.array(self.view.c2)[:-1] * distance
        self.target += vector
