import os
from enum import Enum
from abc import ABC, abstractmethod
import itertools
from typing import Any, Generic, List, TypeVar, Union
from dataclasses import dataclass

from nimble.objects.model import Model


ComponentId = str

PathLike = Union[str, bytes, os.PathLike]
T = TypeVar("T")


class FileType(Enum):
    CODE = 1


@dataclass
class FileSlot:
    file_type: FileType


@dataclass
class ModelSlot:
    pass


SlotType = Union[FileSlot, ModelSlot]


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

    @abstractmethod
    def slot_type(self) -> SlotType:
        pass


class ScriptSlot(ComponentSlot[PathLike]):
    ty = FileSlot(file_type=FileType.CODE)

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

    def slot_type(self) -> SlotType:
        return self.ty


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
