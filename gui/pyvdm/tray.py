#!/usr/bin/env python3
# fix relative path import
import sys, signal, socket
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
from pyvdm.core.manager import CoreManager
from PyQt5.QtCore import (Qt, QSize)
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QIcon, QMenu)

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cm = CoreManager()
        self.dm = self.cm.dm
        #
        self.setIcon( QIcon('../assets/VD_icon.png') )
        self.setContextMenu( self.getDefaultMenu() )
        self.activated.connect( self.onActivation )
        pass
    
    def getCurrentDomain(self, default='<None>'):
        _name = self.cm.stat.getStat()
        _name = default if not _name else _name
        return _name

    def getDefaultMenu(self):
        menu = QMenu()
        # set title bar
        _name = self.getCurrentDomain()
        self.title_bar = self.menu.addAction(_name)
        self.title_bar.setEnabled(False)
        menu.addSeparator()
        # add 'save', 'close' and 'switch' acts
        act_save = menu.addAction('Save Current Domain')
        act_save.triggered.connect(self.save_domain)
        act_close = menu.addAction('Close Current Domain')
        act_close.triggered.connect(self.close_domain)
        self.switch_menu = menu.addMenu('Switch to') #leave empty for default
        menu.addSeparator()
        # add 'quit' act
        act_quit = menu.addAction('Quit')
        act_quit.triggered.connect(self.quit)
        #
        return menu

    def onActivation(self, reason):
        if reason==QSystemTrayIcon.DoubleClick:
            return
        #
        _open_name = self.getCurrentDomain('<None>')
        self.title_bar.setText( _open_name )
        #
        self.switch_menu.clear()
        _domains = list( self.dm.list_domain().keys() )
        for _name in _domains:
            act_name = self.switch_menu.addAction(_name)
            act_name.triggered.connect(self.switch_domain)
        pass

    def save_domain(self, e=None):
        self.cm.save_domain()
        pass

    def close_domain(self, e=None):
        self.cm.close_domain()
        pass

    def switch_domain(self, e):
        _name = e.text if hasattr(e, 'text') else e
        self.cm.switch_domain(_name)
        pass

    def quit(self, e):
        self.close_domain()
        app.exit()
        pass

    pass

if __name__ == '__main__':
    # singleton instance restriction
    try:
        mf_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mf_sock.bind(('', 52500))
    except:
        exit()
    # ignore interrupt signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    app = QApplication(sys.argv)
    tray = TrayIcon()
    sys.exit(app.exec_())
    pass
