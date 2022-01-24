from typing import Optional, cast, Callable
from PyQt5.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QDialog,
    QCheckBox,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQtAds.QtAds import ads

from nimble.common.resources import load_ui
from nimble.interface.warning_popup import WarningPopup
from nimble.interface.editor import Editor
from nimble.objects import Component, Slot, SlotType
from nimble.common import current_project


class CreateScript(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        load_ui(":/ui/new_script_popup.ui", self)
        self.buttonBox.setEnabled(False)
        self.script_name.textChanged.connect(self.update_button_state)
        self.buttonBox.accepted.disconnect(self.accept)
        self.buttonBox.accepted.connect(self.accept_pressed)

    def update_button_state(self):
        self.buttonBox.setEnabled(self.script_name.text() != "")

    def accept_pressed(self):
        name = self.script_name.text() + ".py"
        full_path = current_project.folder / name
        if full_path in current_project.scripts:
            warning_text = f'A script with name "{name}" already exists.'
            warning = WarningPopup(warning_text)
            ok = warning.exec()
            if ok != QDialog.Accepted:
                return

        super().accept()


class FileWidget(QWidget):
    def __init__(
        self,
        slot: Slot,
        open_window: Callable[[ads.CDockWidget], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        assert slot.ty == SlotType.FILE

        load_ui(":/ui/file_widget_slot.ui", self)

        self.slot = slot
        self.options.setModel(current_project.scripts)
        self.options.currentIndexChanged.connect(self.on_index_changed)
        idx = current_project.scripts.get_index(self.slot.get_value())

        text = "Edit" if self.slot.get_value() is not None else "New"
        self.file_widget_button.setText(text)
        self.file_widget_button.clicked.connect(self.on_button_clicked)

        self.options.setCurrentIndex(idx)

        self.open_window = open_window

    def on_index_changed(self, index: int):
        self.slot.insert_in_slot(self.options.itemData(index, Qt.UserRole))
        self.file_widget_button.setText(
            "Edit" if self.slot.get_value() is not None else "New"
        )

    def on_button_clicked(self):
        if self.slot.get_value() is not None:
            # Open the script editor
            self.open_window(Editor(current_project.folder / self.slot.get_value()))
        else:
            # Create a new script
            dialog = CreateScript()
            ok = dialog.exec()
            if ok == QDialog.Accepted:
                script = current_project.create_script(dialog.script_name.text())
                self.slot.insert_in_slot(script)
                idx = current_project.scripts.get_index(self.slot.get_value())
                self.options.setCurrentIndex(idx)


class SlotWidget(QWidget):
    def __init__(
        self,
        slot: Slot,
        open_window: Callable[[ads.CDockWidget], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.slot = slot
        load_ui(":/ui/component_slot.ui", self)
        self.label.setText(slot.display())

        if slot.ty == SlotType.FILE:
            self.field.addWidget(FileWidget(slot, open_window, self))
        if slot.ty == SlotType.BOOLEAN:
            self.field.addWidget(BooleanWidget(slot, self))


class BooleanWidget(QWidget):
    def __init__(self, slot: Slot, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.slot = slot

        self.frame = QVBoxLayout(self)
        self.frame.setContentsMargins(0, 0, 0, 0)
        self.checkbox = QCheckBox(self)
        self.frame.addWidget(self.checkbox)
        self.frame.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.checkbox.stateChanged.connect(self.on_state_change)
        self.checkbox.setChecked(self.slot.get_value())

    def on_state_change(self, state):
        checked = state == Qt.Checked
        self.slot.insert_in_slot(checked)


class ComponentWidget(QWidget):
    def __init__(
        self,
        component: Component,
        open_window: Callable[[ads.CDockWidget], None],
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.component = component
        self.open_window = parent.open_window

        load_ui(":/ui/component.ui", self)
        self.component_name_title = cast(QLabel, self.component_name_title)
        self.component_name_title.setText(component.display_name)
        self.component_slots = cast(QVBoxLayout, self.component_slots)
        for slot in self.component.slots():
            self.component_slots.addWidget(SlotWidget(slot, open_window, self))
        self.show()
