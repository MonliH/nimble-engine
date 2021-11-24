from typing import Optional, Dict

from moderngl.framebuffer import Framebuffer
from model import Model


class ObjectManager:
    def __init__(self) -> None:
        self.objects: Dict[str, Model] = {}
        self.objects_list = []
        self.active = ""

    def set_active(self, obj_name: str):
        if obj_name in self.objects_list:
            self.active = obj_name

    def get_active(self) -> Optional[Model]:
        return self.objects[self.active]

    def add_object(self, name: str, obj: object) -> str:
        object_name = name if name not in self.objects else self.get_new_name(name)
        self.objects[object_name] = obj
        self.objects_list.append(object_name)
        return object_name

    def get_object(self, name: str) -> Model:
        return self.objects[name]

    def first(self) -> str:
        return self.objects[self.objects_list[0]]

    def __getitem__(self, key: str) -> Model:
        return self.objects[key]

    def get_new_name(self, name: str) -> str:
        i = 1
        while f"{name}{i}" in self.objects:
            i += 1
        return f"{name}{i}"

    def render(self, active_fbo: Framebuffer, screen: Framebuffer) -> None:
        for obj in self.objects.values():
            obj.render()
        active_fbo.clear()
        active = self.get_active()
        if active:
            active_fbo.use()
            active.render()
        screen.use()
