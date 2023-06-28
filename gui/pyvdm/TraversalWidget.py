#!/usr/bin/env python3
from pathlib import Path
from PyQt5.QtCore import (QObject, QMetaObject, Q_ARG, pyqtSlot)
from PyQt5.QtQml import QQmlApplicationEngine

import pyvdm.core.errcode as errcode

SYM_NEXT = '→'
SYM_BACK = '←'
SYM_PLUS = '＋'

class TraversalController(QObject):
    def __init__(self, parent, root_view, domain_manager):
        super().__init__(None)
        self.parent = parent
        self.root = root_view
        self.dm = domain_manager
        pass

    @pyqtSlot(str)
    def set_pred_name(self, predName):
        self.root.setProperty('predName', predName)
        self.refresh() #type: ignore
        pass

    @pyqtSlot()
    def refresh(self):
        openName = self.dm.open_domain_name
        predName = self.root.property('predName')
        ##
        predName = '' if predName==SYM_PLUS else predName
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
        self.parent.switch_domain(openName)
        self.root.setProperty('openName', openName)
        self.root.setProperty('visible', False)
        pass

    @pyqtSlot()
    def create_domain(self):
        cnt = 0
        ret = self.dm.create_domain('Default', None, tui=False)
        while ret!=errcode.DomainCode.ALL_CLEAN:
            cnt += 1
            ret = self.dm.create_domain(f'Default-{cnt}', None, tui=False)
        self.refresh() #type: ignore
        pass

    @pyqtSlot(str)
    def delete_domain(self, name):
        self.dm.delete_domain(name, allow_recursive=False)
        self.refresh() #type: ignore
        pass

    @pyqtSlot(str, bool)
    def fork_domain(self, name, copy):
        if name:
            ret = self.dm.fork_domain(name, copy)
            if not copy and ret==errcode.DomainCode.ALL_CLEAN:
                self.root.setProperty('predName', name)
        else:
            ret = self.create_domain() #type: ignore
        self.refresh() #type: ignore
        pass

    @pyqtSlot(str,str,result=bool) #type: ignore
    def update_name(self, old_name, new_name):
        ret = self.dm.update_domain(old_name, None, False, new_name)
        self.refresh() #type: ignore
        return ret==errcode.DomainCode.ALL_CLEAN
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
        self.controller = TraversalController(parent, self.root, self.dm)
        self.engine.rootContext().setContextProperty('controller', self.controller)
        self.controller.refresh() #type: ignore
        pass

    def show(self):
        self.controller.refresh() #type: ignore
        self.root.setProperty('visible', True)
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
