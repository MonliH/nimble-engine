from typing import Optional
from PyQt5.QtWidgets import QWidget

from nimble.common.resources import load_ui


class RunWindow(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        load_ui(":/ui/run_tools.ui", self)
