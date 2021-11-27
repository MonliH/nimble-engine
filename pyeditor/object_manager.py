from typing import Optional, Dict, Tuple

from moderngl.framebuffer import Framebuffer
from model import BoundingBox, Model
from orbit_camera import OrbitCamera
from pyrr import Vector3, Vector4


# (origin, direction, inv_direction, sign)
Ray = Tuple[Vector3, Vector3, Vector3, Tuple[int, int, int]]


def create_ray(origin: Vector3, direction: Vector3) -> Ray:
    inv_direction = Vector3((1.0 / direction.x, 1.0 / direction.y, 1.0 / direction.z))
    sign = (inv_direction.x < 0, inv_direction.y < 0, inv_direction.z < 0)
    return (origin, direction, inv_direction, sign)


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

    def delete_obj(self, idx: int) -> None:
        if 0 <= idx < len(self.objects_list):
            if idx == self.active_idx:
                self.active_idx = -1
            elif idx < self.active_idx:
                self.active_idx -= 1
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

    def render(self, active_fbo: Framebuffer, screen: Framebuffer) -> None:
        for obj in self.objects.values():
            obj.render()
        active_fbo.clear()
        active = self.get_active()
        if active:
            active_fbo.use()
            active.render()
        screen.use()

    def cast_ray(
        self, x: int, y: int, camera: OrbitCamera
    ) -> Optional[Tuple[str, int]]:
        width, height = camera.width, camera.height
        x = (2.0 * x) / width - 1.0
        y = 1.0 - (2.0 * y) / height
        z = 1.0

        ray_nds = Vector3((x, y, z), dtype="f4")
        ray_clip = Vector4((ray_nds.x, ray_nds.y, -1.0, 1.0), dtype="f4")
        ray_eye = (~camera.proj) * ray_clip
        ray_eye = Vector4((ray_eye.x, ray_eye.y, -1.0, 0.0), dtype="f4")

        ray_wor = Vector3(((~camera.view) * ray_eye).xyz, dtype="f4").normalized
        orig = camera.position

        for i, obj_str in enumerate(self.objects_list):
            obj = self.objects[obj_str]
            ray = create_ray(orig, ray_wor)
            if self.does_intersect(
                obj.bounding_box_world,
                ray,
            ):
                return (obj_str, i)

        return None

    def does_intersect(
        self,
        bounds: BoundingBox,
        r: Ray,
    ) -> bool:
        (orig, dir, invdir, sign) = r

        tmin = (bounds[sign[0]].x - orig.x) * invdir.x
        tmax = (bounds[1 - sign[0]].x - orig.x) * invdir.x

        tymin = (bounds[sign[1]].y - orig.y) * invdir.y
        tymax = (bounds[1 - sign[1]].y - orig.y) * invdir.y

        if (tmin > tymax) or (tymin > tmax):
            return False
        if tymin > tmin:
            tmin = tymin
        if tymax < tmax:
            tmax = tymax

        tzmin = (bounds[sign[2]].z - orig.z) * invdir.z
        tzmax = (bounds[1 - sign[2]].z - orig.z) * invdir.z

        if (tmin > tzmax) or (tzmin > tmax):
            return False
        if tzmin > tmin:
            tmin = tzmin
        if tzmax < tmax:
            tmax = tzmax

        return True
