import pybullet as p
from abc import ABC
from enum import Enum
import itertools
import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar, cast

import nimble
from nimble.common.ecs import Processor, World
from nimble.interface.gui_logger import (
    with_gui_logging,
    with_gui_logging_default,
)
from nimble.objects.model import Model


ComponentId = str

T = TypeVar("T")


class SlotType(Enum):
    FILE = "file"
    BOOLEAN = "boolean"


class Slot(ABC, Generic[T]):
    def __init__(self, value: Optional[T], label: str, ty: SlotType):
        self.value = value
        self.label = label
        self.ty = ty

    def insert_in_slot(self, value: T):
        self.value = value

    def get_value(self) -> T:
        return self.value

    def get_jsonable(self) -> Any:
        return self.value

    def display(self) -> str:
        return self.label


class Component:
    def __init__(self):
        self.inited = False

    @staticmethod
    @property
    def display_name() -> str:
        raise NotImplementedError("Component.display_name not implemented")

    def slots(self) -> List[Slot]:
        raise NotImplementedError("Component.slots not implemented")

    @property
    def type_alias(self) -> Optional[str]:
        return None


class PhysicsComponent(Component):
    def __init__(
        self,
        model: Model,
        _id: Optional[int] = None,
        slot_params: Optional[List[Any]] = None,
    ):
        super().__init__()
        self._id = _id
        self.model = model
        self.static = Slot(
            False if slot_params is None else slot_params[0],
            "Is static",
            SlotType.BOOLEAN,
        )

    display_name = "Physics Component"

    @property
    def id(self) -> ComponentId:
        return "physics"

    def slots(self) -> List[Slot]:
        return [self.static]


class PhysicsProcessor(Processor):
    def __init__(self):
        super().__init__()
        self.client = p.connect(p.DIRECT)
        p.resetSimulation()
        p.setGravity(0, -9.81, 0)

    def init(self):
        self.added_entities: Dict[str, int] = {}
        for (_, component) in cast(World, self.world).get_component(PhysicsComponent):
            model_name = component.model.name
            if model_name not in self.added_entities:
                collider = component.model.geometry.create_collision_shape(
                    component.model.scale, p
                )
                self.added_entities[model_name] = (
                    p.createMultiBody(
                        0 if component.static.get_value() else 1,
                        collider,
                        basePosition=tuple(component.model.position.tolist()),
                        baseOrientation=p.getQuaternionFromEuler(
                            tuple(component.model.rotation.tolist())
                        ),
                    ),
                    component.model,
                )

    def process(self):
        for _ in range(4):
            p.stepSimulation()

        for (body, model) in self.added_entities.values():
            pos, rot = p.getBasePositionAndOrientation(body)
            model.set_position(pos)
            x, y, z = p.getEulerFromQuaternion(rot)
            model.set_rotation((-x, -y, -z))


def CustomComponentQuery(id) -> str:
    return f"custom_{id}.py"


class CustomComponent(Component):
    _unique_id = itertools.count()

    def __init__(
        self,
        model: Model,
        _id: Optional[int] = None,
        slot_params: Optional[List[Any]] = None,
    ):
        super().__init__()
        self.model = model
        self._id = next(self._unique_id) if _id is None else _id

        self.script_slot = Slot(
            None if slot_params is None else slot_params[0], "Script", SlotType.FILE
        )
        self.file = None
        self.inited = False

    display_name = "Custom Script"

    @property
    def id(self) -> ComponentId:
        return f"custom_{self._id}"

    def slots(self) -> List[Slot]:
        return [self.script_slot]

    @property
    def type_alias(self) -> Optional[str]:
        return f"custom_{self.script_slot.get_value()}"


class ScriptProcessor(Processor):
    def __init__(self, components: List[CustomComponent]):
        is_inited = set()
        self.processors = {}

        for component in components:
            if component.type_alias in is_inited:
                continue

            self.processors[component.type_alias] = self.get_processor_from_script(
                component.script_slot.get_value()
            )
            is_inited.add(component.type_alias)

    @staticmethod
    def get_processor_from_script(path: Optional[str]) -> Processor:
        from nimble.common import current_project

        if path is None:
            return BaseComponent()

        with open(current_project.folder / path, "r") as f:
            script_file_contents = f.read()

        @with_gui_logging_default({})
        def run():
            module = {"nimble": nimble}
            exec(script_file_contents, module)
            return module

        module = run()

        if "Component" in module:
            CustomProcessor = module["Component"]
            CustomProcessor.__init__ = lambda _: None
            processor_instance = CustomProcessor()
        else:
            processor_instance = NoProcessor()

        return processor_instance

    @with_gui_logging
    def init(self):
        for processor in self.processors.values():
            processor.world = self.world

            if hasattr(processor, "init"):
                processor.init()

    @with_gui_logging
    def process(self):
        for pid, processor in self.processors.items():
            for (_, component) in self.world.get_component(pid):
                processor.process(component.model)


class BaseComponent(Processor):
    def init(self):
        pass

    def process(self, model: Model):
        pass


class NoProcessor(BaseComponent):
    def init(self):
        logging.getLogger("nimble").error(
            "No component found. There is likely some error above, which prevented a component from being loaded."
        )

    def process(self, model: Model):
        pass
