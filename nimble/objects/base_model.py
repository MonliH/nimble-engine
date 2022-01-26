from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional

from nimble.utils import custom_index

if TYPE_CHECKING:
    from nimble.objects import Model3D, Component, ComponentId


class ModelObserver:
    def translation_changed(self, obj: Model3D) -> None:
        pass

    def scale_changed(self, obj: Model3D) -> None:
        pass

    def rotation_changed(self, obj: Model3D) -> None:
        pass

    def component_added(self, obj: BaseModel, component_id: int) -> None:
        pass

    def component_removed(self, obj: BaseModel, component_id: int) -> None:
        pass


class BaseModel:
    def __init__(
        self,
        name: Optional[str] = None,
        components: Optional[List[Component]] = None,
    ):
        self.name = name
        self.components: List[Component] = []
        if components is not None:
            self.components.extend(components)
        self._entity_id = None
        self.active = True
        self.observers: Dict[str, ModelObserver] = {}

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

    @property
    def entity_id(self) -> Optional[int]:
        return self._entity_id

    @entity_id.setter
    def entity_id(self, value: int):
        self._entity_id = value
