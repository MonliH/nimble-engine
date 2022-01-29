from __future__ import annotations
import numpy as np
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union
import moderngl_window as mglw
import moderngl as mgl
from pyrr import Matrix44, Vector3

from nimble.interface.orbit_camera import OrbitCamera
from nimble.common.models.bounding_box import BoundingBox
from nimble.objects.material import Material
from .geometry import Geometry
from nimble.common.shader_manager import Shaders
from nimble.utils import custom_index

if TYPE_CHECKING:
    from .component import Component, ComponentId


LikeVector3 = Union[Vector3, Tuple[int, int, int], List[int]]


class ModelObserver:
    def translation_changed(self, obj: Model) -> None:
        pass

    def scale_changed(self, obj: Model) -> None:
        pass

    def rotation_changed(self, obj: Model) -> None:
        pass

    def component_added(self, obj: Model, component_id: int) -> None:
        pass

    def component_removed(self, obj: Model, component_id: int) -> None:
        pass


def to_vec3(v: LikeVector3) -> Vector3:
    if isinstance(v, Vector3):
        return v
    return Vector3(v, dtype="f4")


class Model:
    """A 3D object in the world, with a material and geometry."""

    def __init__(
        self,
        material: Material,
        geometry: Optional[Geometry] = None,
        name: Optional[str] = None,
        rotation: Optional[Vector3] = None,
        position: Optional[Vector3] = None,
        scale: Optional[Vector3] = None,
        components: Optional[List[Component]] = None,
    ):
        if not isinstance(material, Material):
            raise TypeError("`material` must be of type Material")

        self.material = material
        self.name = name

        self.rotation = Vector3((0, 0, 0), dtype="f4")
        self.position = Vector3((0, 0, 0), dtype="f4")
        self.scale = Vector3((1, 1, 1), dtype="f4")

        if rotation is not None:
            self.rotation = rotation
        if position is not None:
            self.position = position
        if scale is not None:
            self.scale = scale

        self.model_matrix: Optional[Matrix44] = None

        self.bounding_box_world: BoundingBox = None
        self.bounding_box_buffer = None
        self.vbo_vert = None

        self.geometry = geometry

        indicies = np.array(
            [0, 1, 2, 3, 0, 7, 6, 1, 6, 5, 2, 5, 4, 3, 4, 7], dtype="i4"
        )

        ctx: mgl.Context = mglw.ctx()
        self.verts = ctx.buffer(indicies)
        self.transform_changed()

        self.observers: Dict[str, ModelObserver] = {}

        self.components: List[Component] = []
        if components is not None:
            self.components.extend(components)

        self._entity_id = None
        self.active = True

    def set_active(self, value: bool):
        self.active = value

    def add_component(self, component: Component) -> int:
        insert_idx = len(self.components)
        self.components.append(component)
        for observer in self.observers.values():
            observer.component_added(self, insert_idx)
        return insert_idx

    def remove_component(self, component_id: ComponentId):
        idx = custom_index(self.components, lambda c: c.id == component_id)

        del self.components[idx]

        for observer in self.observers.values():
            observer.component_removed(self, idx)

    def set_name(self, new_name: str):
        self.name = new_name

    def register_observer(self, observer: ModelObserver, idx: str):
        self.observers[idx] = observer

    def unregister_observer(self, idx: str):
        del self.observers[idx]

    def set_all_observers(self, observers: Dict[str, ModelObserver]):
        self.observers = observers

    def remove_all_observers(self):
        self.observers = {}

    def update_bounding_render(self):
        i = self.bounding_box_world[0]
        a = self.bounding_box_world[1]

        # fmt: off
        verts = np.array([
            [i[0], a[1], i[2]],
            [a[0], a[1], i[2]],
            [a[0], a[1], a[2]],
            [i[0], a[1], a[2]],
            [i[0], i[1], a[2]],
            [a[0], i[1], a[2]],
            [a[0], i[1], i[2]],
            [i[0], i[1], i[2]],
        ], dtype="f4")
        # fmt: on

        ctx: mgl.Context = mglw.ctx()
        if self.vbo_vert is None:
            self.vbo_vert = ctx.buffer(verts)
        else:
            self.vbo_vert.write(verts)

        if self.bounding_box_buffer is None:
            # Create a new VAO if it doesn't exist
            self.bounding_box_buffer = ctx.vertex_array(
                Shaders()["bounding_box"],
                [(self.vbo_vert, "3f", "model_position")],
                index_buffer=self.verts,
            )

    def position_changed(self):
        for observer in self.observers.values():
            observer.translation_changed(self)
        self.transform_changed()

    def translate(self, translation: LikeVector3):
        translation = to_vec3(translation)
        self.position += translation
        self.position_changed()

    def rotation_changed(self):
        for observer in self.observers.values():
            observer.rotation_changed(self)
        self.transform_changed()

    def rotate(self, rotation: LikeVector3):
        rotation = to_vec3(rotation)
        self.rotation += rotation
        self.rotation_changed()

    def set_rotation(self, rotation: LikeVector3):
        rotation = to_vec3(rotation)
        self.rotation = rotation
        self.rotation_changed()

    def scale_changed(self):
        for observer in self.observers.values():
            observer.scale_changed(self)
        self.transform_changed()

    def set_scale(self, scale: LikeVector3):
        scale = to_vec3(scale)
        self.scale = scale
        self.scale_changed()

    def set_position(self, position: LikeVector3):
        self.position = to_vec3(position)
        self.transform_changed()

    def transform_changed(self):
        # Recalculate model matrix
        self.model_matrix = (
            Matrix44.from_translation(self.position, dtype="f4")
            * Matrix44.from_eulers(self.rotation[[0, 2, 1]], dtype="f4")
            * Matrix44.from_scale(self.scale, dtype="f4")
        )

        if self.geometry is not None:
            # Recalculate bounding box
            self.bounding_box_world = self.geometry.get_world_bounding_box(
                self.model_matrix
            )
            self.update_bounding_render()

    def render(self, camera: OrbitCamera):
        self.material.render(
            camera, self.geometry, self.model_matrix, self.bounding_box_buffer
        )

    @property
    def entity_id(self) -> Optional[int]:
        return self._entity_id

    @entity_id.setter
    def entity_id(self, value: int):
        self._entity_id = value
