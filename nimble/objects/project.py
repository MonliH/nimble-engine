from typing import Dict, Optional
from PyQt5.QtWidgets import QFileSystemModel

from nimble.objects.component import PathLike


class Project(QFileSystemModel):
    def __init__(self):
        super().__init__()
        self.folder: Optional[PathLike] = None

    def set_folder(self, folder: PathLike):
        self.folder = folder


current_project = Project()
