#!/usr/bin/env python3
import sys
import pkg_resources
from PyQt5.QtCore import (Qt, QRect, QSize)
from PyQt5.QtGui import (QIcon, QMovie)
from PyQt5.QtWidgets import (QApplication, QWidget, QDesktopWidget, QLabel,
                        QLayout, QGridLayout, QPlainTextEdit, QSizePolicy)

ASSETS = lambda _: pkg_resources.resource_filename(__name__, _)

class TransitionSceneWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Dialog)
        pass

    pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w_ts = TransitionSceneWidget()
    sys.exit(app.exec_())
