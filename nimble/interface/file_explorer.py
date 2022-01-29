"""A virtual file explorer to look at project files."""

from typing import Optional, cast
from PyQt5.QtWidgets import QTreeView, QWidget, QFileSystemModel

from nimble.common.resources import load_ui
from nimble.common import ProjectObserver, current_project


class FileExplorer(QWidget, ProjectObserver):
    def project_changed(self):
        active_folder = str(current_project.folder)
        self.model.setRootPath(active_folder)
        self.files.setRootIndex(self.model.index(active_folder))

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        current_project.add_observer("file_explorer", self)
        load_ui(":/ui/file_explorer.ui", self)
        self.files = cast(QTreeView, self.files)
        self.model = QFileSystemModel()
        if current_project.saved_project_is_open():
            self.model.setRootPath("")
        self.files.setModel(self.model)
