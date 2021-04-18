#!/usr/bin/env python3
# fix relative path import
import sys, signal, socket
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import pkg_resources
from TransitionSceneWidget import TransitionSceneWidget
from pyvdm.core.manager import CoreManager
from PyQt5.QtCore import (QObject, QThread, Qt, QSize, QUrl, pyqtSignal)
from PyQt5.QtGui import (QIcon, )
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu)
from PyQt5.QtMultimedia import QSoundEffect

global app
ASSETS = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/'+_)

class MFWorker(QObject):
    def __init__(self, func, args=None):
        super().__init__(None)
        self.func = func
        self.args = args
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.run)
        pass

    def isRunning(self):
        return self.thread.isRunning()

    def start(self):
        self.thread.start()
        pass
    
    def terminate(self):
        self.thread.exit(0)
        pass

    def run(self):
        if self.args:
            self.func(*self.args)
        else:
            self.func()
        self.thread.exit(0)
        pass
    pass

class TrayIcon(QSystemTrayIcon):
    stop_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cm = CoreManager()
        self.dm = self.cm.dm
        self.w_ts = TransitionSceneWidget()
        self.stop_signal.connect(self.w_ts.stop)
        #
        _open_domain = self.getCurrentDomain('')
        if _open_domain: #for abnormal exit
            self.cm.open_domain(_open_domain)
        #
        self.setIcon( QIcon(ASSETS('VD_icon.png')) )
        self.loadSoundEffect()
        #
        self.setContextMenu( self.getDefaultMenu() )
        self.show()
        pass
    
    def loadSoundEffect(self):
        try:
            self.se_save = QSoundEffect()
            self.se_save.setSource( QUrl.fromLocalFile(ASSETS('SE-Save-SagradaReset.wav')) )
            self.se_save.setVolume(0.25)
        except:
            self.se_save = None
        try:
            self.se_close = QSoundEffect()
            self.se_close.setSource( QUrl.fromLocalFile(ASSETS('SE-Close-SagradaReset.wav')) )
            self.se_close.setVolume(0.25)
        except:
            self.se_close = None
        pass

    def playTransitionScene():
        pass

    def getCurrentDomain(self, default='<None>'):
        _name = self.cm.stat.getStat()
        _name = default if not _name else _name
        return _name

    def getDefaultMenu(self):
        menu = QMenu()
        # set title bar
        _name = self.getCurrentDomain()
        self.title_bar = menu.addAction(_name)
        self.title_bar.setEnabled(False)
        menu.addSeparator()
        # add 'save', 'close' and 'switch' acts
        act_save = menu.addAction('Save Current Domain')
        act_save.triggered.connect(self.save_domain)
        act_close = menu.addAction('Close Current Domain')
        act_close.triggered.connect(self.close_domain)
        self.switch_menu = menu.addMenu('Switch to') #leave empty for default
        self.switch_menu.aboutToShow.connect( self.onActivation )
        self.switch_menu.triggered.connect( self.switch_domain )
        menu.addSeparator()
        # add 'quit' act
        act_quit = menu.addAction('Quit')
        act_quit.triggered.connect(self.quit)
        #
        return menu

    def onActivation(self):
        _open_name = self.getCurrentDomain()
        self.title_bar.setText( _open_name )
        #
        self.switch_menu.clear()
        _domains = list( self.dm.list_domain().keys() )
        for _name in _domains:
            act_name = self.switch_menu.addAction(_name)
            # act_name.triggered.connect(self.switch_domain)
            if _name==_open_name:
                act_name.setEnabled(False)
        pass

    #---------- wrap of CoreManager operations ----------#
    def save_domain(self, e=None):
        ret = self.cm.save_domain()
        if ret is not True:
            print(ret)
        else:
            self.se_save.play()
        pass

    def close_domain(self, e=None):
        self.se_close.play()
        ret = self.cm.close_domain()
        if ret is not True:
            print(ret)
            print('... save shi te na i.')
        else:
            self.title_bar.setText( self.getCurrentDomain() )
        pass

    def switch_domain(self, e):
        _name = e.text() if hasattr(e, 'text') else e
        # play transition animation on new threads (with sound effect)
        self.worker = MFWorker(self.w_ts.start)
        self.worker.run()
        #
        ret = self.cm.switch_domain(_name)
        if ret is True:
            self.title_bar.setText( self.getCurrentDomain() )
        else:
            print(ret)
        # end animation playing (with sound effect)
        self.stop_signal.emit()
        pass

    def quit(self, e):
        self.close_domain()
        app.exit()
        pass

    pass

def main():
    global app
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

if __name__ == '__main__':
    main()
