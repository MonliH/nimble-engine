from math import dist, pi
from typing import Optional, Set, Tuple, Union
from numpy.lib.type_check import real
from pyrr import Vector3

from userspace.model import Model
from userspace.geometry import Cylinder, Ray
from userspace.object_manager import ObjectManager
import common.bounding_box as bounding_box
import common.ray_cast as ray_cast

from common.shader_manager import global_sm
from .orbit_camera import OrbitCamera


class Arrow:
    def __init__(self, color: Vector3, rotation: Vector3, scale: float):
        self.color = color.astype("f4")

        self.axis_shader = global_sm["constant_color"]

        line_height = 0.5
        height = line_height * 0.35
        line_radius = 0.015

        self.line = Model(
            self.axis_shader,
            Cylinder(
                height=line_height,
                radius_top=line_radius,
                radius_bottom=line_radius,
                height_offset=line_height / 2,
            ),
            rotation=rotation,
            scale=Vector3((scale,) * 3, dtype="f4"),
        )
        self.point = Model(
            self.axis_shader,
            Cylinder(
                height=height,
                radius_top=0,
                radius_bottom=0.04,
                height_offset=line_height + height / 2,
            ),
            rotation=rotation,
            scale=Vector3((scale,) * 3, dtype="f4"),
        )

        self.update_bounding_box()

    def update_bounding_box(self):
        self.bounding_box = bounding_box.join(
            self.line.bounding_box_world, self.point.bounding_box_world
        )

    def render(self, camera: OrbitCamera):
        self.axis_shader["color"].write(self.color)
        self.line.render(camera, mvp=True)
        self.point.render(camera, mvp=True)

    def set_scale(self, scale: Vector3):
        self.line.set_scale(scale)
        self.point.set_scale(scale)
        self.update_bounding_box()

    def set_position(self, scale: Vector3):
        self.line.set_position(scale)
        self.point.set_position(scale)
        self.update_bounding_box()

    def translate(self, translation: Vector3):
        self.line.translate(translation)
        self.point.translate(translation)
        self.update_bounding_box()


class Axis:
    X = 0
    Y = 1
    Z = 2


class AxisArrows:
    def __init__(self, scale):
        self.x = Arrow(Vector3((1, 0, 0)), Vector3((0, pi / 2, 0), dtype="f4"), scale)
        self.y = Arrow(Vector3((0, 1, 0)), Vector3((0, 0, 0), dtype="f4"), scale)
        self.z = Arrow(Vector3((0, 0, 1)), Vector3((-pi / 2, 0, 0), dtype="f4"), scale)

        self.dragged = None
        self.active: Optional[Model] = None
        self.translating = False
        self.plane = None

    def render(self, camera: OrbitCamera):
        self.x.render(camera)
        self.y.render(camera)
        self.z.render(camera)

    def set_scale(self, scale: float):
        scale = Vector3((scale,) * 3, dtype="f4")
        self.x.set_scale(scale)
        self.y.set_scale(scale)
        self.z.set_scale(scale)

    def start_translate(self, axis: Union[Axis, Set[Axis]]):
        self.start_drag(axis)
        self.translating = True

    def start_drag(self, axis: Union[Axis, Set[Axis]]):
        self.dragged = set(axis) if isinstance(axis, set) else {axis}

    def stop_drag(self):
        self.dragged = None
        self.translating = False
        self.length = None

    def set_active(self, active: Optional[Model], camera):
        if active is not None:
            self.active = active
            self.x.set_position(active.position)
            self.y.set_position(active.position)
            self.z.set_position(active.position)

            normal = camera.position - self.active.position
            self.plane = (normal, self.active.position)

    @staticmethod
    def project_point_on_plane(
        ray: Vector3, plane: Tuple[Vector3, Vector3], camera: OrbitCamera
    ) -> Vector3:
        normal, p0 = plane
        l = ray.normalised

        l0 = camera.position
        d = (p0 - l0).dot(normal) / l.dot(normal)
        intersection = l0 + l * d

        real_diff = intersection - camera.position
        return real_diff

    def did_drag(
        self,
        camera: OrbitCamera,
        x: int,
        y: int,
        dx: int,
        dy: int,
    ):
        if self.active is None:
            return

        if self.dragged is not None:
            normal, _ = self.plane
            real_model = ray_cast.get_pos(x, y, camera)
            model = real_model.normalised * normal.length

            real_diff = self.project_point_on_plane(
                ray_cast.get_pos(x + dx, y + dy, camera), self.plane, camera
            )
            new_vector = real_diff.normalised * normal.length
            diff = new_vector - model
            diff *= camera.radius / 3

            translation = (
                diff.x if Axis.X in self.dragged else 0,
                diff.y if Axis.Y in self.dragged else 0,
                diff.z if Axis.Z in self.dragged else 0,
            )
            translate_vec = Vector3(translation, dtype="f4")

            self.x.translate(translate_vec)
            self.y.translate(translate_vec)
            self.z.translate(translate_vec)
            self.active.translate(translate_vec)
