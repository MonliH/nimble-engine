import importlib

if "_PYIBoot_SPLASH" in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash

    pyi_splash.close()

import os
import faulthandler
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QApplication
import sys
from nimble.window import MainWindow


def start():
    faulthandler.enable()

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    MainWindow()
    os._exit(app.exec_())


if __name__ == "__main__":
    start()
