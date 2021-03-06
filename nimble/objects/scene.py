from __future__ import annotations
from typing import Any, List, Optional, Dict, Tuple
from PyQt5 import QtCore

from PyQt5.QtCore import QAbstractListModel, Qt
from PyQt5 import QtGui

from moderngl.framebuffer import Framebuffer
from moderngl_window.scene.camera import Camera
from pyrr import Vector3

from nimble.common.event_listener import InputObserver
from nimble.common.models.size import Size
import nimble.common.models.ray_cast as ray_cast
from nimble.objects import Cube, Plane, Ray, Material, Model, ModelObserver


class SceneObserver:
    """A base class for classes that want to be notified when the scene changed."""

    def select_changed(self, idx: int, obj: Optional[Model]) -> None:
        pass

    def obj_deleted(self, deleted_idx: int) -> None:
        pass

    def obj_name_changed(self, idx: int, obj: Model) -> None:
        pass


class Scene(InputObserver, QAbstractListModel):
    """A scene object, which holds a collection of objects and the current selected object."""

    def __init__(self) -> None:
        super().__init__()
        self.objects: Dict[str, Model] = {}
        self.objects_list: List[str] = []
        self.active_idx = -1

        self.observers: List[SceneObserver] = []
        self.active_obj_observers: Dict[str, ModelObserver] = {}

    @classmethod
    def default_scene(cls):
        """Create a default scene, with a cube and a plane."""
        scene = cls()
        cube = Model(
            Material("viewport"),
            geometry=Cube(),
            name="Cube",
            position=Vector3((0, 0.5, 0)),
        )
        scene.add_obj(cube)
        scene.add_obj(
            Model(
                Material("viewport"),
                geometry=Plane(),
                name="Plane",
                scale=Vector3((7, 1, 7)),
                position=Vector3((0, -0.001, 0)),
            )
        )
        return scene

    def replace(self, new_model: Scene):
        """Replace the current scene with the given scene, in place."""

        # Tell observers all objects are about to be deleted
        for observer in self.observers:
            for i in self.objects:
                observer.obj_deleted(i)

        # Delete all objects
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
        """Change the active object to the object at the given index."""
        old_obj = self.get_actikve()
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
        """Rename the object at the given index."""
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
        """Delete the object at the given index."""
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
        """Get the object at the given index."""
        if 0 <= idx < len(self.objects_list):
            return self.objects[self.objects_list[idx]]

    def get_obj_name(self, idx) -> str:
        """Get the name of the object at the given index."""
        if 0 <= idx < len(self.objects_list):
            return self.objects_list[idx]

    def get_active(self) -> Optional[Model]:
        """Get the currently selected object."""
        if self.active in self.objects:
            return self.objects[self.active]

    def add_obj(self, obj: Model) -> int:
        """Add an object to the scene, and return the index it was inserted at."""
        name = obj.name
        object_name = name if name not in self.objects else self.get_new_name(name)
        obj.set_name(object_name)
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
        """Get the object with the given name."""
        return self.objects[name]

    def __getitem__(self, key: str) -> Model:
        return self.objects[key]

    def get_new_name(self, name: str) -> str:
        """Get a new name for an object that is unique, based on the given name."""
        i = 2
        while f"{name}{i}" in self.objects:
            i += 1
        return f"{name}{i}"

    def render(
        self, camera: Camera, active_fbo: Framebuffer, screen: Framebuffer
    ) -> None:
        """Render the scene to a `screen`, and the active object (if any) to
        the `active_fbo`."""
        for obj in self.objects.values():
            if obj.active:
                obj.render(camera)
        active_fbo.clear()
        active = self.get_active()
        if active:
            active_fbo.use()
            active.render(camera)
        screen.use()

    def cast_ray(self, ray: Ray) -> Optional[Tuple[str, int]]:
        """Cast a ray into the scene, and return the name and the index of the
        object it hit."""
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
