import importlib
import os

# Code to deal with pyinstaller splash screen
if "_PYIBoot_SPLASH" in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash

    pyi_splash.close()

import faulthandler
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QApplication
import sys
from nimble.window import MainWindow

import ctypes

app_id = u"jonathan.li.nimble.main"

try:
    # This is to show the nimble icon properly in the taskbar
    # see https://stackoverflow.com/a/1552105/9470078 for more
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
except AttributeError:
    # Not running on windows
    pass


def start():
    faulthandler.enable()  # Enable faulthandler for debugging

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    # Create and show the window maximized
    window = MainWindow()
    window.showMaximized()

    os._exit(app.exec_())


if __name__ == "__main__":
    start()
