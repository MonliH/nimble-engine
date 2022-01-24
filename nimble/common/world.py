from typing import Type
from nimble.common.ecs import BaseWorld, _C
from nimble.objects.model import Model


class World(BaseWorld):
    def get_obj_component(self, obj: Model, component: Type[_C]) -> _C:
        return self.component_for_entity(obj.entity_id, component)
