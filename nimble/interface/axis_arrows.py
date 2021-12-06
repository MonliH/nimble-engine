from math import pi
from pyrr import Vector3

from userspace.model import Model
from userspace.geometry import Cylinder
import common.bounding_box as bounding_box

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


class AxisArrows:
    def __init__(self, scale):
        self.x = Arrow(Vector3((1, 0, 0)), Vector3((0, pi / 2, 0), dtype="f4"), scale)
        self.y = Arrow(Vector3((0, 1, 0)), Vector3((0, 0, 0), dtype="f4"), scale)
        self.z = Arrow(Vector3((0, 0, 1)), Vector3((pi / 2, 0, 0), dtype="f4"), scale)

    def render(self, camera: OrbitCamera):
        self.x.render(camera)
        self.y.render(camera)
        self.z.render(camera)

    def set_scale(self, scale: float):
        scale = Vector3((scale,) * 3, dtype="f4")
        self.x.set_scale(scale)
        self.y.set_scale(scale)
        self.z.set_scale(scale)
