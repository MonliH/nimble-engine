from typing import Optional, cast
from PyQt5.QtWidgets import QDialog, QWidget, QLabel

from nimble.common.resources import load_ui


class WarningPopup(QDialog):
    def __init__(self, warn_text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        load_ui(":/ui/warning_popup.ui", self)
        self.warning = cast(QLabel, self.warning)
        self.warning.setText(warn_text)
