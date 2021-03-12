#!/usr/bin/env python3
'''Mind Flash
This is *mf*, a flash pass your mind.
You Write, You Listen.
'''
import sys, time, pkg_resources
from PyQt5.QtCore import (QEasingCurve, QPropertyAnimation, Qt, QSize, QRect, QTimer, QThread, pyqtSlot)
from PyQt5.QtGui import (QBrush, QColor, QMovie, QPainter, QPen, QPixmap)
from PyQt5.QtWidgets import (QApplication, QGraphicsOpacityEffect, QLabel, QProxyStyle, QWidget, QDesktopWidget,
                    QLayout, QGridLayout)

ASSETS = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/'+_)
SIZE_FULLSCREEN = -1
SIZE_ORIGINAL   = 0


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
    def __init__(self, parent, filename, size=0, mask=True):
        super().__init__(parent)
        self.parent = parent
        self.mask = mask
        self.styleHelper()
        self.setScene(filename, size)
        pass
    
    def styleHelper(self):
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.setAlignment(Qt.AlignCenter)
        #
        self.label = QLabel('Transition Scene', self)
        if self.mask:
            self.proxy_style = RoundPixmapStyle(style=self.label.style())
            self.label.setStyle(self.proxy_style)
        else:
            self.proxy_style = None
        self.grid.addWidget(self.label, 0, 0)
        self.setLayout(self.grid)
        #
        self.setFixedSize( self.parent.size() )
        pass

    def setScene(self, filename, size):
        self.movie = QMovie( ASSETS(filename) )
        self.movie.jumpToFrame(0)
        _movie_size = self.movie.currentImage().size()
        if size==SIZE_ORIGINAL:
            self.movie_size = _movie_size
        elif size==SIZE_FULLSCREEN:
            _movie_size.scale( self.parent.size(), Qt.KeepAspectRatio )
            self.movie.setScaledSize(_movie_size)
            pass
        else: #custom size
            _movie_size.scale( QSize(size, size), Qt.KeepAspectRatio )
            self.movie.setScaledSize(_movie_size)
            pass
        #
        self.label.setMovie(self.movie)
        self.label.setFixedSize( self.movie_size )
        if self.mask and size!=SIZE_FULLSCREEN:
            self.proxy_style.setRadius( self.movie_size.height() / 2 )
        pass

    def start(self):
        if self.movie: self.movie.start()
        #play sound effect
        pass

    def stop(self):
        if self.movie: self.movie.stop()
        #stop sound effect
        pass

    pass

class TransitionSceneWidget(QWidget):
    def __init__(self, parent=None, size=0, mask=True):
        super().__init__(parent)
        # set fullscreen size on default display
        self.setFixedSize( QDesktopWidget().availableGeometry().size() )
        self.w_scene  = SceneManager(self, 'MOV-Trans-BNA.gif', size, mask)
        self.start_time = time.time()
        # set main window layout as grid
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.addWidget(self.w_scene, 0, 0)
        self.setLayout(self.grid)
        self.resize(self.sizeHint())
        # set window style
        self.styleHelper()
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

    def styleHelper(self):
        self.eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.eff)
        pass

    #Reference: https://stackoverflow.com/questions/19087822/how-to-make-qt-widgets-fade-in-or-fade-out
    def fadeIn(self):
        self.fade_in = QPropertyAnimation(self.eff, b'opacity')
        self.fade_in.setDuration(450)
        self.fade_in.setStartValue(0); self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.InBack)
        #
        self.setVisible(True)
        self.fade_in.start()
        pass

    def fadeOut(self, callback, args=None):
        self.fade_out = QPropertyAnimation(self.eff, b'opacity')
        self.fade_out.setDuration(450)
        self.fade_out.setStartValue(1.); self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.OutBack)
        #
        if args is tuple:
            _cb = lambda: callback(*args)
        else:
            _cb = lambda: callback()
        #
        self.setVisible(False)
        self.fade_out.start()
        self.fade_out.finished.connect(_cb)
        pass

    def hideScene(self):
        self.setVisible(False)
        self.w_scene.stop()
        pass

    @pyqtSlot()
    def start(self):
        self.fadeIn()
        self.start_time = time.time()
        self.w_scene.start()
        pass

    @pyqtSlot()
    def stop(self):
        _elapsed = time.time() - self.start_time
        if _elapsed < 0.5:
            _sleep = int( 1000*(0.5-_elapsed) )
            QTimer.singleShot(_sleep, self.stop)
        else:
            self.fadeOut( self.hideScene )
        pass

    pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_ts = TransitionSceneWidget()
    main_ts.start()
    # main_ts.fade_in.finished.connect( main_ts.stop )
    sys.exit(app.exec_())