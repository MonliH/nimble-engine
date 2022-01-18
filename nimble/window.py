from typing import cast
from PyQt5.QtGui import QFont, QFontDatabase
import moderngl_window as mglw
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QDialog, QWidget
from PyQt5.QtCore import QSettings, Qt
from PyQtAds.QtAds import ads
from nimble.interface.editor import Editor

import nimble.resources.resources
from nimble.common.resources import load_ui
from nimble.interface.entity_inspector import EntityInspector
from nimble.interface.file_explorer import FileExplorer
from nimble.interface.outline import OutlineWidget
from nimble.interface.project_ui import OpenProject, OverwriteWarning, SaveProjectAs
from nimble.interface.viewport import ViewportWidget
from nimble.objects.project import ProjectObserver, current_project
from nimble.objects.scene import Scene


class MainWindow(QMainWindow, ProjectObserver):
    def __init__(self, parent=None):
        super().__init__(parent)
        current_project.add_observer("main_window", self)
        font_id = QFontDatabase().addApplicationFont(":/fonts/OpenSans-Regular.ttf")
        family = QFontDatabase().applicationFontFamilies(font_id)[0]
        QApplication.setFont(QFont(family))

        self.setWindowState(Qt.WindowMaximized)
        self.show()
        self.setWindowTitle("Nimble Engine")

        load_ui(":/ui/main_window.ui", self)
        self.actionNew.triggered.connect(self.new_project)

        self.dock_manager = ads.CDockManager(self)

        self.viewport_dock = ads.CDockWidget("Scene Viewer")
        self.dock_manager.addDockWidget(ads.RightDockWidgetArea, self.viewport_dock)
        self.viewport = ViewportWidget(
            self.viewport_dock,
            on_gl_init=self.init_viewport,
        )
        self.viewport_dock.setWidget(self.viewport)

        self.outline_dock = ads.CDockWidget("Outline")
        self.dock_manager.addDockWidget(ads.LeftDockWidgetArea, self.outline_dock)
        self.outline = OutlineWidget(self.outline_dock)
        self.outline_dock.setWidget(self.outline)

        self.entity_dock = ads.CDockWidget("Entity Inspector")
        self.dock_manager.addDockWidget(ads.RightDockWidgetArea, self.entity_dock)
        self.entity = EntityInspector()
        self.entity_dock.setWidget(self.entity)

        self.file_explorer_dock = ads.CDockWidget("File Explorer")
        self.file_explorer = FileExplorer()
        self.file_explorer_dock.setWidget(self.file_explorer)
        self.dock_manager.addDockWidget(
            ads.RightDockWidgetArea, self.file_explorer_dock
        )

        self.last_mouse_button = None

        self.shift = False
        self.did_drag = False
        self.open_context = None
        self.context_menu_pos = (0, 0)
        self._modifiers = mglw.context.base.KeyModifiers()

        self.actionSave_Layout.triggered.connect(self.save_perspectives)
        self.actionReset_Layout.triggered.connect(self.restore_perspectives)
        self.actionOpen.triggered.connect(self.open_project)

        self.actionSave.triggered.connect(self.save_project)

        self.menuWindow = cast(QMenu, self.menuWindow)
        self.menuWindow.addAction(self.viewport_dock.toggleViewAction())
        self.menuWindow.addAction(self.outline_dock.toggleViewAction())
        self.menuWindow.addAction(self.entity_dock.toggleViewAction())
        self.menuWindow.addAction(self.file_explorer_dock.toggleViewAction())

        self.restore_perspectives()
        self.project_changed()

        text_dock = ads.CDockWidget("Text Editor")
        text_dock.setWidget(self.create_code_editor())
        self.dock_manager.addDockWidgetFloating(text_dock)

    def create_code_editor(self) -> QWidget:
        editor = Editor()
        return editor

    def project_changed(self):
        self.setWindowTitle(current_project.get_project_display_name())

    def init_viewport(self):
        current_project.scene.replace(Scene.default_scene())

    def closeEvent(self, event):
        event.accept()

    def save_perspectives(self):
        settings = QSettings("UserPrefs.ini", QSettings.IniFormat)
        self.dock_manager.addPerspective("default")
        self.dock_manager.savePerspectives(settings)

    def restore_perspectives(self):
        settings = QSettings("UserPrefs.ini", QSettings.IniFormat)
        self.dock_manager.loadPerspectives(settings)
        self.dock_manager.openPerspective("default")

    def new_project(self):
        overwrite = OverwriteWarning(self)
        res = overwrite.exec()
        if res == QDialog.Accepted:
            dialog = SaveProjectAs(self, new_project=True)
            res = dialog.exec()
            if res == QDialog.Accepted:
                current_project.new_project(dialog.folder, dialog.name)

    def open_project(self):
        overwrite = OverwriteWarning(self)
        res = overwrite.exec()
        if res == QDialog.Accepted:
            dialog = OpenProject(self)
            res = dialog.exec()
            if res == QDialog.Accepted:
                current_project.load_project(dialog.filename)

    def save_project_as(self):
        dialog = SaveProjectAs(self)
        res = dialog.exec()
        if res == QDialog.Accepted:
            current_project.set_project_name(dialog.folder, dialog.name)
            current_project.save_project()
            current_project.save_scene()

    def save_project(self):
        if not current_project.saved_project_is_open():
            self.save_project_as()
        else:
            current_project.save_scene()
