#!/usr/bin/env python3
from utils import (ASSETS, CONFIG, POSIX, signal_emit)
from pathlib import Path
from pyvdm.core.manager import CoreManager
from PyQt5.QtCore import (Qt, QThread, QUrl, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QIcon, )
from PyQt5.QtWidgets import (
            QApplication, QTabWidget, QDesktopWidget, QAbstractItemView, QHeaderView,
            QWidget,  QTableWidget, QGroupBox, QGridLayout, QFormLayout, QTableWidgetItem,
            QPushButton, QLabel, QDialog, QFileDialog, QMessageBox, QComboBox, QLineEdit)
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
        self.styleHelper()
        self.refresh()
        pass

    def styleHelper(self):
        _header = [x if '<' not in x else '' for x in self.header]
        self.setColumnCount( self.length )
        self.setHorizontalHeaderLabels( _header )
        #
        for i,x in enumerate(self.header):
            if i==self.entry or '<' in x:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
            else:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)
        #
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        pass

    def refresh(self):
        self.setRowCount(0)

        for i,(key,value) in enumerate( self.loader() ):
            _row = i
            self.insertRow( _row )
            for j in range(self.length):
                if j==self.entry:
                    _item = QTableWidgetItem(key)
                    self.setItem(_row, j, _item)
                elif '<' in self.header[j]:
                    _title = self.header[j].strip('<>')
                    _button = QPushButton(_title)
                    _button.setObjectName(key)
                    _button.clicked.connect( self.onButtonClicked )
                    self.setCellWidget(_row, j, _button)
                else:
                    _item = value[ self.header[j] ]
                    _item = str(_item) if _item is not str else _item
                    _item = QTableWidgetItem( _item )
                    self.setItem(_row, j, _item)
            pass
        pass

    @pyqtSlot()
    def onButtonClicked(self):
        _btn = self.sender()
        _title = _btn.text()
        key = _btn.objectName()
        self.slots[_title](key)
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
        self.info_box = InformationArea(self,
            lambda: self.pm.list().items(),
            ['<uninstall>', 'name', 'version', 'description', 'author', 'capability', 'homepage', '<run>'],
            {'uninstall':self.uninstallPlugin, 'run':self.runPluginFunction},
            entry=1
        )
        self.info_box.itemClicked.connect( self.onItemClicked )
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
        self.dm_tab = DMTabWidget(self, self.core.dm)
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
        pass

    pass

if __name__== '__main__':
    import sys
    app = QApplication(sys.argv)
    main_window = ControlPanelWindow()
    main_window.show()
    sys.exit(app.exec_())