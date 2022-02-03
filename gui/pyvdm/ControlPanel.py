#!/usr/bin/env python3
from utils import (ASSETS, CONFIG, POSIX, MFWorker)
from pathlib import Path
import json, time
from datetime import datetime
from urllib import request as url_request
from pyvdm.core.errcode import (CapabilityCode, )
from pyvdm.core.manager import CoreManager
from PyQt5.QtCore import (Qt, QThread, QUrl, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QIcon, )
from PyQt5.QtWidgets import (QApplication, QTabWidget, QDesktopWidget, QAbstractItemView, QHeaderView,
            QWidget, QGroupBox,  QPushButton, QLabel, QDialog, QFileDialog, QMessageBox, QComboBox, QLineEdit)
from PyQt5.QtWidgets import (QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, )
from PyQt5.QtWidgets import ( QGridLayout, QFormLayout, QHBoxLayout, QVBoxLayout, )
from PyQt5.QtMultimedia import (QAudioDeviceInfo, QSoundEffect)

class MainTabWidget(QWidget):
    def __init__(self, parent, core):
        super().__init__(parent)
        self.parent = parent
        self.core = core
        pass
    pass

class InformationArea(QTableWidget):
    send_signal = pyqtSignal(str)

    def __init__(self, parent, loader, header, slots=None, entry=0):
        super().__init__(parent)
        self.loader = loader
        self.header = header
        self.length = len(header)
        self.slots = slots
        self.entry = entry
        #
        self.status = dict()
        self.styleHelper()
        self.refresh()
        self.itemChanged.connect( self.onItemChanged )
        self.itemClicked.connect( self.onItemClicked )
        self.itemDoubleClicked.connect( self.onItemDoubleClicked )
        self.itemSelectionChanged.connect( self.onItemSelectionChanged )
        pass

    def styleHelper(self):
        _header = [x if x[0] not in ['<','['] else '' for x in self.header]
        self.setColumnCount( self.length )
        self.setHorizontalHeaderLabels( _header )
        #
        for i,x in enumerate(self.header):
            if i==self.entry or x[0] in ['<','[']:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
            else:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)
        if self.length == 1:
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        #
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        pass

    def refresh(self):
        self.setRowCount(0)

        self.raw_items = self.loader()
        for _row,(key,value) in enumerate( self.raw_items ):
            self.insertRow( _row )
            for j in range(self.length):
                if j==self.entry:
                    _item = QTableWidgetItem(key)
                    self.setItem(_row, j, _item)
                elif self.header[j][0] == '<':
                    _title = self.header[j].strip('<>')
                    _button = QPushButton(_title)
                    _button.setObjectName(key)
                    _button.clicked.connect( self.onButtonClicked )
                    self.setCellWidget(_row, j, _button)
                elif self.header[j][0] == '[':
                    _key = self.header[j].strip('[]')
                    _item = QTableWidgetItem( value[_key] )
                    if 'status' in value:
                        _status = value['status']
                    else:
                        _status = 'Capable'
                    if _status in ['Capable', 'Incapable']:
                        _item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                        _checked = Qt.Checked if _status in ['Capable'] else Qt.Unchecked
                        _item.setCheckState( _checked )
                        _item.setData(Qt.UserRole, _key)
                        self.status.update({ value[_key]:_checked })
                    self.setItem(_row, j, _item)
                else:
                    _item = value[ self.header[j] ]
                    _item = str(_item) if _item is not str else _item
                    _item = QTableWidgetItem( _item )
                    self.setItem(_row, j, _item)
            pass
        pass

    def select(self, name, col=-1):
        if col==-1: col = self.entry
        # _keys = list(zip( *list(self.info_box.raw_items) ))[0]
        # row = _keys.index(name)
        for row in range( self.rowCount() ):
            _title = self.item(row, col).text()
            if _title==name:
                return self.setCurrentCell(row, col)
        pass

    @pyqtSlot()
    def onButtonClicked(self):
        _btn = self.sender()
        _title = _btn.text()
        key = _btn.objectName()
        self.slots[_title](key)
        pass

    @pyqtSlot(QTableWidgetItem)
    def onItemChanged(self, item):
        _status = item.checkState()
        _name = item.text()
        if _name in self.status and _status!=self.status[_name]:
            _key  = item.data(Qt.UserRole)
            if self.slots[_key](_name):
                self.status[_name] = _status
            else:
                item.setCheckState( self.status[_name] )
        pass

    @pyqtSlot(QTableWidgetItem)
    def onItemClicked(self, item):
        if 'onItemClicked' in self.slots:
            self.slots['onItemClicked']( item.text() )
        pass

    @pyqtSlot(QTableWidgetItem)
    def onItemDoubleClicked(self, item):
        if 'onItemDoubleClicked' in self.slots:
            self.slots['onItemDoubleClicked']( item.text() )
        pass

    @pyqtSlot()
    def onItemSelectionChanged(self):
        if 'onItemSelectionChanged' in self.slots:
            self.slots['onItemSelectionChanged']()
        pass

    pass

class DetailsArea(QWidget):
    def __init__(self, parent, pm):
        super().__init__(parent)
        self.parent = parent
        self.pm = pm
        self.config = None
        #
        self.styleHelper()
        self.setVisible(False)
        pass

    def styleHelper(self):
        _name_layout = QHBoxLayout()
        _name_layout.addWidget( QLabel('Name:') )
        self.name = QLineEdit()
        _name_layout.addWidget(self.name)
        #
        self.created_time = QLabel()
        self.last_update_time = QLabel()
        self.info_box = InformationArea(self,
            loader = lambda: self.pm.list().items(),
            header = ['[name]', 'version'],
            slots  = {'name':self.checkPlugins, 'onItemDoubleClicked':self.jumpToPMTab},
            entry  = -1
        )
        #
        save_btn = QPushButton('Save')
        save_btn.clicked.connect( self.parent.updateDomain )
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect( self.cancelEdit )
        _btn_layout = QHBoxLayout()
        _btn_layout.addWidget(save_btn)
        _btn_layout.addWidget(cancel_btn)
        #
        layout = QFormLayout()
        layout.addRow( _name_layout )
        layout.addRow( self.created_time )
        layout.addRow( self.last_update_time )
        layout.addRow( self.info_box )
        layout.addRow( _btn_layout )
        self.setLayout( layout )
        pass

    def initDefaultConfig(self):
        self.config = None
        #
        self.name.setText('')
        _created_time = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        self.created_time.setText( f'Created Time\t: {_created_time}' )
        _last_update_time = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        self.last_update_time.setText( f'Last Update Time : {_last_update_time}' )
        #
        for idx in range( self.info_box.rowCount()  ):
            _item = self.info_box.item(idx, 0)
            _item.setCheckState( Qt.Checked )
        #
        self.setEnabled(True)
        self.setVisible(True)
        pass

    def loadFromConfig(self, config):
        self.config = config
        #
        self.name.setText( config['name'] )
        _created_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(config['created_time']))
        self.created_time.setText( f'Created Time\t: {_created_time}' )
        _last_update_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(config['last_update_time']))
        self.last_update_time.setText( f'Last Update Time : {_last_update_time}' )
        #
        for idx in range( self.info_box.rowCount()  ):
            _item = self.info_box.item(idx, 0)
            if _item.text() in config['plugins'].keys():
                _item.setCheckState( Qt.Checked )
            else:
                _item.setCheckState( Qt.Unchecked )
        #
        self.setEnabled(False)
        self.setVisible(True)
        pass

    def saveConfig(self):
        self.config = {}
        # domain name validation
        _name = self.name.text().strip()
        if not _name:
            QMessageBox.critical(self, "ERROR", "Name should not be empty.", QMessageBox.Ok)
            return False
        #
        self.config['name'] = _name
        _created_time = self.created_time.text().removeprefix('Created Time\t: ')
        _created_time = datetime.strptime(_created_time, '%Y-%m-%d %H:%M')
        self.config['created_time'] = _created_time.timestamp()
        self.config['last_update_time'] = time.time()
        self.config['plugins'] = dict()
        for idx in range( self.info_box.rowCount() ):
            _item = self.info_box.item(idx, 0)
            if _item.checkState()==Qt.Checked:
                _name = _item.text()
                _version = self.info_box.item(idx, 1).text()
                self.config['plugins'].update({ _name : _version })
        return True

    @pyqtSlot(str)
    def checkPlugins(self, name:str):
        return True

    @pyqtSlot()
    def cancelEdit(self):
        if self.config:
            self.loadFromConfig( self.config )
        else:
            self.setEnabled(False)
            self.setVisible(False)
        pass

    @pyqtSlot(str)
    def jumpToPMTab(self, name:str):
        _keys = list(zip( *list(self.info_box.raw_items) ))[0]
        if name in _keys:
            self.parent.parent.route(f'PMTab://{name}')
        pass

    pass

class DMTabWidget(QWidget):
    def __init__(self, parent, dm, pm):
        super().__init__(parent)
        self.parent = parent
        self.dm = dm
        self.pm = pm
        #
        self.styleHelper()
        pass

    def styleHelper(self):
        layout = QGridLayout()
        # add domain area (10x5)
        _box = QGroupBox('Domains')
        _sub_layout = QVBoxLayout()
        self.info_box = InformationArea(self,
            loader = lambda: self.dm.list_domain().items(),
            header = ['name'],
            slots  = {
                        'onItemDoubleClicked':self.editDetails,
                        'onItemSelectionChanged':self.showDetails}
        )
        _sub_layout.addWidget( self.info_box )
        ##
        _btn_layout = QGridLayout()
        self.add_button = QPushButton('Add ...');
        self.add_button.clicked.connect( self.addDomain )
        _btn_layout.addWidget( self.add_button, 0, 0, 1, 2 )
        self.edit_button = QPushButton('Edit'); self.edit_button.setVisible(False)
        self.edit_button.clicked.connect( self.editDetails )
        _btn_layout.addWidget( self.edit_button, 0, 0, 1, 1 )
        self.remove_button = QPushButton('Remove'); self.remove_button.setVisible(False)
        # self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect( self.removeDomain )
        _btn_layout.addWidget( self.remove_button, 0, 1, 1, 1 )
        _sub_layout.addLayout( _btn_layout )
        ##
        _box.setLayout( _sub_layout )
        layout.addWidget( _box, 0, 0, 10, 5 )
        # add detail area (10x5)
        _box = QGroupBox('Details')
        _sub_layout = QVBoxLayout()
        self.details = DetailsArea(self, self.pm)
        _sub_layout.addWidget( self.details )
        _box.setLayout( _sub_layout )
        layout.addWidget( _box, 0, 5, 10, 5 )
        #
        self.setLayout( layout )
        pass

    @pyqtSlot()
    def showDetails(self):
        _item = self.info_box.currentItem()
        if _item and _item.isSelected():
            _name = _item.text()
            _config = self.dm.list_domain(_name)[_name]
            self.details.loadFromConfig(_config)
            #
            self.add_button.setVisible(False)
            self.edit_button.setVisible(True)
            self.remove_button.setVisible(True)
        else:
            self.details.setVisible(False)
            #
            self.add_button.setVisible(True)
            self.edit_button.setVisible(False)
            self.remove_button.setVisible(False)
        pass

    @pyqtSlot()
    def editDetails(self, name=None):
        if not name:
            name = self.info_box.currentItem().text()
        self.details.setEnabled(True)
        pass

    @pyqtSlot()
    def addDomain(self):
        self.details.initDefaultConfig()
        pass

    @pyqtSlot()
    def removeDomain(self):
        name = self.info_box.currentItem().text()
        #
        confirm_box = QMessageBox()
        confirm_box.setText(f'Are you sure you want to remove domain "{name}"?')
        confirm_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_box.setDefaultButton(QMessageBox.No)
        if confirm_box.exec() != QMessageBox.Yes: return
        #
        ret = self.dm.delete_domain(name)
        if ret==True:
            self.info_box.refresh()
        else:
            QMessageBox.critical(self, "ERROR", ret.name, QMessageBox.Ok)
        pass

    @pyqtSlot()
    def updateDomain(self):
        if not self.details.config:     # new domain
            _func = self.dm.create_domain
        else:                           # update domain
            _func = self.dm.update_domain
        #
        if not self.details.saveConfig(): return
        _config = self.details.config
        ret = _func(_config['name'], _config)
        #
        if ret==True:
            self.info_box.refresh()
            self.info_box.select(_config['name'], col=0)
        else:
            if _func==self.dm.create_domain: self.details.config=None
            QMessageBox.critical(self, "ERROR", ret.name, QMessageBox.Ok)
        pass

    pass

class CMTabWidget(QWidget):
    def __init__(self, parent, cm):
        super().__init__(parent)
        self.parent = parent
        self.cm = cm
        #
        self.styleHelper()
        self.toggleDaemon()
        self.worker = MFWorker(self.fetchRemoteCapability)
        self.worker.run()
        pass

    def styleHelper(self):
        layout = QGridLayout()
        ## add capability information area (10x8)
        _box = QGroupBox('Capability')
        _sub_layout = QVBoxLayout()
        self.info_box = InformationArea(None,
            loader = lambda: self.cm.query().items(),
            header = ['[name]'],
            slots  = {'name':self.toggleCapability},
            entry  = -1
        )
        _sub_layout.addWidget( self.info_box )
        _box.setLayout( _sub_layout )
        layout.addWidget(_box, 0, 0, 10, 8)
        ## add daemon button area (2x2)
        _box = QGroupBox('Daemon')
        _sub_layout = QVBoxLayout()
        self.start_button = QPushButton('Start'); self.start_button.clicked.connect(self.toggleDaemon)
        self.stop_button  = QPushButton('Stop');  self.stop_button.clicked.connect(self.toggleDaemon)
        _sub_layout.addWidget( self.start_button )
        _sub_layout.addWidget( self.stop_button )
        _box.setLayout( _sub_layout )
        layout.addWidget( _box, 0, 8, 2, 2 )
        ## add install area (8x2)
        _box = QGroupBox('Candidates')
        _sub_layout = QVBoxLayout()
        self.cap_list = QListWidget()
        _sub_layout.addWidget( self.cap_list )
        self.install_button = QPushButton('Install')
        self.install_button.clicked.connect( self.installRemoteCapability )
        _sub_layout.addWidget( self.install_button )
        _box.setLayout( _sub_layout )
        layout.addWidget( _box, 2, 8, 8, 2 )
        #
        self.setLayout( layout )
        pass

    def fetchRemoteCapability(self):
        _url = "https://api.github.com/repos/VDM-Maintainer-Group/vdm-capability-library/git/trees/main"
        try:
            res = url_request.urlopen(_url).read().decode('utf-8')
            res = json.loads(res)
            res = [ x['path'] for x in res['tree'] if x['mode']=='040000' ]
            if '__wrapper__' in res: res.remove('__wrapper__')
            #
            self.cap_list.clear()
            _installed = list( self.cm.query().keys() )
            for x in res:
                _item = QListWidgetItem(x)
                if x in _installed:
                    _item.setFlags( _item.flags() & ~Qt.ItemIsEnabled )
                self.cap_list.insertItem(-1, _item)
        except Exception as e:
            print(e)
        pass

    @pyqtSlot()
    def installRemoteCapability(self):
        _items = self.cap_list.selectedItems()
        if len(_items)>=1:
            name = _items[0].text()
            QMessageBox.critical(self, 'Capability Installation Failed',
                f'[{name}] installation not implemented.', QMessageBox.Ok)
            #if install succeed, 1) disable it in `cap_list` 2) refresh `info_box`
        pass

    @pyqtSlot()
    def installCapability(self):
        _selected = QFileDialog.getOpenFileName(self, caption="Select capability archive file",
                directory=POSIX( Path.home() ),
                filter="Archive file (*.zip)" )
        _filename, _type = _selected
        if _filename:
            res = self.cm.install(_filename) #ui is blocked here.
        pass

    @pyqtSlot(str)
    def toggleCapability(self, name:str):
        if self.cm.query(name)=='Capable':
            _func = self.cm.disable
        else:
            _func = self.cm.enable
        #
        return _func(name)==CapabilityCode.ALL_CLEAN

    @pyqtSlot()
    def toggleDaemon(self):
        if self.sender():
            _action = self.sender().text().lower()
            self.cm.daemon(_action)
        #
        _status = self.cm.daemon('status')
        if _status==CapabilityCode.DAEMON_IS_RUNNING:
            self.start_button.setText('Restart')
            self.stop_button.setEnabled(True)
        else:
            self.start_button.setText('Start')
            self.stop_button.setEnabled(False)
        pass

    pass

class PMTabWidget(QWidget):
    def __init__(self, parent, pm):
        super().__init__(parent)
        self.parent = parent
        self.pm = pm
        #
        self.styleHelper()
        pass

    def styleHelper(self):
        layout = QGridLayout()
        # add information box (6x10)
        # _box = QGroupBox('Plugin')
        self.info_box = InformationArea(self,
            lambda: self.pm.list().items(),
            ['<uninstall>', 'name', 'version', 'description', 'author', 'capability', 'homepage', '<run>'],
            {'uninstall':self.uninstallPlugin, 'run':self.runPluginFunction},
            entry=1
        )
        self.info_box.itemClicked.connect( self.onItemClicked )
        # _sub_layout = QVBoxLayout()
        # _sub_layout.addWidget(self.info_box)
        # _box.setLayout( _sub_layout )
        layout.addWidget(self.info_box, 0, 0, 6, 10)
        # add install buttion (1x2)
        _button = QPushButton("Install ...", self)
        _button.clicked.connect( self.installPlugin )
        layout.addWidget(_button, 6, 0, 1, 2)
        # add status label (1x8)
        self.status_label = QLabel(self)
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_label.setStyleSheet("border: 1px solid grey;")
        layout.addWidget(self.status_label, 6, 2, 1, 8)
        #
        self.setLayout( layout )
        pass

    @pyqtSlot()
    def onItemClicked(self):
        row, col = self.info_box.currentRow(), self.info_box.currentColumn()
        item = self.info_box.item(row, col)
        if item: self.info( item.text() )
        pass

    @pyqtSlot(str)
    def info(self, msg:str):
        self.status_label.setText(msg)
        pass

    @pyqtSlot()
    def installPlugin(self):
        _selected = QFileDialog.getOpenFileName(self, caption="Select plugin archive file",
                directory=POSIX( Path.home() ),
                filter="Archive file (*.zip)" )
        _filename, _type = _selected
        res = self.pm.install(_filename)
        if res==True:
            _name = Path(_filename).name
            self.info(f'Success: installed from "{_name}".')
            self.info_box.refresh()
        else:
            self.info(f'Installation failed: {res.name}.')
        pass

    @pyqtSlot(str)
    def uninstallPlugin(self, name:str):
        confirm_box = QMessageBox()
        confirm_box.setText(f'Are you sure you want to uninstall "{name}"?')
        confirm_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_box.setDefaultButton(QMessageBox.No)
        if confirm_box.exec() != QMessageBox.Yes: return
        #
        self.info(f'Uninstall "{name}" ...')
        res = self.pm.uninstall(name)
        if res==True:
            self.info(f'Uninstalled: "{name}".')
            self.info_box.refresh()
        else:
            self.info(f'Uninstall failed: {res.name}.')
        pass

    @pyqtSlot(str)
    def runPluginFunction(self, name:str):
        dialog = QDialog(self)
        form = QFormLayout(dialog)
        ##
        form.addRow( QLabel('Functions:') )
        choices = QComboBox()
        choices.addItems(['onStart', 'onSave', 'onResume', 'onClose', 'onStop'])
        form.addRow(choices)
        ##
        form.addRow( QLabel('Arguments:') )
        arguments = QLineEdit(self)
        form.addRow(arguments)
        ##
        btn = QPushButton('Run')
        btn.clicked.connect(lambda:self.pm.run(
            name, choices.currentText(), arguments.text().split()
        ))
        form.addRow(btn)
        ##
        dialog.exec()
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
        self.dm_tab = DMTabWidget(self, self.core.dm, self.core.pm)
        self.addTab(self.dm_tab, 'Domain Manager')
        #
        self.cm_tab = CMTabWidget(self, self.core.cm)
        self.addTab(self.cm_tab, 'Capability Manager')
        #
        self.pm_tab = PMTabWidget(self, self.core.pm)
        self.addTab(self.pm_tab, 'Plugin Manager')
        #
        pass

    def route(self, uri):
        _tab, name = uri.split('://')
        if _tab=='MainTab':
            pass
        elif _tab=='DMTab':
            pass
        elif _tab=='CMTab':
            pass
        elif _tab=='PMTab':
            self.pm_tab.info_box.select(name)
            self.setCurrentWidget( self.pm_tab )
        else:
            pass
        pass

    pass

if __name__== '__main__':
    import sys
    app = QApplication(sys.argv)
    main_window = ControlPanelWindow()
    main_window.show()
    sys.exit(app.exec_())