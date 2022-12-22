import sys
import os
import time
from MainScreenThread import Thread
from PlaybackScreenThread import ScrollThread
from PySide6.QtCore import Qt, QThread, Signal, Slot,QAbstractTableModel, QPoint, QRect, QSize
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QScreen
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget,QTableView,QTableWidget,
                               QScrollArea,QFrame, QTableWidgetItem,QProgressDialog,QRubberBand,QAbstractItemView)
                   
class Window(QMainWindow):
    def eventFilter(self, object, event):
        if str(event.type()) == 'Type.HoverMove':
            self.curpos = QPoint(event.position().x(),event.position().y()).toTuple()
            self.poslabel.setText("Cursor Position (x,y): "+str(self.curpos))
            return True
        elif str(event.type()) == 'Type.HoverLeave':
            self.poslabel.setText("")
            return True
        else:
            return False

    def mouseDoubleClickEvent(self, event):
        if self.active_widget is not None:
            self.active_widget.setStyleSheet("border:0px solid black")
        widget = self.childAt(event.position().x(),event.position().y())
        if widget is not None and widget.objectName():
            self.active_widget = widget
            self.th.set_file(self.table.item(0,0),widget.objectName())
            widget.setStyleSheet("border: 5px solid green;")
            if widget.objectName() != '0':
                firstframe = self.findChild(QWidget,'0')
                firstframe.setStyleSheet("border:0px solid black")
    
    def mousePressEvent(self, event):
        if self.rubberBand:
            self.rubberBand.hide()
        widget = self.childAt(event.position().x(),event.position().y())
        if widget.objectName() == 'MainScreen':
            self.origin = QPoint(event.position().x(),event.position().y())
            if not self.rubberBand:
                self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        self.rubberBand.setGeometry(QRect(self.origin, QPoint(event.position().x(),event.position().y())))
    
    def __init__(self):
        # super().__init__()
        super(Window, self).__init__()
        self.setWindowTitle("Vision Explorer")
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.active_widget = None
        self.rubberBand = None
        

         
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

        self.layout = QVBoxLayout()
        self.layout.addLayout(toplayout)
        

        # Central widget
        widget = QWidget(self)
        widget.setLayout(self.layout)
        widget.setStyleSheet("background-color: #26242f")
        self.setCentralWidget(widget)

        self.start()

    def create_scroll_layout(self):
        
        self.bottomlayout.deleteLater()
        self.scrollArea.deleteLater()
        self.contentwidget.deleteLater()
        self.scroll_layout.deleteLater()

        self.bottomlayout = QHBoxLayout()
        self.scrollArea = QScrollArea()
        self.contentwidget = QWidget()
        self.scroll_layout = QHBoxLayout()
        self.contentwidget.setLayout(self.scroll_layout)
        
        self.scrollArea.setWidget(self.contentwidget)
        self.scrollArea.setFixedHeight(160)
        self.scrollArea.setWidgetResizable(True)

        self.bottomlayout.addWidget(self.scrollArea)
        self.layout.addLayout(self.bottomlayout)
    
    def clear_scroll_layout(self):
        
        self.bottomlayout.deleteLater()
        self.scrollArea.deleteLater()
        self.contentwidget.deleteLater()
        self.scroll_layout.deleteLater()

        self.bottomlayout = QHBoxLayout()
        self.scrollArea = QScrollArea()
        self.contentwidget = QWidget()
        self.scroll_layout = QHBoxLayout()
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
            self.progressDialog = QProgressDialog("Loading Images..", None, 0, data[2], self)
            self.progressDialog.setWindowTitle(" ")
            self.slabel.setStyleSheet("border: 5px solid green;")
        self.contentwidget.layout().addWidget(self.slabel)
        self.prog_update(data[1])

    def prog_update(self,frame):
        if self.scrollth.isRunning():
            self.table.setDisabled(1)
            self.progressDialog.setValue(frame)
            self.progressDialog.show()
        else:
            self.table.setEnabled(1)
            self.progressDialog.hide()
           
if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec())