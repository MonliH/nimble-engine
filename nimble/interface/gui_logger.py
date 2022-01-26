import traceback
from io import TextIOBase
from typing import Optional, cast
from PyQt5.QtWidgets import QPlainTextEdit, QWidget
import logging
import functools
import sys

from nimble.common.resources import load_ui


def with_gui_logging_default(default=None):
    def gui_decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            log = logging.getLogger("nimble")
            new_stderr = StreamToLogger(log, logging.ERROR)
            stdout = sys.stdout
            sys.stdout = StreamToLogger(log, logging.INFO)
            res = default
            try:
                res = fn(*args, **kwargs)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__, file=new_stderr)
            sys.stdout = stdout

            return res

        return wrapper

    return gui_decorator


with_gui_logging = with_gui_logging_default()


class StreamToLogger(TextIOBase):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


class GuiLogger(QWidget, logging.Handler):
    def __init__(self, parent: Optional[QWidget] = None):
        super(QWidget, self).__init__(parent)
        super(logging.Handler, self).__init__()

        load_ui(":/ui/gui_logger.ui", self)
        self.text = cast(QPlainTextEdit, self.text)
        self.text.setReadOnly(True)
        self.clear.clicked.connect(self.clear_text)

    def clear_text(self):
        self.text.clear()

    def emit(self, record):
        msg = self.format(record)
        self.text.appendPlainText(msg)
