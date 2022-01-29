from __future__ import annotations
import glob
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QDir, QAbstractListModel, QFileSystemWatcher, QModelIndex, Qt
from PyQt5.QtGui import QIcon
import json

from nimble.common.serialize import (
    serialize_model,
    serialize_scene,
    unserialize_model,
    unserialize_scene,
)
from nimble.objects import Scene
from nimble.resources import script_boilerplate


class ProjectObserver:
    """A base class for classes that want to be notified when the current project changes."""

    def project_changed(self):
        pass


class Project(QFileSystemModel):
    """A single nimble project."""

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
        self._scripts = ScriptList()

        self.copied: Any = None

    @staticmethod
    def get_scene_file(folder: Path) -> Path:
        return folder / "scene.nimscn"

    @staticmethod
    def get_project_file(folder: Path) -> Path:
        return folder / "project.nimproj"

    @property
    def scene(self):
        return self._scene

    @property
    def project_file(self) -> Path:
        return self.get_project_file(self.folder)

    def saved_project_is_open(self) -> bool:
        return self.folder is not None and self.name is not None

    def copy(self):
        if self.scene.has_object_selected is not None:
            self.copied = serialize_model(self.scene.get_active())
        else:
            self.copied = None

    def paste(self):
        if self.copied is not None:
            _id = self.scene.add_obj(unserialize_model(self.copied))
            self.scene.set_active(_id)

    def save_scene(self):
        """Save the current scene to the project folder."""
        scene_dict = serialize_scene(current_project.scene)
        json.dump(scene_dict, open(self.get_scene_file(self.folder), "w"))

    def _load_scene(self, filename: Path):
        """Load the scene from the given filename."""
        scene_dict = json.load(open(filename, "r"))
        scene = unserialize_scene(scene_dict)
        self._scene.replace(scene)

    def save_project(self):
        """Save the current project to the project folder."""
        json.dump({"name": self.name}, open(self.get_project_file(self.folder), "w"))

    def _load_project(self, filename: Path):
        """Load the project from the given filename."""
        proj_info = json.load(open(filename, "r"))
        self.name = proj_info["name"]

    def set_folder(self, file: Path, create: bool = False):
        """Load/create a project from a new folder."""
        if self.file_watcher is None:
            self.file_watcher = QFileSystemWatcher()
            self.file_watcher.directoryChanged.connect(self.dir_changed)

        self.file_watcher.removePath(str(self.folder))
        self.folder = file
        if create:
            self.folder.mkdir(parents=True, exist_ok=True)
        self.file_watcher.addPath(str(self.folder))
        self.dir_changed(str(self.folder))
        self.scripts.dataChanged.emit(
            self.scripts.index(0, 0),
            self.scripts.index(self.scripts.rowCount(self.scripts) - 1, 0),
        )

    def dir_changed(self, _path: str):
        old_len = len(self._scripts)
        for path in glob.glob(str(self.folder / "*.py")):
            self._scripts.add_script(Path(path).name)
        del self._scripts[:old_len]

    def load_project(self, file: Path):
        """Load a project from a `*.nimproj` file."""
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
    def scripts(self) -> ScriptList:
        return self._scripts

    def create_script(self, filename: str) -> Path:
        py_filename = filename + ".py"
        full_filename = current_project.folder / py_filename
        with open(full_filename, "w") as f:
            f.write(script_boilerplate.SCRIPT)
        self.scripts.add_script(py_filename)
        return py_filename

    def copy_assets(self, to_dir: str, to_name: str) -> List[Path]:
        to_dir_path = Path(to_dir) / to_name
        to_dir_path.mkdir(parents=True, exist_ok=True)
        scripts = []
        for script in self.scripts:
            shutil.copy(self.folder / str(script), str(to_dir_path))
            scripts.append(script)
        return scripts


class ScriptList(QAbstractListModel):
    """A list of scripts in the current project."""

    def __init__(self):
        super().__init__()
        self._scripts: List[str] = []

    def add_script(self, path: str):
        idx = len(self._scripts)
        self._scripts.append(path)
        self.rowsInserted.emit(QModelIndex(), idx, idx)

    def clear_script(self):
        scripts_len = len(self._scripts)
        self._scripts.clear()
        self.rowsRemoved.emit(QModelIndex(), 0, scripts_len)

    def remove_script(self, path: str):
        for i, p in enumerate(self._scripts):
            if p == path:
                del self._scripts[i]
                self.rowsRemoved.emit(QModelIndex(), i, i)
                break

    def rowCount(self, _parent) -> int:
        return len(self._scripts) + 1

    def data(self, index: QModelIndex, role: int) -> Any:
        if role == Qt.DecorationRole:
            return QIcon(":/img/python.svg")

        if index.row() == 0:
            if role == Qt.UserRole:
                return None
            elif role == Qt.DisplayRole:
                return "<No script selected>"
            return None

        if len(self._scripts) > index.row() - 1:
            fname = self._scripts[index.row() - 1]
            if role == Qt.DisplayRole:
                return str(fname)
            elif role == Qt.UserRole:
                return fname

    def get_index(self, script: Optional[str]) -> int:
        return self._scripts.index(script) + 1 if script is not None else 0

    def __iter__(self):
        return iter(self._scripts)

    def __contains__(self, script):
        return script in self._scripts

    def __len__(self):
        return len(self._scripts)

    def __delitem__(self, key):
        del self._scripts[key]


current_project = Project(project_folder=Path(QDir.temp().canonicalPath()))
