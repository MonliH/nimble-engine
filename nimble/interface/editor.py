from PyQt5.QtGui import QFont, QFontMetrics, QColor, QFontDatabase
from PyQt5.Qsci import QsciScintilla, QsciLexerPython


class Editor(QsciScintilla):
    def __init__(self, parent=None):
        super(Editor, self).__init__(parent)

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
        self.setMarginsBackgroundColor(QColor("#cccccc"))

        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setCaretWidth(2)

        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(True)

        self.setWrapMode(QsciScintilla.WrapWord)
        self.setWrapVisualFlags(QsciScintilla.WrapFlagByBorder)

        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        self.setLexer(lexer)
        self.SendScintilla(
            QsciScintilla.SCI_STYLESETFONT, 1, bytes("Fira Code", "utf8")
        )

        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        self.setMinimumSize(600, 450)
