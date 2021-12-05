from math import pi
from pyrr import Vector3

from userspace.model import Model
from userspace.geometry import Cylinder
import common.bounding_box as bounding_box

from common.shader_manager import global_sm
from .orbit_camera import OrbitCamera


class Arrow:
    def __init__(self, color: Vector3, offset: float, rotation: Vector3, scale: float):
        self.color = color.astype("f4")

        self.axis_shader = global_sm["constant_color"]

        line_height = 1
        height = 0.25

        self.line = Model(
            self.axis_shader,
            Cylinder(radius_top=0.03, radius_bottom=0.03),
            position=Vector3((0, 0, -(line_height * scale / 2 + offset)), dtype="f4"),
            rotation=rotation,
            scale=Vector3((scale,) * 3, dtype="f4"),
            draw_bounding_box=True,
        )
        self.point = Model(
            self.axis_shader,
            Cylinder(height=height, radius_top=0, radius_bottom=0.1),
            position=Vector3((0, 0, -(line_height * scale + offset)), dtype="f4"),
            rotation=rotation,
            scale=Vector3((scale,) * 3, dtype="f4"),
            draw_bounding_box=True,
        )

        self.bounding_box = bounding_box.join(
            self.line.bounding_box_world, self.point.bounding_box_world
        )

    def render(self, camera: OrbitCamera):
        self.axis_shader["color"].write(self.color)
        self.line.render(camera, mvp=True)
        self.point.render(camera, mvp=True)


class AxisArrows:
    def __init__(self, scale):
        # self.x = Arrow(
        #     Vector3((1, 0, 0)), 0, Vector3((0, pi / 2, 0), dtype="f4"), scale
        # )
        # self.y = Arrow(Vector3((0, 1, 0)), 0, Vector3((0, 0, 0), dtype="f4"), scale)
        self.z = Arrow(
            Vector3((0, 0, 1)), 0, Vector3((pi / 2, 0, 0), dtype="f4"), scale
        )

    def render(self, camera: OrbitCamera):
        # self.x.render(camera)
        # self.y.render(camera)
        self.z.render(camera)
