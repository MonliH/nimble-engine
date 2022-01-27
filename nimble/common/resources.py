from PyQt5.QtCore import QFile
from PyQt5.uic import loadUi


def shader(name) -> str:
    source_file = QFile(f":/shaders/{name}")
    source_file.open(QFile.ReadOnly)
    data = source_file.readAll()
    return str(data, encoding="utf-8")


def load_ui(path, widget):
    ui_file = QFile(path)
    ui_file.open(QFile.ReadOnly)
    loadUi(ui_file, widget)
    ui_file.close()
