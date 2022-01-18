import faulthandler
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QApplication
import sys
from nimble.window import MainWindow

faulthandler.enable()

QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
app = QApplication(sys.argv)
wnd = MainWindow()
sys.exit(app.exec_())
