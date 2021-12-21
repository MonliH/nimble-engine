from PySide2.QtCore import QCoreApplication, Qt
from PySide2.QtWidgets import QApplication
import sys
from window import MainWindow

QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
app = QApplication(sys.argv)
wnd = MainWindow()
sys.exit(app.exec_())
