import sys
import os
import time
from MainScreenThread import Thread
from PlaybackScreenThread import ScrollThread
from PySide6.QtCore import Qt, QThread, Signal, Slot,QAbstractTableModel, QPoint, QRect, QSize, QTimer
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QScreen
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget,QTableView,QTableWidget,
                               QScrollArea,QFrame, QTableWidgetItem,QProgressDialog,QRubberBand,QAbstractItemView, QStyle, QSlider)
                   
class Window(QMainWindow):
    def eventFilter(self, object, event):
        if str(event.type()) == 'Type.HoverMove' and self.active_widget is not None:
            self.curpos = QPoint(event.position().x(),event.position().y()).toTuple()
            self.poslabel.setText("Frame #"+self.active_widget.objectName()+"  "+"Cursor Position (x,y): "+str(self.curpos))
            return True
        elif str(event.type()) == 'Type.HoverMove' and self.active_widget is None:
            self.curpos = QPoint(event.position().x(),event.position().y()).toTuple()
            self.poslabel.setText("Cursor Position (x,y): "+str(self.curpos))
            return True
        elif str(event.type()) == 'Type.HoverLeave':
            self.poslabel.setText("")
            return True
        else:
            return False

    def mouseDoubleClickEvent(self, event):
        if self.pause.isEnabled():
            return

        else:
            widget = self.childAt(event.position().x(),event.position().y())
            widgets = self.contentwidget.findChildren(QLabel)
            
            if widget is not None and widget.objectName():
                self.playback_mode = 'idle'
                self.active_widget = widget
                self.th.set_file(self.table.item(0,0),widget.objectName())
                widget.setStyleSheet("border: 5px solid green;")
                for w in widgets:
                    if w.objectName() != self.active_widget.objectName():
                        w.setStyleSheet("border:0px solid black")
                if int(self.active_widget.objectName()) == self.total_frames-1:
                    self.play.setDisabled(1)
                    self.play.setCheckable(0)
                    self.rewind.setDisabled(0)
                    self.rewind.setCheckable(1)
                if int(self.active_widget.objectName()) == 0:
                    self.play.setDisabled(0)
                    self.play.setCheckable(1)
                    self.rewind.setDisabled(1)
                    self.rewind.setCheckable(0)

                if int(self.active_widget.objectName()) != self.total_frames-1 and int(self.active_widget.objectName()) != 0:
                    self.play.setDisabled(0)
                    self.play.setCheckable(1)
                    self.rewind.setDisabled(0)
                    self.rewind.setCheckable(1)

    # def mousePressEvent(self, event):
    #     if self.rubberBand:
    #         self.rubberBand.hide()
    #     widget = self.childAt(event.position().x(),event.position().y())
    #     if widget.objectName() == 'MainScreen':
    #         self.origin = QPoint(event.position().x(),event.position().y())
    #         if not self.rubberBand:
    #             self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
    #         self.rubberBand.setGeometry(QRect(self.origin, QSize()))
    #         self.rubberBand.show()

    # def mouseMoveEvent(self, event):
    #     self.rubberBand.setGeometry(QRect(self.origin, QPoint(event.position().x(),event.position().y())))
    
    def __init__(self):
        # super().__init__()
        super(Window, self).__init__()
        self.setWindowTitle("Vision Explorer")
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.active_widget = None
        self.playback_mode = 'idle'
        self.rubberBand = None
        self.total_frames = None
        self.frame_rate = 1
        

         
        screenGeometry = QScreen.availableGeometry(QApplication.primaryScreen())
        self.setGeometry(screenGeometry)
        self.showMaximized()

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=qApp.quit)
        self.menu_file.addAction(exit)

        self.menu_about = self.menu.addMenu("&About")
        about = QAction("About Qt", self, shortcut=QKeySequence(QKeySequence.HelpContents),
                        triggered=qApp.aboutQt)
        self.menu_about.addAction(about)

        # Create a label for the display camera
        self.label = QLabel(self)
        self.label.setObjectName('MainScreen')
        self.label.setFixedSize(640, 480)
        self.label.setStyleSheet("background-color:black")
        self.label.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.label.installEventFilter(self)

        self.poslabel = QLabel(self)
        self.poslabel.setAlignment(Qt.AlignCenter)
        self.poslabel.setStyleSheet("color:white")

        self.th = Thread(self)
        self.th.updateFrame.connect(self.setImage)

        self.scrollth = ScrollThread(self)
        self.scrollth.updatescroll.connect(self.setScrollImage)
        
        # Main layout
        toplayout = QHBoxLayout()
        leftlayout = QVBoxLayout()
        leftlayout.addWidget(self.label)
        leftlayout.addWidget(self.poslabel)
        leftlayout.setContentsMargins(0,0,0,0)
        leftlayout.setSpacing(5)
        leftlayout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        
        rightlayout = QVBoxLayout()
        self.table = QTableWidget(100, 100, self)
        self.table.cellChanged.connect(self.set_source)
        self.table.setStyleSheet("background-color:white")
        rightlayout.addWidget(self.table)
        toplayout.addLayout(leftlayout)
        toplayout.addLayout(rightlayout)
        toplayout.setSpacing(150)

        self.bottomlayout = QHBoxLayout()
        self.scrollArea = QScrollArea()
        self.contentwidget = QWidget()
        self.scroll_layout = QHBoxLayout()
        self.playback_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.layout = QVBoxLayout()
        self.layout.addLayout(toplayout)
        

        # Central widget
        widget = QWidget(self)
        widget.setLayout(self.layout)
        widget.setStyleSheet("background-color: #26242f")
        self.setCentralWidget(widget)

        self.start()

    def create_scroll_layout(self):
        foreground = "green"
        color = "gray"
        disabledForeground = "red"
        disabledColor = color
        bold = "bold"
        button_style = ":enabled { color: " + foreground + "; background-color: " + color + "; font-weight:  " + bold + " } :disabled { color: " + disabledForeground + "; background-color: " + disabledColor + "; font-weight:  " + bold + " }"

        delay_style = 'QSlider::groove:horizontal {\
                        border: 1px solid #999999;\
                        height: 8px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */\
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);\
                        margin: 2px 0;\
                        }\
                        QSlider::handle:horizontal {\
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);\
                            border: 1px solid #5c5c5c;\
                            width: 18px;\
                            margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */\
                            border-radius: 3px;\
                        }'

        self.bottomlayout.deleteLater()
        self.scrollArea.deleteLater()
        self.contentwidget.deleteLater()
        self.scroll_layout.deleteLater()
        self.playback_layout.deleteLater()
        self.button_layout.deleteLater()

        self.bottomlayout = QHBoxLayout()
        self.scrollArea = QScrollArea()
        self.contentwidget = QWidget()
        self.scroll_layout = QHBoxLayout()
        self.playback_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.play = QPushButton("Play")
        self.play.setIcon(QApplication.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.play.setCheckable(True)
        self.play.setStyleSheet(button_style)
        self.play.clicked.connect(lambda:self.playButtonClicked(int(self.active_widget.objectName())))

        self.pause = QPushButton("Pause")
        self.pause.setIcon(QApplication.style().standardIcon(QStyle.SP_MediaPause))
        self.pause.setCheckable(True)
        self.pause.setStyleSheet(button_style)
        self.pause.clicked.connect(lambda:self.pauseButtonClicked())

        self.rewind = QPushButton("Rewind")
        self.rewind.setIcon(QApplication.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.rewind.setCheckable(True)
        self.rewind.setStyleSheet(button_style)
        self.rewind.clicked.connect(lambda:self.rewindButtonClicked(int(self.active_widget.objectName())))

        self.delay = QSlider(Qt.Horizontal)
        self.delay.setStyleSheet(delay_style)
        self.delay.setRange(1,100)
        self.delay.setSingleStep(5)
        self.delay.setMaximumWidth(250)
        self.delay.sliderMoved.connect(self.slider_position)

        self.contentwidget.setLayout(self.scroll_layout)
        
        self.scrollArea.setWidget(self.contentwidget)
        self.scrollArea.setFixedHeight(160)
        self.scrollArea.setWidgetResizable(True)
        
        self.button_layout.addWidget(self.rewind)
        self.button_layout.addWidget(self.pause)
        self.button_layout.addWidget(self.play)

        self.playback_layout.addLayout(self.button_layout)
        self.playback_layout.addWidget(self.delay)

        self.bottomlayout.addLayout(self.playback_layout)
        self.bottomlayout.addWidget(self.scrollArea)
        self.layout.addLayout(self.bottomlayout)
    
    def clear_scroll_layout(self):
        
        self.bottomlayout.deleteLater()
        self.scrollArea.deleteLater()
        self.contentwidget.deleteLater()
        self.scroll_layout.deleteLater()
        self.playback_layout.deleteLater()
        self.button_layout.deleteLater()
        self.play.deleteLater()
        self.pause.deleteLater()
        self.rewind.deleteLater()
        self.delay.deleteLater()

        self.bottomlayout = QHBoxLayout()
        self.scrollArea = QScrollArea()
        self.contentwidget = QWidget()
        self.scroll_layout = QHBoxLayout()
        self.playback_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.play = QPushButton()
        self.play.setCheckable(True)
        self.pause = QPushButton()
        self.pause.setCheckable(True)
        self.rewind = QPushButton()
        self.rewind.setCheckable(True)
        self.delay = QSlider(Qt.Horizontal)
        self.delay.setRange(25,1000)
        self.delay.setSingleStep(25)
        self.contentwidget.setLayout(self.scroll_layout)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() and not self.scrollth.isRunning():
            e.accept()
        else:
            e.ignore()


    def dropEvent(self, e):
        if e.mimeData().hasUrls() and not self.scrollth.isRunning():
            e.accept()
            urls = e.mimeData().urls()

            for url in urls:
                fname = url.toLocalFile()
                self.table.setItem(0,0,QTableWidgetItem(fname))  
        else:
            e.ignore()
    def slider_position(self,p):
        self.frame_rate = p

    @Slot()
    def closeEvent(self,event):
        self.th.terminate()
        self.scrollth.terminate()
        time.sleep(1)
        QMainWindow.closeEvent(self, event)

    @Slot()
    def start(self):
        self.th.start()
        
    
    @Slot()
    def set_source(self):
        if self.table.item(0,0) and not self.scrollth.isRunning():
            self.th.set_file(self.table.item(0,0),0)
        if self.table.item(0,0).text().lower().endswith('.mp4') or os.path.isdir(self.table.item(0,0).text()):
            self.active_widget = None
            self.scrollth.quit()
            time.sleep(1)
            self.create_scroll_layout()
            self.scrollth.start()
            self.scrollth.set_file(self.table.item(0,0))
                
        else:
            self.scrollth.quit()
            time.sleep(1)
            self.clear_scroll_layout()

    @Slot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    @Slot(QImage)
    def setScrollImage(self,data):       
        self.slabel=QLabel()
        self.slabel.setObjectName(str(data[1]))
        self.slabel.setFixedSize(160, 120)
        self.slabel.setPixmap(QPixmap.fromImage(data[0]))
        if self.slabel.objectName() == '0':
            self.active_widget = self.slabel
            self.progressDialog = QProgressDialog("Loading Images..", None, 0, data[2], self)
            self.progressDialog.setWindowTitle(" ")
            self.slabel.setStyleSheet("border: 5px solid green;")
        self.contentwidget.layout().addWidget(self.slabel)
        self.prog_update(data[1])
        self.total_frames = data[2]

    def prog_update(self,frame):
        if self.scrollth.isRunning():
            self.table.setDisabled(1)
            self.play.setDisabled(1)
            self.pause.setDisabled(1)
            self.rewind.setDisabled(1)
            self.progressDialog.setValue(frame)
            self.progressDialog.show()
        else:
            
            self.play.setEnabled(1)
            self.pause.setEnabled(0)
            self.table.setEnabled(1)
            self.progressDialog.hide()

    def playButtonClicked(self,i):
        i+=1
        self.play.setDisabled(1)
        self.play.setCheckable(0)
        self.th.set_file(self.table.item(0,0),i)
        self.active_widget = self.findChild(QWidget,str(i))
        self.active_widget.setStyleSheet("border: 5px solid green;")
        self.scrollArea.ensureWidgetVisible(self.active_widget)
        widgets = self.contentwidget.findChildren(QLabel)
        for w in widgets:
            if w.objectName() != self.active_widget.objectName():
                w.setStyleSheet("border:0px solid black")
                
        if self.playback_mode == 'paused':
            self.play.setDisabled(0)
            self.play.setCheckable(1)
            self.rewind.setDisabled(0)
            self.rewind.setCheckable(1)
            self.playback_mode = 'playing'

        else:
            if i < self.total_frames-1:
                self.playback_mode = 'playing'
                self.pause.setDisabled(0)
                self.pause.setCheckable(1)
                QTimer.singleShot((1000/self.frame_rate), lambda:self.playButtonClicked(i))

            elif i == self.total_frames-1:
                self.play.setDisabled(1)
                self.play.setCheckable(0)
                self.pause.setDisabled(1)
                self.pause.setCheckable(0)
                self.playback_mode == 'idle'
            else:
                self.play.setDisabled(0)
                self.play.setCheckable(1)
                self.playback_mode == 'idle'

    def rewindButtonClicked(self,i):
        i-=1
        self.rewind.setDisabled(1)
        self.rewind.setCheckable(0)
        self.th.set_file(self.table.item(0,0),i)
        self.active_widget = self.findChild(QWidget,str(i))
        self.active_widget.setStyleSheet("border: 5px solid green;")
        self.scrollArea.ensureWidgetVisible(self.active_widget)
        widgets = self.contentwidget.findChildren(QLabel)
        for w in widgets:
            if w.objectName() != self.active_widget.objectName():
                w.setStyleSheet("border:0px solid black")
                
        if self.playback_mode == 'paused':
            self.rewind.setDisabled(0)
            self.rewind.setCheckable(1)
            self.play.setDisabled(0)
            self.play.setCheckable(1)
            self.playback_mode = 'rewind'

        else:
            if i > 0:
                self.playback_mode = 'rewind'
                self.pause.setDisabled(0)
                self.pause.setCheckable(1)
                QTimer.singleShot((1000/self.frame_rate), lambda:self.rewindButtonClicked(i))

            elif i == 0:
                self.rewind.setDisabled(1)
                self.rewind.setCheckable(0)
                self.pause.setDisabled(1)
                self.pause.setCheckable(0)
                self.playback_mode == 'idle'
            else:
                self.rewind.setDisabled(0)
                self.rewind.setCheckable(1)
                self.playback_mode == 'idle'

    def pauseButtonClicked(self):
        self.pause.setDisabled(1)
        self.pause.setCheckable(0)
        self.th.set_file(self.table.item(0,0),int(self.active_widget.objectName()))
        widgets = self.contentwidget.findChildren(QLabel)
        self.active_widget.setStyleSheet("border: 5px solid green;")
        self.scrollArea.ensureWidgetVisible(self.active_widget)
        for w in widgets:
            if w.objectName() != self.active_widget.objectName():
                w.setStyleSheet("border:0px solid black")
        self.playback_mode = 'paused'

            
            
        

if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec())