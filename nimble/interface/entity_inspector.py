import math
from typing import List, Optional, Tuple, cast
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QWidget,
)
from PyQt5 import uic
from pyrr.objects.vector3 import Vector3

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

        self.spinners: List[Tuple[QDoubleSpinBox, QDoubleSpinBox, QDoubleSpinBox]] = [
            (
                self.x_position,
                self.y_position,
                self.z_position,
            ),
            (
                self.x_rotation,
                self.y_rotation,
                self.z_rotation,
            ),
            (
                self.x_scale,
                self.y_scale,
                self.z_scale,
            ),
        ]

        for i, spinner_row in enumerate(self.spinners):
            for j, spinner in enumerate(spinner_row):
                spinner.valueChanged.connect(
                    lambda _, i=i, j=j: self.spinner_changed(i, j)
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
            for i, spinner_row in enumerate(self.spinners):
                for j, spinner in enumerate(spinner_row):
                    value = self.get_idx(i, self.active)[j]
                    spinner.setValue(value if i != 1 else math.degrees(value))
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

    @staticmethod
    def get_idx(idx: int, obj: Model) -> Vector3:
        if idx == 0:
            return obj.position
        elif idx == 1:
            return obj.rotation
        elif idx == 2:
            return obj.scale

    def spinner_changed(self, row_idx: int, vector_idx: int):
        if self.active is not None:
            new_value = self.spinners[row_idx][vector_idx].value()
            self.get_idx(row_idx, self.active)[vector_idx] = (
                new_value if row_idx != 1 else math.radians(new_value)
            )
            if row_idx == 0:
                self.active.position_changed()
            elif row_idx == 1:
                self.active.rotation_changed()
            elif row_idx == 2:
                self.active.scale_changed()

            self.update_view()
