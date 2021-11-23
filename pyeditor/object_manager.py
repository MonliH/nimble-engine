import typing
from model import Model


class ObjectManager:
    def __init__(self) -> None:
        self.objects: typing.Dict[str, Model] = {}
        self.objects_list = []

    def add_object(self, name: str, obj: object) -> str:
        object_name = name if name not in self.objects else self.get_new_name(name)
        self.objects[object_name] = obj
        self.objects_list.append(object_name)
        return object_name

    def get_object(self, name: str) -> Model:
        return self.objects[name]

    def first(self) -> str:
        return self.objects[self.objects_list[0]]

    def get_new_name(self, name: str) -> str:
        i = 1
        while f"{name}{i}" in self.objects:
            i += 1
        return f"{name}{i}"

    def render(self) -> None:
        for obj in self.objects.values():
            obj.render()
