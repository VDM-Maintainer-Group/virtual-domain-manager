#!/usr/bin/env python3
# fix relative path import
import sys
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
from pyvdm.core.manager import CoreManager
from pyQt5.QtCore import (Qt, QSize)
from pyQt5.QtWidgets import (QSystemTrayIcon, QIcon)

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon( QIcon('../assets/VD_icon.png') )
        self.setContextMenu( self.ContextMenuEvent )
        pass
    
    def ContextMenuEvent(self):
        pass

    pass

if __name__ == '__main__':
    # ignore interrupt signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    app = QApplication(sys.argv)
    sys.exit(app.exec_())
    pass
