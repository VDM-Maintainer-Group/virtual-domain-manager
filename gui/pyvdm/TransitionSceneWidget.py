#!/usr/bin/env python3
'''Mind Flash
This is *mf*, a flash pass your mind.
You Write, You Listen.
'''
import sys, pkg_resources
from PyQt5.QtCore import (Qt, QSize, QRect, QTimer, QThread, pyqtSlot)
from PyQt5.QtGui import (QBrush, QColor, QMovie, QPainter, QPen, QPixmap)
from PyQt5.QtWidgets import (QApplication, QLabel, QProxyStyle, QWidget, QDesktopWidget,
                    QLayout, QGridLayout)

ASSETS = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/'+_)

#Reference: https://stackoverflow.com/questions/54230005/qmovie-with-border-radius
class RoundPixmapStyle(QProxyStyle):
    def __init__(self, radius=0, *args, **kwargs):
        super(RoundPixmapStyle, self).__init__(*args, **kwargs)
        self._radius = radius
        pass

    def setRadius(self, radius):
        self._radius = radius
        pass

    def drawItemPixmap(self, painter, rectangle, alignment, pixmap):
        painter.save()
        pix = QPixmap(pixmap.size()) #_rect.size()
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        #
        w,h = pixmap.width(), pixmap.height()
        _rect = QRect(pixmap.rect())
        if w>h:
            d = (w-h) / 2
            _rect.adjust(d, 0, -d, 0)
        else:
            d = (h-w) / 2
            _rect.adjust(0, d, 0, -d)
        p.setBrush(QBrush(pixmap))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(_rect, self._radius, self._radius) #pixmap.rect()
        #
        p.end()
        super(RoundPixmapStyle, self).drawItemPixmap(painter, rectangle, alignment, pix)
        painter.restore()
        pass
    pass

class SceneManager(QWidget):
    def __init__(self, parent, filename):
        super().__init__(parent)
        self.parent = parent
        self.styleHelper()
        self.setScene(filename)
        self.show()
        pass
    
    def styleHelper(self):
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.setAlignment(Qt.AlignCenter)
        #
        self.label = QLabel('Transition Scene', self)
        self.proxy_style = RoundPixmapStyle(style=self.label.style())
        self.label.setStyle(self.proxy_style)
        self.grid.addWidget(self.label, 0, 0)
        self.setLayout(self.grid)
        #
        self.setFixedSize( self.parent.size() )
        pass

    def setScene(self, filename):
        self.movie = QMovie( ASSETS(filename) )
        self.movie.jumpToFrame(0)
        self.movie_size = self.movie.currentImage().size()
        #
        self.label.setMovie(self.movie)
        self.label.setFixedSize( self.movie_size )
        self.proxy_style.setRadius( self.movie_size.height() / 2 )
        pass

    @pyqtSlot()
    def start(self):
        if self.movie: self.movie.start()
        self.setVisible(True)
        pass

    @pyqtSlot()
    def stop(self):
        if self.movie: self.movie.stop()
        self.setVisible(False)
        pass

    pass

class TransitionSceneWidget(QWidget):
    def __init__(self):
        super().__init__()
        # set fullscreen size on default display
        self.setFixedSize( QDesktopWidget().availableGeometry().size() )
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
        self.setVisible(False)
        pass

    #Reference: https://stackoverflow.com/questions/33982167/pyqt5-create-semi-transparent-window-with-non-transparent-children
    def paintEvent(self, event=None):
        painter = QPainter(self)
        _color = QColor('#f0f5e5') #fromRgb(255,254,249) #Qt.white
        painter.setOpacity(0.97)
        painter.setBrush(_color)
        painter.setPen( QPen(_color) )
        painter.drawRect( self.rect() )
        pass

    pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_ts = TransitionSceneWidget()
    main_ts.w_scene.start()
    sys.exit(app.exec_())