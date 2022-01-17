from pathlib import Path
from typing import Dict, Optional
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QDir, QAbstractItemModel, QFileSystemWatcher
import json

from nimble.common.serialize import serialize_scene, unserialize_scene
from nimble.objects.scene import Scene


class ProjectObserver:
    def project_changed(self):
        pass


class Project(QFileSystemModel):
    def __init__(
        self,
        project_name: Optional[str] = None,
        project_folder: Optional[Path] = None,
    ):
        super().__init__()
        self.name = project_name
        self.folder = project_folder

        self.observers: Dict[str, ProjectObserver] = {}
        self.file_watcher = None
        self._scene = Scene()
        self._scripts: QAbstractItemModel = QAbstractItemModel()

    @staticmethod
    def get_scene_file(folder: Path) -> Path:
        return folder / "scene.nimscn"

    @staticmethod
    def get_project_file(folder: Path) -> Path:
        return folder / "project.nimproj"

    @property
    def scene(self):
        return self._scene

    def saved_project_is_open(self) -> bool:
        return self.folder is not None and self.name is not None

    def save_scene(self):
        scene_dict = serialize_scene(current_project.scene)
        json.dump(scene_dict, open(self.get_scene_file(self.folder), "w"))

    def _load_scene(self, filename: Path):
        scene_dict = json.load(open(filename, "r"))
        scene = unserialize_scene(scene_dict)
        self._scene.replace(scene)

    def save_project(self):
        json.dump({"name": self.name}, open(self.get_project_file(self.folder), "w"))

    def _load_project(self, filename: Path):
        proj_info = json.load(open(filename, "r"))
        self.name = proj_info["name"]

    def set_folder(self, file: Path, create: bool = False):
        if self.file_watcher is None:
            self.file_watcher = QFileSystemWatcher()
            self.file_watcher.directoryChanged.connect(self.dir_changed)

        self.file_watcher.removePath(str(self.folder))
        self.folder = file
        if create:
            self.folder.mkdir(parents=True, exist_ok=True)
        self.file_watcher.addPath(str(self.folder))

    def dir_changed(self, _path: str):
        pass

    def load_project(self, file: Path):
        file = Path(file)
        self.set_folder(file.parent)
        self._load_scene(self.get_scene_file(self.folder))
        self._load_project(file)

        for observer in self.observers.values():
            observer.project_changed()

        for observer in self.scene.observers:
            observer.select_changed(self.scene.active_idx, self.scene.get_active())

    def set_project_name(self, folder: Path, name: str):
        self.set_folder(Path(folder) / f"{name}/", create=True)
        self.name = name
        for observer in self.observers.values():
            observer.project_changed()

    def new_project(self, folder: Path, name: str):
        self.setRootPath(QDir.rootPath())
        self.set_folder(Path(folder) / f"{name}/", create=True)
        self.name = name
        self._scene.replace(Scene.default_scene())
        self.save_project()
        self.save_scene()
        for observer in self.observers.values():
            observer.project_changed()

    def get_project_display_name(self) -> str:
        if self.saved_project_is_open():
            return f"{self.name} - {self.folder}"
        else:
            return "Untitled Project"

    def add_observer(self, key: str, observer: ProjectObserver):
        self.observers[key] = observer

    def remove_observer(self, key: str):
        del self.observers[key]

    @property
    def scripts(self) -> QAbstractItemModel:
        return self._scripts


current_project = Project()
