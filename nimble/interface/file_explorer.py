"""A virtual file explorer to look at project files."""

from typing import Optional, cast
from PyQt5.QtWidgets import QTreeView, QWidget, QFileSystemModel

from nimble.common.resources import load_ui
from nimble.objects.project import ProjectObserver, current_project


class FileExplorer(QWidget, ProjectObserver):
    def project_changed(self):
        print(current_project.folder)
        self.files.setRootIndex(self.model.index(str(current_project.folder)))

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        current_project.add_observer("file_explorer", self)
        load_ui(":/ui/file_explorer.ui", self)
        self.files = cast(QTreeView, self.files)
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.files.setModel(self.model)
