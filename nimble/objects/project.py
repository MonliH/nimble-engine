from typing import Dict, Optional
from PyQt5.QtWidgets import QFileSystemModel

from nimble.objects.component import PathLike


class ProjectObserver:
    def project_changed():
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

    def project_is_saved(self) -> bool:
        return self.folder is not None and self.name is not None

    def set_folder_and_name(self, folder: PathLike, name: str):
        self.folder = folder
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
