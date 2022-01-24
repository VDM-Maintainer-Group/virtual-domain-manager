#!/usr/bin/env python3
# fix relative path import
import sys, signal, socket
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import pkg_resources
from TransitionSceneWidget import TransitionSceneWidget
from pyvdm.core.manager import CoreManager
from PyQt5.QtCore import (QObject, QThread, Qt, QSize, QUrl,
                QTimer, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QIcon, )
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu)
from PyQt5.QtMultimedia import (QAudioDeviceInfo, QSoundEffect)

global app
ASSETS = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/'+_)

SE_MAP = {
    'save': ASSETS('SE-Save-SagradaReset.wav'),
    'close': ASSETS('SE-Close-SagradaReset.wav'),
}

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
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    play_signal  = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cm = CoreManager()
        self.dm = self.cm.dm
        self.w_ts = TransitionSceneWidget()
        self.start_signal.connect( self.w_ts.start )
        self.stop_signal.connect( self.w_ts.stop )
        self.play_signal.connect(self.playSoundEffect)
        #
        _open_domain = self.getCurrentDomain('')
        if _open_domain: #for abnormal exit
            self.cm.open_domain(_open_domain)
        #
        self.setIcon( QIcon(ASSETS('VD_icon.png')) )
        #
        self.setContextMenu( self.getDefaultMenu() )
        self.show()
        pass
    
    @pyqtSlot(str)
    def playSoundEffect(self, type:str):
        _url = QUrl.fromLocalFile( SE_MAP[type] )
        se = QSoundEffect( self )
        se.setSource(_url)
        se.play()
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
        self.act_save = menu.addAction('Save')
        self.act_save.triggered.connect(self.save_domain)
        self.act_close = menu.addAction('Close')
        self.act_close.triggered.connect(self.close_domain)
        #
        self.switch_menu = menu.addMenu('Switch') #leave empty for default
        self.switch_menu.triggered.connect( self.switch_domain )
        self.switch_menu.aboutToShow.connect( self.onShow )
        self.switch_menu.aboutToHide.connect( self.onHide )
        self.updateSwitchMenu()
        self.update_timer = None
        #
        menu.addSeparator()
        # add 'quit' act
        act_quit = menu.addAction('Quit')
        act_quit.triggered.connect(self.quit)
        #
        return menu

    @pyqtSlot()
    def onShow(self):
        if self.update_timer:
            self.update_timer.stop()

    @pyqtSlot()
    def onHide(self):
        self.update_timer = QTimer.singleShot(300, self.updateSwitchMenu)

    @pyqtSlot()
    def updateSwitchMenu(self):
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
            self.play_signal.emit('save')
        pass

    def close_domain(self, e=None):
        self.play_signal.emit('close')
        ret = self.cm.close_domain()
        if ret is not True:
            print(ret)
            print('Save... shi te na i.')
        else:
            self.title_bar.setText( self.getCurrentDomain() ) #expect "<None>"
            self.act_save.setEnabled(False)
            self.act_close.setEnabled(False)
        pass

    def switch_domain(self, e):
        _name = e.text() if hasattr(e, 'text') else e
        # play transition animation on new threads (with sound effect)
        self.start_signal.emit()
        # self.worker = MFWorker(self.w_ts.start)
        # self.worker.run()
        #
        ret = self.cm.switch_domain(_name)
        if ret is True:
            self.title_bar.setText( self.getCurrentDomain() ) #expect not "<None>"
            self.act_save.setEnabled(True)
            self.act_close.setEnabled(True)
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
