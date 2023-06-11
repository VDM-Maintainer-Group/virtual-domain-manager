#!/usr/bin/env python3
from pathlib import Path
from PyQt5.QtCore import (QObject, pyqtSlot)
from PyQt5.QtQml import QQmlApplicationEngine


class TraversalController(QObject):
    def __init__(self, root, domain_manager):
        super().__init__(None)
        self.root = root
        self.dm = domain_manager
        pass

    @pyqtSlot()
    def refresh(self):
        open_name = self.dm.open_domain_name
        pred_name = self.root.property('pred_name')
        domain_list = self.dm.list_child_domain(pred_name)
        domain_list = [(name, len(self.dm.list_child_domain(pred_name))==0)
                       for name in domain_list]
        ##
        if pred_name=='' and len(domain_list)==0: pred_name = '+'
        self.root.setProperty('open_name', open_name)
        self.root.setProperty('pred_name', pred_name)
        self.root.setProperty('domain_list', domain_list)
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
