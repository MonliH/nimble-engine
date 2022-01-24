from math import pi
from typing import Optional, Set, Tuple, Union
from pyrr import Vector3

from nimble.objects import (
    Material,
    Model,
    ModelObserver,
    Cylinder,
    SceneObserver,
)
import nimble.common.models.bounding_box as bounding_box
import nimble.common.models.ray_cast as ray_cast

from ..orbit_camera import OrbitCamera


class Arrow:
    def __init__(self, color: Vector3, rotation: Vector3, scale: float):
        self.color = color.astype("f4")

        material = Material("constant_color", pass_mvp=True)
        self.axis_shader = material.shader

        line_height = 0.5
        height = line_height * 0.35
        line_radius = 0.015

        self.line = Model(
            material,
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
            material,
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
        self.line.render(camera)
        self.point.render(camera)

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


class TransformTools(SceneObserver, ModelObserver):
    def __init__(self, scale, camera: OrbitCamera):
        self.x = Arrow(Vector3((1, 0, 0)), Vector3((0, 0, pi / 2), dtype="f4"), scale)
        self.y = Arrow(Vector3((0, 1, 0)), Vector3((0, 0, 0), dtype="f4"), scale)
        self.z = Arrow(Vector3((0, 0, 1)), Vector3((-pi / 2, 0, 0), dtype="f4"), scale)

        self.dragged = None
        self.active: Optional[Model] = None
        self.translating = False
        self.plane = None
        self.camera = camera

    def select_changed(self, idx: int, obj: Model) -> None:
        self.set_active(obj)
        if obj is not None:
            self.translation_changed(obj)

    def render(self):
        self.x.render(self.camera)
        self.y.render(self.camera)
        self.z.render(self.camera)

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

    def set_active(self, active: Optional[Model]):
        if active is not None:
            self.active = active
            normal = self.camera.position - self.active.position
            self.plane = (normal, self.active.position)

    def update_position(self, position: Vector3):
        self.x.set_position(position)
        self.y.set_position(position)
        self.z.set_position(position)

    def translation_changed(self, obj: Model) -> None:
        self.update_position(obj.position)

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
        x: int,
        y: int,
        dx: int,
        dy: int,
    ):
        if self.active is None:
            return

        if self.dragged is not None:
            normal, _ = self.plane
            real_model = ray_cast.get_pos(x, y, self.camera)
            model = real_model.normalised * normal.length

            real_diff = self.project_point_on_plane(
                ray_cast.get_pos(x + dx, y + dy, self.camera), self.plane, self.camera
            )
            new_vector = real_diff.normalised * normal.length
            diff = new_vector - model
            diff *= self.camera.radius / 3

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
