#!/usr/bin/env python3
'''Mind Flash
This is *mf*, a flash pass your mind.
You Write, You Listen.
'''
import sys, pkg_resources
from PyQt5.QtCore import (Qt, QPoint, QSize, QTimer, QThread, pyqtSlot)
from PyQt5.QtGui import (QFont, QFontMetrics, QIcon, QMovie)
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QDesktopWidget,
                    QLayout, QGridLayout)

ASSETS = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/'+_)

class SceneManager(QWidget):
    def __init__(self, parent, filename):
        super().__init__(parent)
        self.parent = parent
        self.styleHelper()
        self.setScene(filename)
        self.show()
        self.start()
        pass
    
    def styleHelper(self):
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.setAlignment(Qt.AlignCenter)
        #
        self.label = QLabel('Transition Scene', self)
        self.grid.addWidget(self.label, 0, 0)
        self.setLayout(self.grid)
        #
        self.setFixedSize( self.parent.size() )
        self.setStyleSheet('''
            .QWidget {
                background: rgba(255,254,249, 0.96)
            }
        ''')
        pass

    def setScene(self, filename):
        self.movie = QMovie( ASSETS(filename) )
        self.movie.jumpToFrame(0)
        self.movie_size = self.movie.currentImage().size()
        #
        self.label.setMovie(self.movie)
        self.label.setFixedSize( self.movie_size )
        pass

    @pyqtSlot()
    def start(self):
        print(self.size(), self.label.size())
        if self.movie: self.movie.start()
        pass

    @pyqtSlot()
    def stop(self):
        if self.movie: self.movie.stop()
        pass

    pass

class TransitionSceneWidget(QWidget):
    def __init__(self):
        super().__init__()
        # set fullscreen size on default display
        cp = QDesktopWidget().availableGeometry().size()
        self.setFixedSize(cp)
        self.w_scene  = SceneManager(self, 'MOV-Trans-BNA.gif')
        # set main window layout as grid
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.addWidget(self.w_scene, 0, 0)
        self.setLayout(self.grid)
        self.resize(self.sizeHint())
        # set window style
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocus()
        self.show()
        pass

    pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_ts = TransitionSceneWidget()
    sys.exit(app.exec_())