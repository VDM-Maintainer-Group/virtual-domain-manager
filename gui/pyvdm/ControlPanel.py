#!/usr/bin/env python3
from utils import (ASSETS, CONFIG)
from pyvdm.core.manager import CoreManager
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QIcon, )
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QTabWidget,
                    QDesktopWidget, QLayout, QGridLayout)
from PyQt5.QtMultimedia import (QAudioDeviceInfo, QSoundEffect)

class MainTabWidget(QWidget):
    def __init__(self, parent, core):
        super().__init__(parent)
        self.parent = parent
        self.core = core
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

class ControlPanelWindow(QTabWidget):
    def __init__(self, parent=None, core=None):
        super().__init__(parent)
        self.core = core if core else CoreManager()
        #
        self.styleHelper()
        pass

    def styleHelper(self):
        self.addTabs()
        # move to desktop center
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move( qr.topLeft() )
        # set window style
        self.setAttribute( Qt.WA_InputMethodEnabled )
        self.setMinimumSize(600, 360)
        self.setWindowIcon( QIcon(CONFIG['ASSETS_ICON']) )
        self.setWindowTitle('PyVDM Control Panel')
        self.setVisible(False)
        pass

    def addTabs(self):
        self.main_tab = MainTabWidget(self, self.core)
        self.addTab(self.main_tab, "Dashboard")
        #
        self.dm_tab = DMTabWidget(self, self.core.dm)
        self.addTab(self.dm_tab, 'Domain Manager')
        #
        self.cm_tab = CMTabWidget(self, self.core.cm)
        self.addTab(self.cm_tab, 'Capability Manager')
        #
        self.pm_tab = PMTabWidget(self, self.core.pm)
        self.addTab(self.pm_tab, 'Plugin Manager')
        pass

    pass

if __name__== '__main__':
    import sys
    app = QApplication(sys.argv)
    main_window = ControlPanelWindow()
    main_window.show()
    sys.exit(app.exec_())