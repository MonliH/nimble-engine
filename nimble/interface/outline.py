from typing import Optional
from PyQt5.QtWidgets import QListView, QWidget
from PyQt5.QtCore import QItemSelection, pyqtSlot, QItemSelectionModel

from nimble.objects.model import Model
from nimble.objects.scene import SceneObserver
from nimble.objects.project import current_project


class OutlineWidget(QListView, SceneObserver):
    def __init__(self, parent: QWidget = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setModel(current_project.scene)
        self.selection_model = self.selectionModel()
        self.selection_model.selectionChanged.connect(self.on_selection_changed)
        self.setAlternatingRowColors(True)
        current_project.scene.register_observer(self)

    @pyqtSlot(QItemSelection, QItemSelection)
    def on_selection_changed(self, selected, deselected):
        if selected.indexes():
            current_project.scene.set_active(selected.indexes()[0].row())

    def select_changed(self, idx: int, obj: Optional[Model]):
        if idx >= 0:
            self.selection_model.setCurrentIndex(
                self.model().index(idx), QItemSelectionModel.ClearAndSelect
            )
        else:
            # Item deselected
            self.selection_model.clearSelection()
