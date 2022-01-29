from __future__ import annotations
import pybullet as p
from abc import ABC
from enum import Enum
import itertools
import logging
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional, TypeVar, cast

import nimble
from nimble.common.ecs import Processor
from nimble.common.keys import PressedKeys
from nimble.interface.gui_logger import (
    with_gui_logging,
    with_gui_logging_default,
)
from nimble.objects.model import LikeVector3, Model

if TYPE_CHECKING:
    from nimble.interface.orbit_camera import OrbitCamera
    from nimble.common.world import World


ComponentId = str

T = TypeVar("T")


class SlotType(Enum):
    FILE = "file"
    BOOLEAN = "boolean"
    FLOAT = "float"


class Slot(ABC, Generic[T]):
    """A value in a component that can be set by the user."""

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
    """A component which can modify an entity."""

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
    """A rigid-body physics component"""

    def __init__(
        self,
        model: Model,
        _id: Optional[int] = None,
        slot_params: Optional[List[Any]] = None,
    ):
        super().__init__()
        self._id = _id
        self.model = model
        self.mass = Slot(
            1 if slot_params is None else slot_params[0], "Mass", SlotType.FLOAT
        )
        self.friction = Slot(
            0.5 if slot_params is None else slot_params[1], "Friction", SlotType.FLOAT
        )
        self.static = Slot(
            False if slot_params is None else slot_params[2],
            "Is static",
            SlotType.BOOLEAN,
        )

    display_name = "Physics Component"

    @property
    def id(self) -> ComponentId:
        return "physics"

    def slots(self) -> List[Slot]:
        return [self.mass, self.friction, self.static]

    def apply_force(self, force: LikeVector3):
        """Apply an external force to this physics body."""
        p.applyExternalForce(
            self._id,
            -1,
            list(force),
            p.getBasePositionAndOrientation(self._id)[0],
            p.WORLD_FRAME,
        )

    def collides_with(self, other: PhysicsComponent) -> bool:
        """Check if this physics body collides with `other`."""
        return len(p.getContactPoints(self._id, other._id)) > 0

    @property
    def body_id(self) -> Optional[int]:
        return self._id

    @body_id.setter
    def body_id(self, value: Optional[int]):
        self._id = value


class PhysicsProcessor(Processor):
    """The processor for physics."""

    def __init__(self):
        super().__init__()

        self.client = p.connect(p.DIRECT)

        # Reset the simulation
        p.resetSimulation()
        # Set physics parameters
        p.setPhysicsEngineParameter(
            fixedTimeStep=1.0 / 120.0,
            numSolverIterations=100,
        )
        p.setGravity(0, -9.81, 0)

    def add_rigid_body(self, component: PhysicsComponent, eid: int):
        """Add a rigid body to the physics simulation."""
        collider = component.model.geometry.create_collision_shape(
            component.model.scale, p
        )
        body_id = p.createMultiBody(
            0
            if component.static.get_value()
            else component.mass.get_value(),  # Note: mass = 0 means static
            collider,
            basePosition=tuple(component.model.position.tolist()),
            # Encode euler angles as quaternion
            baseOrientation=p.getQuaternionFromEuler(
                tuple(-r for r in component.model.rotation.tolist())
            ),
        )

        # Remember that we added this entity
        self.added_entities[eid] = (body_id, component.model)

        friction = component.friction.get_value()
        p.changeDynamics(
            body_id, -1, lateralFriction=friction, spinningFriction=friction * 0.01
        )
        component.body_id = body_id

    def init(self):
        self.added_entities: Dict[int, int] = {}
        self.world: World = self.world

        # Loop through each physics component and add it to the physics simulation
        for (eid, component) in self.world.get_component(PhysicsComponent):
            if eid not in self.added_entities:
                self.add_rigid_body(component, eid)

    def process(self):
        for (eid, component) in self.world.get_component(PhysicsComponent):
            if not component.model.active:
                # If the model is disabled (inactive), remove it from the physics simulation
                if eid in self.added_entities:
                    p.removeBody(component.body_id)
                    del self.added_entities[eid]
                continue

            if eid not in self.added_entities:
                # Add new bodies to the physics simulation
                self.add_rigid_body(component, eid)

        # Run the simulation
        p.stepSimulation()

        for (eid, component) in self.world.get_component(PhysicsComponent):
            if not component.static.get_value():
                # Update the model position and rotation from the physics simulation
                pos, rot = p.getBasePositionAndOrientation(component.body_id)
                component.model.set_position(pos)
                x, y, z = p.getEulerFromQuaternion(rot)
                component.model.set_rotation((-x, -y, -z))

        # Perform collision detection before next step to allow for custom scripts to
        # react to collisions
        p.performCollisionDetection()


def CustomComponentQuery(id) -> str:
    return f"custom_{id}.py"


class CustomComponent(Component):
    """A custom component that can modify an entity."""

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
    """The processor for custom scripts."""

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
        """Get a processor from a script file."""
        from nimble.common import current_project

        if path is None:
            return BaseComponent()

        with open(current_project.folder / path, "r") as f:
            script_file_contents = f.read()

        @with_gui_logging_default({})  # Route errors to the GUI logger
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
                # Only run init if it exists
                processor.init()

    @with_gui_logging
    def process(self):
        for pid, processor in self.processors.items():
            for (_, component) in self.world.get_component(pid):
                # Process every custom component and pass in it's model
                processor.process(component.model)

    def add_keys_attr(self, keys: PressedKeys):
        """Add the pressed keys attribute to the processors."""
        for processor in self.processors.values():
            processor.keys = keys


class BaseComponent(Processor):
    def init(self):
        pass

    def process(self, model: Model):
        pass


class NoProcessor(BaseComponent):
    """A processor that gives a warning on initialization."""

    def init(self):
        logging.getLogger("nimble").error(
            "No component found. There is likely some error above, which prevented a component from being loaded."
        )

    def process(self, model: Model):
        pass


class CameraComponent:
    def __init__(self, camera: OrbitCamera):
        self.camera = camera
