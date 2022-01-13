from __future__ import annotations
from typing import Any, List, Optional, Dict, Tuple
from PyQt5 import QtCore

from PyQt5.QtCore import QAbstractListModel, Qt
from PyQt5 import QtGui

from moderngl.framebuffer import Framebuffer
from moderngl_window.scene.camera import Camera

from nimble.common.event_listener import InputObserver
from nimble.common.models.size import Size
from nimble.objects.geometry import Ray
from nimble.objects.model import Model, ModelObserver
import nimble.common.models.ray_cast as ray_cast


class SceneObserver:
    def select_changed(self, idx: int, obj: Optional[Model]) -> None:
        pass

    def obj_deleted(self, deleted_idx: int) -> None:
        pass

    def obj_name_changed(self, idx: int, obj: Model) -> None:
        pass


class Scene(InputObserver, QAbstractListModel):
    def __init__(self) -> None:
        super().__init__()
        self.objects: Dict[str, Model] = {}
        self.objects_list: List[str] = []
        self.active_idx = -1

        self.observers: List[SceneObserver] = []
        self.active_obj_observers: Dict[str, ModelObserver] = {}

    def replace(self, new_model: Scene):
        for observer in self.observers:
            for i in self.objects:
                observer.obj_deleted(i)

        self.objects = new_model.objects
        self.objects_list = new_model.objects_list
        self.active_idx = new_model.active_idx

        self.emit_changed(0, len(self.objects_list))

        for observer in self.observers:
            observer.select_changed(self.active_idx, self.get_active())

    def register_observer(self, observer: SceneObserver):
        self.observers.append(observer)

    def register_active_obj_observer(self, observer: ModelObserver, key: str):
        self.active_obj_observers[key] = observer

    def unregister_active_obj_observer(self, key: str):
        del self.active_obj_observers[key]

    def set_active(self, idx: int):
        old_obj = self.get_active()
        new_obj = self.get_obj_from_idx(idx)

        if old_obj is not new_obj:
            if old_obj is not None:
                old_obj.remove_all_observers()

            self.active_idx = idx
            active = self.get_active()

            if active is not None:
                active.set_all_observers(self.active_obj_observers)

            for observer in self.observers:
                observer.select_changed(self.active_idx, active)

    @property
    def active(self) -> Optional[str]:
        if 0 <= self.active_idx < len(self.objects_list):
            return self.objects_list[self.active_idx]

    @property
    def has_object_selected(self) -> bool:
        return self.active_idx != -1

    def rename_obj(self, idx: int, new_name: str):
        old_name = self.get_obj_name(idx)
        obj = self.get_obj_from_idx(idx)
        if obj is not None:
            obj.set_name(new_name)
            self.objects_list[idx] = new_name
            del self.objects[old_name]
            self.objects[new_name] = obj
            self.emit_changed(idx)
            for observer in self.observers:
                observer.obj_name_changed(idx, obj)

    def delete_obj(self, idx: int) -> None:
        if 0 <= idx < len(self.objects_list):
            if idx == self.active_idx:
                self.active_idx = -1
            elif idx < self.active_idx:
                self.active_idx -= 1
            self.objects[self.objects_list[idx]].geometry.vao.release()
            del self.objects[self.objects_list[idx]]
            del self.objects_list[idx]
            self.emit_changed(idx)

            for observer in self.observers:
                observer.obj_deleted(idx)

    def get_obj_from_idx(self, idx: int) -> Optional[Model]:
        if 0 <= idx < len(self.objects_list):
            return self.objects[self.objects_list[idx]]

    def get_obj_name(self, idx) -> str:
        if 0 <= idx < len(self.objects_list):
            return self.objects_list[idx]

    def get_active(self) -> Optional[Model]:
        if self.active in self.objects:
            return self.objects[self.active]

    def add_obj(self, obj: object) -> int:
        name = obj.name
        object_name = name if name not in self.objects else self.get_new_name(name)
        self.objects[object_name] = obj
        idx = len(self.objects_list)
        self.objects_list.append(object_name)
        self.emit_changed(idx)
        return idx

    def emit_changed(self, start: int, end: Optional[int] = None):
        if end is None:
            end = start + 1
        self.dataChanged.emit(
            self.index(start, 0), self.index(end, 0), [Qt.DisplayRole]
        )

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
            active.render(camera)
        screen.use()

    def cast_ray(self, ray: Ray) -> Optional[Tuple[str, int]]:
        min_dist = float("inf")
        min_dist_obj = None
        for i, obj_str in enumerate(self.objects_list):
            obj = self.objects[obj_str]
            dist = ray_cast.ray_intersect(
                obj.bounding_box_world,
                ray,
            )
            if dist is not None:
                if dist[0] < min_dist:
                    min_dist_obj = (obj_str, i)
                    min_dist = dist[0]

        return min_dist_obj

    def mouse_pressed(self, event: QtGui.QMouseEvent, size: Size):
        if event.button() == Qt.LeftButton:
            ray = ray_cast.get_ray(event.pos(), size)
            hit_object = self.cast_ray(ray)
            if hit_object is not None:
                self.set_active(hit_object[1])
            else:
                self.set_active(-1)

    def key_pressed(self, event: QtGui.QKeyEvent, size: Size):
        if event.key() == Qt.Key_Delete:
            self.delete_obj(self.active_idx)

    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        return len(self.objects_list)

    def data(self, index: QtCore.QModelIndex, role: int) -> Any:
        obj_name = self.objects_list[index.row()]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return obj_name

    def headerData(
        self, section: int, orientation: QtCore.Qt.Orientation, role: int
    ) -> Any:
        return "Object Name"
