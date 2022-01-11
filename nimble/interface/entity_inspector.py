from typing import Optional, Tuple, cast
from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
    QVBoxLayout,
    QPushButton,
)
from PyQt5 import uic
from nimble.common.resources import ui_file

from nimble.objects.model import Model, ModelObserver
from nimble.objects.scene import SceneObserver
from nimble.objects.scene import active_scene


class ModelWidget(QWidget, SceneObserver, ModelObserver):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.active = None

        uic.loadUi(ui_file("entity_inspector.ui"), self)
        self.object_name_title = cast(QLabel, self.object_name_title)
        self.object_name_input = cast(QLineEdit, self.object_name_input)
        self.entity_info = cast(QWidget, self.entity_info)

        self.position_spinners: Tuple[
            QDoubleSpinBox, QDoubleSpinBox, QDoubleSpinBox
        ] = (
            self.x_position,
            self.y_position,
            self.z_position,
        )

        for i, spinner in enumerate(self.position_spinners):
            spinner.valueChanged.connect(
                lambda _, i=i: self.position_spinner_changed(i)
            )

        self.update_view()
        self.object_name_input.textChanged.connect(self.rename_object)

        active_scene.register_observer(self)
        active_scene.register_active_obj_observer(self, "entity_inspector")

    def select_changed(self, idx: int, obj: Optional[Model]) -> None:
        if obj is not self.active:
            self.active = obj
            self.active_idx = idx
            self.update_view()

    def minimumSizeHint(self) -> QSize:
        return QSize(10, 100)

    def update_view(self):
        if self.active is not None:
            self.object_name_title.setText(f"Object ({self.active.name})")
            self.entity_info.show()
            self.object_name_input.setText(self.active.name)
            for i, spinner in enumerate(self.position_spinners):
                spinner.setValue(self.active.position[i])
        else:
            self.object_name_title.setText(f"No object selected")
            self.entity_info.hide()

    def obj_name_changed(self, idx: int, obj: Model):
        if self.active_idx == idx:
            self.update_view()

    def rename_object(self, new_name: str):
        if self.active is not None:
            active_scene.rename_obj(self.active_idx, new_name)
            self.object_name_input.setText(new_name)

    def translation_changed(self, obj: Model) -> None:
        self.update_view()

    def position_spinner_changed(self, idx: int):
        if self.active is not None:
            self.active.position[idx] = self.position_spinners[idx].value()
            self.active.position_changed()
            self.update_view()
