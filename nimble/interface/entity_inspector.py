import math
from typing import Callable, List, Optional, Tuple, cast
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QColorDialog,
)
from pyrr.objects.vector3 import Vector3
from PyQtAds.QtAds import ads

from nimble.common.resources import load_ui
from nimble.interface.component_widget import ComponentWidget
from nimble.objects import (
    Component,
    CustomComponent,
    PhysicsComponent,
    BaseModel,
    ModelObserver,
    SceneObserver,
)
from nimble.common import current_project
from nimble.objects.base_model import BaseModel
from nimble.objects.model_2d import Model2D
from nimble.objects.model_3d import Model3D


class EntityInspector(QWidget, SceneObserver, ModelObserver):
    def __init__(
        self,
        open_window: Callable[[ads.CDockWidget], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.active = None

        load_ui(":/ui/entity_inspector.ui", self)
        self.open_window = open_window

        self.object_name_title = cast(QLabel, self.object_name_title)
        self.object_name_title.setMargin(10)
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

        current_project.scene.register_observer(self)
        current_project.scene.register_active_obj_observer(self, "entity_inspector")

        self.component_type = cast(QComboBox, self.component_type)
        self.components_types_list = [None, PhysicsComponent, CustomComponent]
        self.component_type.addItem("")
        for component in self.components_types_list[1:]:
            self.component_type.addItem(component.display_name)

        self.component_type.currentIndexChanged.connect(self.component_changed)

        self.add_component = cast(QPushButton, self.add_component)
        self.add_component.setEnabled(False)
        self.add_component.clicked.connect(self.add_component_clicked)

        self.components_list = cast(QVBoxLayout, self.components_list)
        self.scroll_area = cast(QScrollArea, self.scroll_area)
        self.scroll_area.setFrameShape(QAbstractItemView.NoFrame)

        self.pick_color = cast(QPushButton, self.pick_color)
        self.pick_color.pressed.connect(self.select_color)

    def create_color(self):
        return f"rgb({', '.join(str(int(f*255)) for f in self.active.material.color)})"

    def select_color(self):
        color = QColorDialog.getColor(
            QColor(*(int(f * 255) for f in self.active.material.color)),
            self,
            "Select Color",
            QColorDialog.DontUseNativeDialog,
        )
        rgb = (color.getRgb())[:3]
        self.active.material.set_color(tuple(f / 255 for f in rgb))
        self.update_view()

    def component_changed(self, idx: int):
        if self.components_types_list[idx] is None:
            self.add_component.setEnabled(False)
        else:
            self.add_component.setEnabled(True)

    def add_component_to_list(self, idx: int, component: Component):
        self.components_list.insertWidget(
            idx, ComponentWidget(component, self.open_window, self)
        )

    def remove_component(self, idx: int):
        self.components_list.itemAt(idx).widget().setParent(None)

    def add_component_clicked(self):
        ComponentCons = self.components_types_list[self.component_type.currentIndex()]
        if ComponentCons is not None:
            self.active.add_component(ComponentCons(self.active))

    def select_changed(self, idx: int, obj: Optional[BaseModel]) -> None:
        if obj is not self.active:
            self.active = obj
            self.active_idx = idx

            for i in reversed(range(self.components_list.count())):
                self.components_list.itemAt(i).widget().setParent(None)

            if self.active is not None:
                for component in self.active.components:
                    self.add_component_to_list(-1, component)
                self.object_name_input.setText(self.active.name)

            self.update_view()

    def component_removed(self, _obj: BaseModel, component_id: int) -> None:
        self.remove_component(component_id)

    def component_added(self, obj: BaseModel, component_id: int) -> None:
        self.add_component_to_list(-1, obj.components[component_id])

    def minimumSizeHint(self) -> QSize:
        return QSize(10, 100)

    def update_view(self):
        if self.active is not None:
            self.object_name_title.setText(f"Object ({self.active.name})")
            self.entity_info.show()
            for i, spinner_row in enumerate(self.spinners):
                values = self.get_idx(i, self.active)
                for j, spinner in enumerate(spinner_row):
                    if not spinner.hasFocus():
                        if values is not None and len(values) > j:
                            print(values, i, j)
                            value = values[j]
                            spinner.setValue(value if i != 1 else math.degrees(value))
                        else:
                            vstack: QVBoxLayout = getattr(
                                self, f"verticalLayout_{i * 3 + j+1}"
                            )
                            for i in range(vstack.count()):
                                vstack.itemAt(i).widget().setDisabled(True)

            self.pick_color.setStyleSheet(
                ";".join(self.pick_color.styleSheet().split(";")[:-1])
                + f"; background-color: {self.create_color()}"
            )
            self.pick_color.repaint()
        else:
            self.object_name_title.setText(f"No object selected")
            self.entity_info.hide()

    def obj_name_changed(self, idx: int, obj: BaseModel):
        if self.active_idx == idx:
            self.update_view()

    def rename_object(self, new_name: str):
        if self.active is not None:
            current_project.scene.rename_obj(self.active_idx, new_name)

    def translation_changed(self, obj: BaseModel) -> None:
        self.update_view()

    @staticmethod
    def get_idx(idx: int, obj: BaseModel) -> Vector3:
        if idx == 0:
            return obj.position

        if isinstance(obj, Model3D):
            if idx == 1:
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
