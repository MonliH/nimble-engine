import pathlib
from typing import Dict, Optional
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QDir

from nimble.objects.component import PathLike
from nimble.objects.scene import Scene


class ProjectObserver:
    def project_changed(self):
        pass


class Project(QFileSystemModel):
    def __init__(
        self,
        project_name: Optional[str] = None,
        project_folder: Optional[PathLike] = None,
    ):
        super().__init__()
        self.name = project_name
        self.folder = project_folder

        self.observers: Dict[str, ProjectObserver] = {}
        self._scene = Scene()

    @property
    def scene(self):
        return self._scene

    def project_is_saved(self) -> bool:
        return self.folder is not None and self.name is not None

    def set_folder_and_name(self, folder: PathLike, name: str):
        self.setRootPath(QDir.rootPath())
        self.folder = pathlib.Path(folder) / f"{name}/"
        self.folder.mkdir(parents=True, exist_ok=True)
        self.name = name
        for observer in self.observers.values():
            observer.project_changed()

    def get_project_display_name(self) -> str:
        if self.project_is_saved():
            return f"{self.name} - {self.folder}"
        else:
            return "Untitled Project"

    def add_observer(self, key: str, observer: ProjectObserver):
        self.observers[key] = observer

    def remove_observer(self, key: str):
        del self.observers[key]


current_project = Project()
