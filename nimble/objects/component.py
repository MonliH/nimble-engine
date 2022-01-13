import os
from abc import ABC, abstractmethod
import itertools
from typing import Any, Generic, List, TypeVar, Union

from nimble.objects.model import Model


ComponentId = str

PathLike = Union[str, bytes, os.PathLike]
T = TypeVar("T")


class ComponentSlot(ABC, Generic[T]):
    @abstractmethod
    def validate(self, value: Any) -> bool:
        pass

    @abstractmethod
    def insert_in_slot(self, value: T) -> bool:
        pass

    @abstractmethod
    def get_value(self) -> T:
        pass


class ScriptSlot(ComponentSlot[PathLike]):
    def __init__(self):
        self.filename: PathLike = ""

    def validate(self, value: Any) -> bool:
        return isinstance(value, PathLike)

    def insert_in_slot(self, value: PathLike) -> bool:
        if isinstance(value, PathLike):
            self.filename = value
            return True
        return False

    def get_value(self) -> PathLike:
        return self.filename


class Component:
    def __init__(self, model: Model):
        raise NotImplementedError("Component.__init__ not implemented")

    def update(self):
        raise NotImplementedError("Component.update not implemented")

    @staticmethod
    @property
    def display_name() -> str:
        raise NotImplementedError("Component.display_name not implemented")

    @property
    def id(self) -> ComponentId:
        raise NotImplementedError("Component.id not implemented")

    def slots(self) -> List[ComponentSlot]:
        pass


class CustomComponent(Component):
    _unique_id = itertools.count()

    def __init__(self, model: Model):
        self.model = model
        self._id = next(self._unique_id)

        self.script_slot = ScriptSlot()

    display_name = "Custom Script"

    @property
    def id(self) -> ComponentId:
        return f"custom_{self._id}"

    def slots(self) -> List[ComponentSlot]:
        return [self.script_slot]
