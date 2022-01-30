#!/usr/bin/env python3
from pyvdm.core.manager import CoreManager
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QTabWidget,
                    QDesktopWidget, QLayout, QGridLayout)
from PyQt5.QtMultimedia import (QAudioDeviceInfo, QSoundEffect)

class MainTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        pass
    pass

class DMTabWidget(QWidget):
    def __init__(self, parent, dm):
        super().__init__(parent)
        self.parent = parent
        self.dm = dm
        pass
    pass

class CMTabWidget(QWidget):
    def __init__(self, parent, cm):
        super().__init__(parent)
        self.parent = parent
        self.cm = cm
        pass
    pass

class PMTabWidget(QWidget):
    def __init__(self, parent, pm):
        super().__init__(parent)
        self.parent = parent
        self.pm = pm
        pass
    pass

class ControlPanelClass(QWidget):
    def __init__(self, parent=None, core=None):
        super().__init__(parent)
        self.core = core if core else CoreManager()
        #
        self.styleHelper()
        pass

    def styleHelper(self):
        pass

    pass

if __name__== '__main__':
    pass