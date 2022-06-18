#!/usr/bin/env python3
# fix relative path import
import sys, signal, socket
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
from pyvdm.gui.utils import (CONFIG, MFWorker)
from ControlPanel import ControlPanelWindow
from TransitionSceneWidget import TransitionSceneWidget
from pyvdm.core.manager import CoreManager
from PyQt5.QtCore import (Qt, QSize, QUrl,
                QTimer, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QIcon, )
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtMultimedia import (QAudioDeviceInfo, QSoundEffect)

global app
NONE_DOMAIN = '<None>'

class TrayIcon(QSystemTrayIcon):
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    play_signal  = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cm = CoreManager()
        self.dm = self.cm.dm
        _open_name = self.getCurrentDomain()
        if _open_name: #for abnormal exit
            self.cm.open_domain(_open_name)
        #
        self.control_panel = ControlPanelWindow(self, self.cm)
        #
        self.w_ts = TransitionSceneWidget()
        self.start_signal.connect( self.w_ts.start )
        self.stop_signal.connect( self.w_ts.stop )
        self.play_signal.connect(self.playSoundEffect)
        #
        self.setContextMenu( self.getDefaultMenu() )
        self.updateTitleBar()
        self.setIcon( QIcon( CONFIG['ASSETS_ICON'] ) )
        #
        self.activated.connect( self.onActivation )
        self.show()
        pass

    def getCurrentDomain(self):
        _name = self.cm.stat.getStat()
        _name = None if not _name else _name
        return _name

    def getDefaultMenu(self):
        menu = QMenu()
        # set title bar and autosave act
        self.title_bar = menu.addAction(NONE_DOMAIN)
        self.title_bar.setEnabled(False)
        self.act_autosave = QAction('Autosave', self)
        self.act_autosave.setCheckable(True)
        menu.addAction( self.act_autosave )
        self.act_autosave.triggered.connect( self.onActAutosave )
        self.autosave_timer = None
        menu.addSeparator()

        # add 'save' and 'close' acts
        self.act_save = menu.addAction('Save')
        self.act_save.triggered.connect(self.save_domain)
        self.act_close = menu.addAction('Close')
        self.act_close.triggered.connect(self.close_domain)
        # and 'switch' submenu
        self.switch_menu = menu.addMenu('Switch') #leave empty for default
        self.switch_menu.triggered.connect( self.switch_domain )
        self.updateSwitchMenu()
        menu.addSeparator()

        # add 'quit' act
        act_open_panel = menu.addAction('Open Control Panel')
        act_open_panel.triggered.connect( lambda: self.control_panel.show() )
        act_quit = menu.addAction('Quit')
        act_quit.triggered.connect(self.quit)

        menu.aboutToShow.connect( self.updateSwitchMenu )
        return menu

    def updateTitleBar(self):
        _open_name = self.getCurrentDomain()
        if _open_name:
            self.title_bar.setText( _open_name )
            self.act_autosave.setEnabled(True)
            self.act_save.setEnabled(True)
            self.act_close.setEnabled(True)
            self.act_autosave.setChecked( CONFIG['AUTOSAVE']=='True' )
        else:
            self.title_bar.setText( NONE_DOMAIN )
            self.act_autosave.setEnabled(False)
            self.act_save.setEnabled(False)
            self.act_close.setEnabled(False)
        return _open_name

    @pyqtSlot(str)
    def playSoundEffect(self, _file):
        _url = QUrl.fromLocalFile(_file)
        se = QSoundEffect( self )
        se.setSource(_url)
        se.play()
        pass

    @pyqtSlot()
    def updateSwitchMenu(self):
        _open_name = self.updateTitleBar()
        #
        self.switch_menu.clear()
        _domains = list( self.dm.list_domain().keys() )
        for _name in _domains:
            act_name = self.switch_menu.addAction(_name)
            if _name==_open_name:
                act_name.setEnabled(False)
        pass

    @pyqtSlot()
    def onActAutosave(self):
        _checked = self.act_autosave.isChecked()
        CONFIG['AUTOSAVE'] = "True" if _checked else "False"
        
        if not _checked:
            if self.autosave_timer: self.autosave_timer.stop()
            self.autosave_timer = None
        else:
            self.autosave_timer = QTimer(self)
            self.autosave_timer.timeout.connect(
                lambda: self.cm.save_domain()
            )
            self.autosave_timer.start(15*1000) #interval: 15s
        pass

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def onActivation(self, reason):
        if reason==QSystemTrayIcon.Trigger:
            self.control_panel.show()
            pass
        pass

    #---------- wrap of CoreManager operations ----------#
    def save_domain(self, e=None):
        ret = self.cm.save_domain()
        if ret is not True:
            print(ret)
        else:
            self.play_signal.emit( CONFIG['THEME_SE_SAVE'] )
        pass

    def close_domain(self, e=None):
        self.play_signal.emit( CONFIG['THEME_SE_CLOSE'] )
        ret = self.cm.close_domain()
        if ret is not True:
            print(ret)
            print('Save... shi te na i.')
        else:
            self.updateTitleBar()
        pass

    def switch_domain(self, e):
        def _switch_domain(name):
            self.start_signal.emit()
            ret = self.cm.switch_domain(name)
            if ret is True:
                self.updateTitleBar()
            else:
                print(ret)
            self.stop_signal.emit()
            pass
        
        _name = e.text() if hasattr(e, 'text') else e
        self.worker = MFWorker( _switch_domain, args=(_name,) )
        self.worker.start()
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
    QApplication.setAttribute( Qt.AA_EnableHighDpiScaling )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = TrayIcon()
    sys.exit(app.exec_())
    pass

if __name__ == '__main__':
    main()
