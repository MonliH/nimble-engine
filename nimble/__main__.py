from PySide2.QtCore import QCoreApplication, Qt
from PySide2.QtWidgets import QApplication
import sys
from nimble.window import MainWindow

QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
app = QApplication(sys.argv)
wnd = MainWindow()
sys.exit(app.exec_())
