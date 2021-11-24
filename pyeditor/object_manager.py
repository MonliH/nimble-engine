from typing import Optional, Dict

from moderngl.framebuffer import Framebuffer
from model import Model


class ObjectManager:
    def __init__(self) -> None:
        self.objects: Dict[str, Model] = {}
        self.objects_list = []
        self.active_idx = 0

    def set_active(self, idx: int):
        self.active_idx = idx

    @property
    def active(self):
        return self.objects_list[self.active_idx]

    def get_active(self) -> Optional[Model]:
        if self.active in self.objects:
            return self.objects[self.active]

    def add_object(self, name: str, obj: object) -> int:
        object_name = name if name not in self.objects else self.get_new_name(name)
        self.objects[object_name] = obj
        idx = len(self.objects_list)
        self.objects_list.append(object_name)
        return idx

    def get_object(self, name: str) -> Model:
        return self.objects[name]

    def __getitem__(self, key: str) -> Model:
        return self.objects[key]

    def get_new_name(self, name: str) -> str:
        i = 2
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
