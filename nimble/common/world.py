from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Type
from nimble.common.ecs import BaseWorld, _C
from nimble.objects.model import Model
from nimble.objects.component import CameraComponent

if TYPE_CHECKING:
    from nimble.interface.orbit_camera import OrbitCamera


class World(BaseWorld):
    def get_obj_component(self, obj: Model, component: Type[_C]) -> _C:
        return self.component_for_entity(obj.entity_id, component)

    def get_camera(self) -> Optional[OrbitCamera]:
        try:
            return self.get_component(CameraComponent)[0][1].camera
        except Exception as e:
            return None
