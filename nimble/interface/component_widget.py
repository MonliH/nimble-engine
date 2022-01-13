from typing import Optional
from PyQt5.QtWidgets import QWidget
from nimble.common.resources import load_ui

from nimble.objects.component import Component


class ComponentWidget(QWidget):
    def __init__(self, component: Component, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.component = component

        load_ui(":/ui/component.ui", self)
        self.show()
