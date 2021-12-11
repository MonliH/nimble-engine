from typing import Optional, Dict, Tuple

from moderngl.framebuffer import Framebuffer
from moderngl_window import activate_context
from moderngl_window.scene.camera import Camera
from userspace.model import Model
from interface.orbit_camera import OrbitCamera
import common.ray_cast as ray_cast


class ObjectManager:
    def __init__(self) -> None:
        self.objects: Dict[str, Model] = {}
        self.objects_list = []
        self.active_idx = -1

    def set_active(self, idx: int):
        self.active_idx = idx

    @property
    def active(self) -> Optional[str]:
        if 0 <= self.active_idx < len(self.objects_list):
            return self.objects_list[self.active_idx]

    @property
    def has_object_selected(self) -> bool:
        return self.active_idx != -1

    def delete_obj(self, idx: int) -> None:
        if 0 <= idx < len(self.objects_list):
            if idx == self.active_idx:
                self.active_idx = -1
            elif idx < self.active_idx:
                self.active_idx -= 1
            self.objects[self.objects_list[idx]].geometry.vao.release()
            del self.objects[self.objects_list[idx]]
            del self.objects_list[idx]

    def get_obj_from_idx(self, idx: int) -> Model:
        if 0 <= idx < len(self.objects_list):
            return self.objects[self.objects_list[idx]]

    def get_obj_name(self, idx) -> str:
        if 0 <= idx < len(self.objects_list):
            return self.objects_list[idx]

    def get_active(self) -> Optional[Model]:
        if self.active in self.objects:
            return self.objects[self.active]

    def add_obj(self, name: str, obj: object) -> int:
        object_name = name if name not in self.objects else self.get_new_name(name)
        self.objects[object_name] = obj
        idx = len(self.objects_list)
        self.objects_list.append(object_name)
        return idx

    def get_obj(self, name: str) -> Model:
        return self.objects[name]

    def __getitem__(self, key: str) -> Model:
        return self.objects[key]

    def get_new_name(self, name: str) -> str:
        i = 2
        while f"{name}{i}" in self.objects:
            i += 1
        return f"{name}{i}"

    def render(
        self, camera: Camera, active_fbo: Framebuffer, screen: Framebuffer
    ) -> None:
        for obj in self.objects.values():
            obj.render(camera)
        active_fbo.clear()
        active = self.get_active()
        if active:
            active_fbo.use()
            active.render(camera, bounding=False)
        screen.use()

    def cast_ray(
        self, x: int, y: int, camera: OrbitCamera
    ) -> Optional[Tuple[str, int]]:
        ray = ray_cast.get_ray(x, y, camera)
        for i, obj_str in enumerate(self.objects_list):
            obj = self.objects[obj_str]
            if ray_cast.does_intersect(
                obj.bounding_box_world,
                ray,
            ):
                return (obj_str, i)

        return None
