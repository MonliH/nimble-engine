"""A virtual file explorer to look at project files."""

from typing import Optional, cast
from PyQt5.QtWidgets import QTreeView, QWidget

from nimble.common.resources import load_ui
from nimble.objects.project import current_project


class FileExplorer(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        load_ui(":/ui/file_explorer.ui", self)
        self.files = cast(QTreeView, self.files)
        self.files.setModel(current_project)
