import logging
from pathlib import Path
from typing import List, cast

import moderngl_window as mglw
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMenu, QAction
from PyQtAds.QtAds import ads

import nimble.resources.resources  # Note: This is needed to load the qt resources. (don't remove this seemingly unused import!)
from nimble.common import ProjectObserver, current_project
from nimble.common.resources import load_ui
from nimble.interface.entity_inspector import EntityInspector
from nimble.interface.file_explorer import FileExplorer
from nimble.interface.gui_logger import GuiLogger
from nimble.interface.outline import OutlineWidget
from nimble.interface.project_ui import OpenProject, OverwriteWarning, SaveProjectAs
from nimble.interface.run_window import RunWindow
from nimble.interface.viewport import ViewportWidget
from nimble.objects import Scene


class MainWindow(QMainWindow, ProjectObserver):
    MaxRecentProjects = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        current_project.add_observer("main_window", self)
        font_id = QFontDatabase().addApplicationFont(":/fonts/OpenSans-Regular.ttf")
        family = QFontDatabase().applicationFontFamilies(font_id)[0]
        QApplication.setFont(QFont(family))
        self.settings = QSettings("jonathan_li", "nimble")

        load_ui(":/ui/main_window.ui", self)
        self.actionNew.triggered.connect(self.new_project)
        self.setWindowIcon(QIcon(":/img/logo.png"))

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

        self.actionSave.setShortcutContext(Qt.WindowShortcut)
        self.addAction(self.actionSave)
        self.actionSave.triggered.connect(self.save_project)

        self.actionCopy.triggered.connect(current_project.copy)
        self.actionPaste.triggered.connect(current_project.paste)

        self.play = ads.CDockWidget("Play")
        self.play.setWidget(RunWindow())
        self.dock_manager.addDockWidget(ads.BottomDockWidgetArea, self.play)

        logTextBox = GuiLogger(self)
        logTextBox.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logging.getLogger("nimble").addHandler(logTextBox)
        logging.getLogger("nimble").setLevel(logging.DEBUG)

        self.log = ads.CDockWidget("Log")
        self.log.setWidget(logTextBox)
        self.dock_manager.addDockWidget(ads.BottomDockWidgetArea, self.log)

        self.menuWindow = cast(QMenu, self.menuWindow)
        self.menuWindow.addAction(self.viewport_dock.toggleViewAction())
        self.menuWindow.addAction(self.outline_dock.toggleViewAction())
        self.menuWindow.addAction(self.entity_dock.toggleViewAction())
        self.menuWindow.addAction(self.file_explorer_dock.toggleViewAction())
        self.menuWindow.addAction(self.play.toggleViewAction())
        self.menuWindow.addAction(self.log.toggleViewAction())

        self.restore_perspectives()
        self.project_changed()

        self.menuOpen_Recent = cast(QMenu, self.menuOpen_Recent)
        self.recent_project_actions: List[QAction] = []
        for _ in range(self.MaxRecentProjects):
            action = QAction()
            self.recent_project_actions.append(action)
            self.menuOpen_Recent.addAction(action)
            action.triggered.connect(self.open_recent_project)

        self.update_recent_projects()

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
        settings = QSettings(":/default_prefs.ini", QSettings.IniFormat)
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
                self.add_recent_project(current_project.project_file)

    def open_project(self):
        overwrite = OverwriteWarning(self)
        res = overwrite.exec()
        if res == QDialog.Accepted:
            dialog = OpenProject(self)
            res = dialog.exec()
            if res == QDialog.Accepted:
                current_project.load_project(dialog.filename)
                self.add_recent_project(current_project.project_file)

    def save_project_as(self):
        dialog = SaveProjectAs(self)
        res = dialog.exec()
        if res == QDialog.Accepted:
            current_project.copy_assets(dialog.folder, dialog.name)
            current_project.set_project_name(dialog.folder, dialog.name)
            current_project.save_project()
            current_project.save_scene()
            self.add_recent_project(current_project.project_file)

    def save_project(self):
        if not current_project.saved_project_is_open():
            self.save_project_as()
        else:
            current_project.save_scene()

        self.add_recent_project(current_project.project_file)

    def add_recent_project(self, path: Path):
        recent_projects = self.settings.value("recent_projects", [], "QStringList")
        path_str = str(path)
        if path_str in recent_projects:
            recent_projects.remove(path_str)

        recent_projects.insert(0, path_str)
        del recent_projects[MainWindow.MaxRecentProjects :]

        self.settings.setValue("recent_projects", recent_projects)
        self.update_recent_projects()

    def update_recent_projects(self):
        deleted_projects = []
        recent_projects = self.settings.value("recent_projects", [], "QStringList")
        for i, project in enumerate(recent_projects):
            if not Path(project).exists():
                deleted_projects.append(i)

        deleted_projects.reverse()
        for to_del in deleted_projects:
            del recent_projects[to_del]

        self.settings.setValue("recent_projects", recent_projects)

        current_recent_files = min(len(recent_projects), MainWindow.MaxRecentProjects)
        for i in range(current_recent_files):
            path = Path(recent_projects[i])
            action = self.recent_project_actions[i]
            action.setText(path.parent.name)
            action.setData(path)
            action.setVisible(True)

        for i in range(current_recent_files, MainWindow.MaxRecentProjects):
            self.recent_project_actions[i].setVisible(False)

    def open_recent_project(self):
        action = self.sender()
        if action:
            path = action.data()
            if path:
                current_project.load_project(path)
                self.add_recent_project(current_project.project_file)
