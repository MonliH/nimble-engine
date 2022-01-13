from pathlib import Path

from PyQt5.QtCore import QFile
from PyQt5.uic import loadUi


resource_dir = (Path(__file__).parent.parent / "resources").resolve()


def shader(name) -> Path:
    return resource_dir / "shaders" / name


def load_ui(path, widget):
    ui_file = QFile(path)
    ui_file.open(QFile.ReadOnly)
    loadUi(ui_file, widget)
    ui_file.close()
