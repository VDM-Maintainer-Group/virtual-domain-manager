#!/usr/bin/env python3
import sys
import time
from PyQt5.QtCore import (QEasingCurve, QPropertyAnimation, Qt, QSize, QRect, QTimer, QUrl,
                    QThread, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QBrush, QColor, QMovie, QPainter, QPen, QPixmap)
from PyQt5.QtWidgets import (QApplication, QGraphicsOpacityEffect, QLabel, QProxyStyle, QWidget,
                    QDesktopWidget, QLayout, QGridLayout)
from PyQt5.QtMultimedia import (QAudioDeviceInfo, QSoundEffect)

from pyvdm.gui.utils import CONFIG

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
        pix.fill(Qt.transparent) #type: ignore
        p = QPainter(pix)
        #
        w,h = pixmap.width(), pixmap.height()
        _rect = QRect(pixmap.rect())
        if w>h:
            d = int( (w-h) / 2 )
            _rect.adjust(d, 0, -d, 0)
        else:
            d = int( (h-w) / 2 )
            _rect.adjust(0, d, 0, -d)
        p.setBrush(QBrush(pixmap))
        p.setPen(Qt.NoPen) #type: ignore
        p.drawRoundedRect(_rect, self._radius, self._radius) #pixmap.rect()
        #
        p.end()
        super(RoundPixmapStyle, self).drawItemPixmap(painter, rectangle, alignment, pix)
        painter.restore()
        pass
    pass

class SceneManager(QWidget):
    play_signal  = pyqtSignal()

    def __init__(self, parent, size=0, mask=True):
        super().__init__(parent)
        self.parent = parent
        self.mask = mask # type: ignore
        self.size = size # type: ignore
        self.styleHelper()
        #
        self.soundEffect = None
        self.play_signal.connect(self.playSoundEffect) # type: ignore
        pass
    
    def styleHelper(self):
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.setAlignment(Qt.AlignCenter) #type: ignore
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

    def setupScene(self):
        self.movie = QMovie( CONFIG['THEME_MOV_TRANS'], parent=self )
        self.movie.jumpToFrame(0)
        _size = self.size
        #
        _movie_size = self.movie.currentImage().size()
        if _size==SIZE_ORIGINAL:
            self.movie_size = _movie_size
        elif _size==SIZE_FULLSCREEN:
            _movie_size.scale( self.parent.size(), Qt.KeepAspectRatio ) #type: ignore
            self.movie.setScaledSize(_movie_size)
            pass
        else: #custom size
            _movie_size.scale( QSize(_size, _size), Qt.KeepAspectRatio ) #type: ignore
            self.movie.setScaledSize(_movie_size)
            pass
        #
        self.label.setMovie(self.movie)
        self.label.setFixedSize( self.movie_size )
        if self.mask and _size!=SIZE_FULLSCREEN:
            self.proxy_style.setRadius( self.movie_size.height() / 2 ) #type: ignore
        pass

    @pyqtSlot()
    def playSoundEffect(self):
        _url = QUrl.fromLocalFile( CONFIG['THEME_SE_TRANS'] )
        self.soundEffect = QSoundEffect( self )
        self.soundEffect.setLoopCount( QSoundEffect.Infinite ) #type: ignore
        self.soundEffect.setSource(_url)
        self.soundEffect.play()
        pass

    def start(self):
        self.setupScene()
        if self.movie: self.movie.start()
        self.play_signal.emit()
        pass

    def stop(self):
        if self.movie: self.movie.stop()
        self.soundEffect.stop() #type: ignore
        pass

    pass

class TransitionSceneWidget(QWidget):
    def __init__(self, parent=None, size=0, mask=True):
        super().__init__(parent)
        # set fullscreen size on default display
        self.setFixedSize( QDesktopWidget().availableGeometry().size() )
        self.w_scene  = SceneManager(self, size, mask)
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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) #type: ignore
        self.setAttribute(Qt.WA_TranslucentBackground, True) #type: ignore
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
            QTimer.singleShot(_sleep, self.stop) # type: ignore
        else:
            self.fadeOut( self.hideScene )
        pass

    pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_ts = TransitionSceneWidget()
    main_ts.start() # type: ignore
    # main_ts.fade_in.finished.connect( main_ts.stop )
    sys.exit(app.exec_())