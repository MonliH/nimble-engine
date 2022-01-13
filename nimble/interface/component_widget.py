from typing import Optional, cast
from PyQt5.QtWidgets import QLabel, QWidget
from nimble.common.resources import load_ui

from nimble.objects.component import Component


class ComponentWidget(QWidget):
    def __init__(self, component: Component, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.component = component

        load_ui(":/ui/component.ui", self)
        self.component_name_title = cast(QLabel, self.component_name_title)
        self.component_name_title.setText(component.display_name)
        self.show()
