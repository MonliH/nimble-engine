from math import pi
from typing import Optional
from pyrr import Vector3

from userspace.model import Model
from userspace.geometry import Cylinder
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

    def render(self, camera: OrbitCamera):
        self.x.render(camera)
        self.y.render(camera)
        self.z.render(camera)

    def set_scale(self, scale: float):
        scale = Vector3((scale,) * 3, dtype="f4")
        self.x.set_scale(scale)
        self.y.set_scale(scale)
        self.z.set_scale(scale)

    def start_drag(self, axis: Axis):
        self.dragged = axis

    def stop_drag(self):
        self.dragged = None

    def set_active(self, active: Optional[Model]):
        if active is not None:
            self.active = active
            self.x.set_position(active.position)
            self.y.set_position(active.position)
            self.z.set_position(active.position)

    def did_drag(self, camera: OrbitCamera, x: int, y: int, dx: int, dy: int):
        if self.dragged is not None:
            length = ray_cast.get_ray_between(camera, self.active)[1]

            model = ray_cast.get_ray(x, y, camera)[1].normalised
            model_delta = ray_cast.get_ray(x + dx, y + dy, camera)[1].normalised
            model *= length.length
            model_delta *= length.length

            diff = model_delta - model
            diff *= 0.2

            translation = (
                (diff.x, 0, 0)
                if self.dragged == Axis.X
                else (0, diff.y, 0)
                if self.dragged == Axis.Y
                else (0, 0, diff.z)
            )
            translate_vec = Vector3(translation, dtype="f4")

            self.x.translate(translate_vec)
            self.y.translate(translate_vec)
            self.z.translate(translate_vec)
            self.active.translate(translate_vec)
