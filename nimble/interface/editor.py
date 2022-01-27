from typing import Callable
from PyQt5.QtGui import QFont, QFontMetrics, QColor, QFontDatabase, QKeySequence, QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QMenuBar, QWidget, QShortcut, QMainWindow
from pathlib import Path
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from nimble.common import current_project


class EditorWidget(QsciScintilla):
    def __init__(self, initial: str, parent=None):
        super(EditorWidget, self).__init__(parent)
        self.setText(initial)

        font_id = QFontDatabase().addApplicationFont(":/fonts/FiraCode-Regular.ttf")
        family = QFontDatabase().applicationFontFamilies(font_id)[0]
        font = QFont(family)
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)
        self.setMarginsFont(font)

        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("0000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#ebebeb"))

        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setCaretWidth(2)

        self.setTabWidth(4)
        self.setIndentationsUseTabs(True)
        self.setUtf8(True)

        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        self.setLexer(lexer)
        self.SendScintilla(
            QsciScintilla.SCI_STYLESETFONT, 1, bytes("Fira Code", "utf8")
        )


class EditorInner(QWidget):
    def __init__(
        self,
        filename: str,
        save: Callable[[], None],
        on_change: Callable[[], None],
        parent=None,
    ):
        super().__init__(parent)

        self.filename = filename
        self.box_layout = QVBoxLayout(self)

        self.menu_bar = QMenuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        self.save_action = self.file_menu.addAction("Save")
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self, save, save)
        shortcut.activated.connect(save)
        shortcut.activatedAmbiguously.connect(save)

        self.save_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.save_action.triggered.connect(save)
        self.addAction(self.save_action)

        self.box_layout.setMenuBar(self.menu_bar)
        self.box_layout.setContentsMargins(0, 0, 0, 0)
        with open(filename, "r") as f:
            initial_contents = f.read()

        self.editor = EditorWidget(initial_contents)
        self.editor.textChanged.connect(on_change)

        self.box_layout.addWidget(self.editor)


class Editor(QMainWindow):
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.saved = True

        self.editor = EditorInner(filename, self.save, self.on_change)
        self.setCentralWidget(self.editor)
        self.update_title()
        self.setWindowIcon(QIcon(":/img/logo.png"))

        self.resize(650, 650)

    def title_text(self):
        return f"Text Editor ({Path(self.filename).relative_to(current_project.folder)}){' *' if not self.saved else ''}"

    def update_title(self):
        new_title = self.title_text()
        self.setWindowTitle(new_title)

    def on_change(self):
        prev = self.saved
        self.saved = False

        if prev:
            self.update_title()

    def save(self):
        content = self.editor.editor.text()
        with open(self.filename, "w") as f:
            f.write(content)

        prev = self.saved
        self.saved = True

        if not prev:
            self.update_title()
