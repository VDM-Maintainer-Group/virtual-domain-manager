#!/usr/bin/env python3
from pathlib import Path
from PyQt5.QtCore import (QObject, QMetaObject, Q_ARG, pyqtSlot)
from PyQt5.QtQml import QQmlApplicationEngine

SYM_NEXT = '→'
SYM_BACK = '←'
SYM_PLUS = '＋'

class TraversalController(QObject):
    def __init__(self, root, domain_manager):
        super().__init__(None)
        self.root = root
        self.dm = domain_manager
        pass

    @pyqtSlot()
    def refresh(self):
        openName = self.dm.open_domain_name
        predName = self.root.property('predName')
        ##
        domain_list = sorted( self.dm.list_child_domain(predName) )
        for i,name in enumerate(domain_list):
            num = len(self.dm.list_child_domain(name))
            domain_list[i] = {'name':name, 'selected':name==openName, 'shortcut':SYM_NEXT if num else SYM_PLUS}
        ##
        if predName=='' and len(domain_list)==0:
            predName = SYM_PLUS
        else:
            domain_list.append({'name':SYM_PLUS, 'selected':False, 'shortcut':''})
        ##
        self.root.setProperty('openName', openName)
        self.root.setProperty('predName', predName)
        QMetaObject.invokeMethod(self.root, 'setDomainList', Q_ARG("QVariant", domain_list))
        pass

    @pyqtSlot(str)
    def open_domain(self, openName):
        #TODO: self.dm.open_domain(name)
        self.root.setProperty('openName', openName)
        self.refresh()
        pass

    @pyqtSlot()
    def create_domain(self):
        #TODO: self.dm.create_domain()
        print('create_domain')
        pass

    @pyqtSlot(str)
    def delete_domain(self, name):
        #TODO: self.dm.delete_domain(name)
        print('delete_domain', name)
        pass

    @pyqtSlot(str, bool)
    def fork_domain(self, name, copy):
        #TODO: self.dm.fork_domain()
        print('fork_domain', name, copy)
        pass

    @pyqtSlot(str)
    def set_pred_name(self, predName):
        self.root.setProperty('predName', predName)
        self.refresh()
        pass

    @pyqtSlot(str,str)
    def update_name(self, old_name, new_name):
        #TODO: self.dm.update_domain_name(old_name, new_name)
        print('update_name', old_name, new_name)
        pass

    pass
    

class TraversalWidget():
    def __init__(self, parent, domain_manager):
        self.parent = parent
        self.dm = domain_manager
        ##
        qml_folder = Path(__file__).parent / 'qml'
        source = (qml_folder / 'main.qml').as_posix()
        self.engine = QQmlApplicationEngine()
        self.engine.load(source)
        self.root = self.engine.rootObjects()[0]
        ##
        self.controller = TraversalController(self.root, self.dm)
        self.engine.rootContext().setContextProperty('controller', self.controller)
        self.controller.refresh()
        pass

    def show(self):
        self.root.show()
    pass

if __name__ == '__main__':
    import sys
    from pyvdm.core.manager import CoreManager
    from PyQt5.QtWidgets import QApplication

    cm = CoreManager()
    app = QApplication(sys.argv)
    w = TraversalWidget(cm, cm.dm)
    w.show()
    sys.exit(app.exec())
