# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import os
import sys
import time

import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot,QAbstractTableModel, QPoint, QRect, QSize
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QScreen
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget,QTableView,QTableWidget,
                               QScrollArea,QFrame, QTableWidgetItem,QProgressDialog,QRubberBand)


class ScrollThread(QThread):
    updatescroll = Signal(list)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.image_source = None
        self.status = True
        self.cap = True
        
        
    # @Slot(str)
    def set_file(self, fname):
        # The data comes with the 'opencv-python' module
        self.image_source =  fname.text()
        

    def run(self):
        
        cap = cv2.VideoCapture(self.image_source)
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        
        # for i in range(30):
        for i in range(int(total_frames)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()

            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # cv2.putText(frame,"frame #"+str(i+1),(75,75),cv2.FONT_HERSHEY_COMPLEX,4,(255,255,255),6)
                frame = cv2.resize(frame,(160,120))

                h, w, ch = frame.shape
                img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                self.updatescroll.emit([img,i])
                
            else:
                self.quit()
        self.quit()
                    

                    

class Thread(QThread):
    updateFrame = Signal(QImage)
    

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.image_source = None
        self.status = True
        self.cap = True
        
        
    # @Slot(str)
    def set_file(self, fname,frame_no):
        self.image_source =  fname.text()
        self.frame_no = int(frame_no)
        

    def run(self):
        while True:
            self.status = True
            
            if self.image_source != None:

                source = self.image_source
                self.cap = cv2.VideoCapture(source)
                
                while self.status:
                    if self.image_source != None and self.image_source != source:
                        self.status = False

                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_no)
                    ret, frame = self.cap.read()
                    if not ret:
                        continue

                    # # Reading the image in RGB to display it
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame,(640,480))

                    # # Creating and scaling QImage
                    h, w, ch = frame.shape
                    img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                    # scaled_img = img.scaled(640, 480, Qt.KeepAspectRatio)
                    
                    # Emit signal
                    self.updateFrame.emit(img)
                # sys.exit(-1)
            else:
                pass
           
            



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

        self.origin = QPoint(event.position().x(),event.position().y())
        print(self.origin)
        self.rubberBand = None
        if not self.rubberBand:
            self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):

        self.rubberBand.setGeometry(QRect(self.origin, QPoint(event.position().x(),event.position().y())))

    def mouseReleaseEvent(self, event):

        self.rubberBand.hide()
        # determine selection, for example using QRect::intersects()
        # and QRect::contains().

    def __init__(self):
        # super().__init__()
        super(Window, self).__init__()
        self.setWindowTitle("Vision Explorer")
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.active_widget = None
        
        # self.showFullScreen()
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
        self.label.setFixedSize(640, 480)
        self.label.setStyleSheet("background-color:black")
        self.label.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.label.installEventFilter(self)

        self.poslabel = QLabel(self)
        self.poslabel.setAlignment(Qt.AlignCenter)
        self.poslabel.setStyleSheet("color:white")

        # Thread in charge of updating the image
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
        if self.table.item(0,0).text().lower().endswith('.mp4'):
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
            self.slabel.setStyleSheet("border: 5px solid green;")
        self.contentwidget.layout().addWidget(self.slabel)
        
if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec())