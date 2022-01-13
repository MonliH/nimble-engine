from PyQt5.QtWidgets import QDialog, QFileDialog

from nimble.common.resources import load_ui


class SaveProjectAs(QDialog):
    def __init__(self, parent=None, new_project=False):
        super().__init__(parent)
        load_ui(":/ui/save_project_as.ui", self)

        if new_project:
            self.title.setText("Create a New Project")
            self.create.setText("Create!")

        self.browse_file.clicked.connect(self.browse_file_path)
        self.filename_editor.textChanged.connect(self.check_line)
        self.project_name.textChanged.connect(self.check_line)
        self.create.clicked.connect(self.created)
        self.create.setEnabled(False)

    def created(self):
        self.accept()

    def check_line(self):
        ok = self.filename_editor.text() != "" and self.project_name.text() != ""
        self.create.setEnabled(ok)

    def browse_file_path(self):
        fname = QFileDialog.getExistingDirectory(
            self,
            "Open folder",
            ".",
            options=QFileDialog.DontUseNativeDialog,
        )
        self.filename_editor.setText(fname)
