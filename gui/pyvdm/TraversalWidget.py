#!/usr/bin/env python3
from pathlib import Path

from PyQt5.QtQml import QQmlApplicationEngine

class TraversalWidget():
    def __init__(self):
        self.qml_folder = Path(__file__).parent / 'qml'
        source = (self.qml_folder / 'main.qml').as_posix()
        ##
        self.engine = QQmlApplicationEngine()
        self.engine.load(source)
        pass
    
    def show(self):
        self.engine.rootObjects()[0].show()
    pass

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = TraversalWidget()
    w.show()
    sys.exit(app.exec())
