from typing import Optional, cast
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QComboBox, QSizePolicy
from PyQt5.QtCore import Qt

from nimble.common.resources import load_ui
from nimble.objects.component import Component, ComponentSlot, display_slot_type
from nimble.objects.project import current_project


class SlotWidget(QWidget):
    def __init__(self, slot: ComponentSlot, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.slot = slot
        load_ui(":/ui/component_slot.ui", self)
        self.label.setText(display_slot_type(slot.ty))
        self.options = QComboBox(self)
        self.options.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.options.setGeometry(self.options.geometry().adjusted(0, 0, 0, -15))
        self.options.setModel(current_project.scripts)
        self.options.currentIndexChanged.connect(self.on_index_changed)
        idx = current_project.scripts.get_index(self.slot.get_value())
        self.options.setCurrentIndex(idx)
        self.field.addWidget(self.options)

    def on_index_changed(self, index: int):
        self.slot.insert_in_slot(self.options.itemData(index, Qt.UserRole))


class ComponentWidget(QWidget):
    def __init__(self, component: Component, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.component = component

        load_ui(":/ui/component.ui", self)
        self.component_name_title = cast(QLabel, self.component_name_title)
        self.component_name_title.setText(component.display_name)
        self.component_slots = cast(QVBoxLayout, self.component_slots)
        for slot in self.component.slots():
            self.component_slots.addWidget(SlotWidget(slot))
        self.show()
