import os
from enum import Enum
from abc import ABC, abstractmethod
import itertools
from typing import Any, Generic, List, Optional, TypeVar, Union
from dataclasses import dataclass
from pathlib import Path

from nimble.objects.model import Model


ComponentId = str

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


def display_slot_type(slot_type: SlotType) -> str:
    if isinstance(slot_type, FileSlot):
        return "File"
    elif isinstance(slot_type, ModelSlot):
        return "Model"
    else:
        raise ValueError(f"Unknown slot type: {slot_type}")


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
    def get_jsonable(self) -> Any:
        pass

    @abstractmethod
    def slot_type(self) -> SlotType:
        pass


class ScriptSlot(ComponentSlot[str]):
    ty = FileSlot(file_type=FileType.CODE)

    def __init__(self, filename: Optional[str] = None):
        self.filename: Optional[str] = filename

    def validate(self, value: Any) -> bool:
        return isinstance(value, Path)

    def insert_in_slot(self, value: Any) -> bool:
        if isinstance(value, (str)):
            self.filename = value
            return True
        elif value is None:
            self.filename = None
            return True
        return False

    def get_jsonable(self) -> Any:
        return self.filename if self.filename is not None else None

    def get_value(self) -> Optional[str]:
        return self.filename

    def slot_type(self) -> SlotType:
        return self.ty


class Component:
    def __init__(self):
        self.inited = False

    def update(self):
        raise NotImplementedError("Component.update not implemented")

    @staticmethod
    @property
    def display_name() -> str:
        raise NotImplementedError("Component.display_name not implemented")

    def slots(self) -> List[ComponentSlot]:
        raise NotImplementedError("Component.slots not implemented")

    def tick(self) -> None:
        raise NotImplementedError("Component.tick not implemented")

    def init(self) -> None:
        raise NotImplementedError("Component.init not implemented")


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

        self.script_slot = ScriptSlot(None if slot_params is None else slot_params[0])
        self.file = None
        self.inited = False

    display_name = "Custom Script"

    @property
    def id(self) -> ComponentId:
        return f"custom_{self._id}"

    def slots(self) -> List[ComponentSlot]:
        return [self.script_slot]

    def init(self):
        from nimble.objects.project import current_project

        with open(current_project.folder / self.script_slot.get_value(), "r") as f:
            self.script_file_contents = f.read()

    def tick(self):
        print(self.script_file_contents)
