import sys
import os
import time
from functools import partial
import datetime
from MainScreenThread import Thread
from PlaybackScreenThread import ScrollThread
from LiveRecordThread import LiveRecord
from findDevices import OAK_USB_Devices, Webcam_Devices, Load_Device_Thread
from PySide6.QtCore import Qt, QThread, Signal, Slot,QAbstractTableModel, QPoint, QRect, QSize, QTimer
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QScreen, QPainter, QFontMetrics, QIcon
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget,QTableView,QTableWidget,
                               QScrollArea,QFrame, QTableWidgetItem,QProgressDialog,QRubberBand,QAbstractItemView, QStyle, QSlider, QToolBar, QFileDialog,QMessageBox)
#https://icons8.com
#                    
class Window(QMainWindow):
    def eventFilter(self, object, event):
        if str(event.type()) == 'Type.HoverMove': 
            if self.active_widget is not None:
                self.curpos = QPoint(event.position().x(),event.position().y()).toTuple()
                self.poslabel.setText("Frame #"+self.active_widget.objectName()+"  "+"Cursor Position (x,y): "+str(self.curpos))
                return True

            elif self.active_widget is None:
                self.curpos = QPoint(event.position().x(),event.position().y()).toTuple()
                self.poslabel.setText("Cursor Position (x,y): "+str(self.curpos))
                return True

        elif str(event.type()) == 'Type.HoverLeave':
            self.poslabel.setText("")
            return True
        else:
            return False

    def mouseDoubleClickEvent(self, event):
        # print(self.table.item(0,0).text())
        # if self.pause.isEnabled() or self.master_mode == 'live' or self.table.item(0,0).text().lower().endswith(self.mixed_formats) or not os.path.isdir(self.table.item(0,0).text()):
            
        #     return

        if self.table.item(0,0).text().lower().endswith(self.mixed_formats) or os.path.isdir(self.table.item(0,0).text()):
            widget = self.childAt(event.position().x(),event.position().y())
            widgets = self.contentwidget.findChildren(QLabel)

            if self.pause.isEnabled():
                return
            
            elif widget is not None and widget.objectName() and not self.pause.isEnabled():
                self.playback_mode = 'idle'
                self.active_widget = widget
                self.th.set_file(self.table.item(0,0),widget.objectName(),self.master_mode)
                widget.setStyleSheet("border: 5px solid green;")
                for w in widgets:
                    if w.objectName():
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
    def enableWindow(self):
        self.window().setDisabled(0)

    def enableLiveMode(self):
        if self.master_mode == 'offline':
            self.record.setEnabled(1)
            self.master_mode = 'live'
            self.mode_label.setText('Live')
            self.mode_label.setStyleSheet('color:green')
            self.th.set_file(self.table.item(0,0),0,self.master_mode)
            self.window().setDisabled(1)
            QTimer.singleShot(5000,self.enableWindow)
            self.table.setDisabled(1)
            self.menu_device.setDisabled(1)
            self.fpslabel.setText(" ")
            
            
        elif self.master_mode == 'live':
            self.record.setEnabled(0)
            self.master_mode = 'offline'
            self.mode_label.setText('Offline')
            self.mode_label.setStyleSheet('color:red')
            self.th.set_file(self.table.item(0,0),0,self.master_mode)
            self.window().setDisabled(1)
            QTimer.singleShot(5000,self.enableWindow)
            self.table.setDisabled(0)
            self.menu_device.setDisabled(0)
            self.ave_fps = []
            self.fpslabel.setText(" ")

    def web_found(self):
        self.table.setItem(0,0,QTableWidgetItem('0'))


    def oak_found(self,checked):
        action = self.sender()
        cam = action.text()
        
        if cam == 'Color Camera':
           self.table.setItem(0,0,QTableWidgetItem('1'))
        elif cam == 'Mono Left Camera':
            self.table.setItem(0,0,QTableWidgetItem('2'))
        elif cam == 'Mono Right Camera':
            self.table.setItem(0,0,QTableWidgetItem('3'))
        elif cam == 'Stereo':
            self.table.setItem(0,0,QTableWidgetItem('4'))

    def show_progress(self):
        if hasattr(self,'dev_dlg'):
            self.dev_dlg.deleteLater()
            self.dev_dlg = QProgressDialog("Searching for Devices..", None, 0, 0, self)
            self.dev_dlg.show()
            print('show')
        else:
            self.dev_dlg = QProgressDialog("Searching for Devices..", None, 0, 0, self)
            self.dev_dlg.show()
       
            print('show')
        
    
    
    def update_progress(self,value):
        self.dev_dlg.hide()

        print('delete')

    @Slot()
    def getDeviceData(self):
        self.deviceth.updateDevices.connect(self.refresh_devices)

        
        self.deviceth.terminate()
        time.sleep(1)

    def run_deviceth(self):
        # self.deviceth.loaded.connect(self.update_progress)
        self.deviceth.finished.connect(self.getDeviceData)
        self.deviceth.started.connect(self.show_progress)
        self.deviceth.loaded.connect(self.update_progress)
        self.deviceth.start()
        print('started')
        
        # self.dev_dlg.show()
        # self.dev_update()
       
        
    @Slot()
    def refresh_devices(self,data):
        # self.deviceth.terminate()
        self.menu_device.clear()
        # self.deviceth.quit()
        if hasattr(self,'webcam_action'):
            self.webcam_action.deleteLater()
        if hasattr(self,'oak_sub'):
            self.oak_sub.deleteLater()
        self.webcam = data[0]
        self.oak = data[1]
        if self.webcam:
            self.webcam_action = QAction("Webcam")
            self.webcam_action.triggered.connect(self.web_found)
            self.menu_device.addAction(self.webcam_action)
            self.menu_device.addSeparator()
        
        if self.oak is not None:
            for device in self.oak:
                mxId, cams = list(device.items())[0]
                self.oak_sub = self.menu_device.addMenu("OAK Camera: "+str(mxId))
                self.menu_device.addSeparator()
                for cam in cams:
                    self.cam_action = QAction(cam,self)
                    self.cam_action.triggered.connect(self.oak_found)
                    self.oak_sub.addAction(self.cam_action)
                
        
        self.refresh_action = QAction("Refresh Available Devices")
        self.refresh_action.triggered.connect(self.run_deviceth)
        self.menu_device.addAction(self.refresh_action)
        
        if hasattr(self,'dev_dlg'):
            self.dev_dlg.hide()
        

    def __init__(self):
        # super().__init__()
        super(Window, self).__init__()
        self.setWindowTitle("Vision Explorer")
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.active_widget = None
        self.playback_mode = 'idle'
        self.rubberBand = None
        self.fps = None
        self.ave_fps = []
        self.total_frames = None
        self.frame_rate = 1
        self.recording = False
        self.image_dir = None
        self.master_mode = 'offline'
        self.saveTimer = QTimer()
        self.img_formats = ('.jpg','.bmp','.jpe','.jpeg','.tif','.tiff')
        self.vid_formats = ('.mp4','.avi','.mov','.wmv')
        self.mixed_formats = ('.mp4','.avi','.mov','.wmv','.jpg','.bmp','.jpe','.jpeg','.tif','.tiff')
        
        self.webcam = Webcam_Devices()
        self.oak = OAK_USB_Devices()
        # self.webcam = None
        # self.oak = None


        screenGeometry = QScreen.availableGeometry(QApplication.primaryScreen())
        self.setGeometry(screenGeometry)
        self.showMaximized()

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16,16))
        self.addToolBar(self.toolbar)

        self.mode_button = QAction(QIcon('assets/play2.png'),'&Mode',self)
        self.mode_button.setStatusTip("Enable/Disable Live Mode")
        self.mode_button.triggered.connect(self.enableLiveMode)
        self.toolbar.addAction(self.mode_button)
        
        
        self.mode_label = QLabel('Offline')
        self.mode_label.setStyleSheet('color:red')
        self.toolbar.addWidget(self.mode_label)
        self.mode_button.setDisabled(1)


        # Create a label for the display camera
        self.label = QLabel(self)
        self.label.setObjectName('MainScreen')
        self.label.setFixedSize(720, 480)
        self.label.setStyleSheet("background-color:black")
        self.label.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.label.installEventFilter(self)

        self.poslabel = QLabel(self)
        self.poslabel.setAlignment(Qt.AlignCenter)
        self.poslabel.setStyleSheet("color:white")

        self.fpslabel = QLabel(self)
        self.fpslabel.setAlignment(Qt.AlignRight)
        self.fpslabel.setStyleSheet("color:white")

        self.th = Thread(self)
        self.th.updateFrame.connect(self.setImage)

        self.scrollth = ScrollThread(self)
        self.scrollth.updatescroll.connect(self.setScrollImage)
        
        # Main layout
        toplayout = QHBoxLayout()
        leftlayout = QVBoxLayout()
        leftlayout.addWidget(self.label)
        leftlayout.addWidget(self.poslabel)
        leftlayout.setContentsMargins(75,0,0,0)
        leftlayout.setSpacing(5)
        leftlayout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        
        rightlayout = QVBoxLayout()
        self.table = QTableWidget(100, 100, self)
        self.table.cellChanged.connect(self.set_source)
        self.table.setStyleSheet("background-color:white")
        rightlayout.addWidget(self.table)
        rightlayout.addWidget(self.fpslabel)
        # rightlayout.setContentsMargins(75,0,0,0)
        rightlayout.setSpacing(5)
        rightlayout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

        toplayout.addLayout(leftlayout)
        toplayout.addLayout(rightlayout)
        toplayout.setSpacing(75)

        self.bottomlayout = QHBoxLayout()
        self.scrollArea = QScrollArea()
        self.contentwidget = QWidget()
        self.pb_widget = QWidget()
        self.scroll_layout = QHBoxLayout()
        self.playback_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.layout = QVBoxLayout()
        self.layout.addLayout(toplayout)

        self.create_scroll_layout()
        
                # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=qApp.quit)
        self.menu_file.addAction(exit)

        self.menu_device = self.menu.addMenu("Devices")
        self.deviceth = Load_Device_Thread(self)
        self.refresh_devices([self.webcam,self.oak])
        # self.deviceth.finished.connect(lambda:self.refresh_devices([self.webcam,self.oak]))
        # self.deviceth.start()
        # self.run_deviceth()
        # if self.webcam:
        #     self.webcam_action = QAction("Webcam")
        #     self.webcam_action.triggered.connect(self.web_found)
        #     self.menu_device.addAction(self.webcam_action)
        #     self.menu_device.addSeparator()
        
        # if self.oak is not None:
        #     self.oak_sub = self.menu_device.addMenu("OAK Camera: "+self.oak[0])
        #     self.menu_device.addSeparator()
        #     for cam in self.oak[1]:
        #         self.cam_action = QAction(cam,self)
        #         self.cam_action.triggered.connect(self.oak_found)
        #         self.oak_sub.addAction(self.cam_action)
        #         self.oak_sub.addSeparator()
        
        # self.refresh_action = QAction("Refresh Available Devices")
        # self.refresh_action.triggered.connect(self.refresh_devices)
        # self.menu_device.addAction(self.refresh_action)




        # self.menu_about = self.menu.addMenu("&About")
        # about = QAction("About Qt", self, shortcut=QKeySequence(QKeySequence.HelpContents),
        #                 triggered=qApp.aboutQt)
        # self.menu_about.addAction(about)

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
                        border: 1px solid gray;\
                        height: 8px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */\
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);\
                        margin: 2px 0;\
                        }\
                        QSlider::handle:horizontal {\
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);\
                            border: 1px solid black;\
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
        self.pb_widget.deleteLater()

        self.bottomlayout = QHBoxLayout()
        self.scrollArea = QScrollArea()
        self.contentwidget = QWidget()
        self.pb_widget = QWidget()
        self.scroll_layout = QHBoxLayout()
        self.playback_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.pb_title = QLabel()
        self.pb_title.setText("Frame Review")
        self.pb_title.setMaximumWidth(250)
        self.pb_title.setMaximumHeight(10)
        self.pb_title.setAlignment(Qt.AlignCenter)
        self.pb_title.setStyleSheet("color:gray;font-weight:bold")

        self.play = QPushButton()
        self.play.setIcon(QIcon('assets/play2.png'))
        self.play.setCheckable(False)
        self.play.setDisabled(True)
        self.play.setStyleSheet(button_style)
        self.play.clicked.connect(lambda:self.playButtonClicked(int(self.active_widget.objectName())))

        self.pause = QPushButton()
        self.pause.setIcon(QIcon('assets/pause2.png'))
        self.pause.setCheckable(False)
        self.pause.setDisabled(True)
        self.pause.setStyleSheet(button_style)
        self.pause.clicked.connect(lambda:self.pauseButtonClicked())

        self.rewind = QPushButton()
        self.rewind.setIcon(QIcon('assets/rewind2.png'))
        self.rewind.setCheckable(False)
        self.rewind.setDisabled(True)
        self.rewind.setStyleSheet(button_style)
        self.rewind.clicked.connect(lambda:self.rewindButtonClicked(int(self.active_widget.objectName())))

        self.record = QPushButton()
        self.record.setIcon(QIcon('assets/record2.png'))
        self.record.setCheckable(False)
        self.record.setDisabled(True)
        self.record.setStyleSheet(button_style)
        self.record.clicked.connect(lambda:self.recordButtonClicked())

        self.delay = QSlider(Qt.Horizontal)
        self.delay.setStyleSheet(delay_style)
        self.delay.setRange(1,50)
        self.delay.setSliderPosition(self.frame_rate)
        self.delay.setSingleStep(1)
        self.delay.setMaximumWidth(275)
        self.delay.sliderMoved.connect(self.slider_position)

        self.fr_display = QLabel()
        self.fr_display.setText("Frame Delay: "+str(int(1000/self.frame_rate))+" ms")
        self.fr_display.setMaximumWidth(275)
        self.fr_display.setMaximumHeight(10)
        self.fr_display.setAlignment(Qt.AlignCenter)
        self.fr_display.setStyleSheet("color:gray;font-weight:bold")

        self.contentwidget.setLayout(self.scroll_layout)
        self.pb_widget.setObjectName("pbwidget")
        self.pb_widget.setLayout(self.playback_layout)
        self.pb_widget.setFixedHeight(160)
        self.pb_widget.setFixedWidth(275)
        self.pb_widget.setStyleSheet("QWidget#pbwidget {border:1px solid white}")
        
        self.scrollArea.setObjectName("scrollarea")
        self.scrollArea.setWidget(self.contentwidget)
        self.scrollArea.setFixedHeight(160)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("QWidget#scrollarea {border:1px solid white}")
        
        self.button_layout.addWidget(self.rewind)
        self.button_layout.addWidget(self.pause)
        self.button_layout.addWidget(self.play)
        self.button_layout.addWidget(self.record)

        self.playback_layout.addWidget(self.pb_title)
        self.playback_layout.addLayout(self.button_layout)
        self.playback_layout.addWidget(self.delay)
        self.playback_layout.addWidget(self.fr_display)

        self.bottomlayout.addWidget(self.pb_widget)
        self.bottomlayout.addWidget(self.scrollArea)
        self.layout.addLayout(self.bottomlayout)
    
    def clear_scroll_layout(self):
        
        self.bottomlayout.deleteLater()
        self.scrollArea.deleteLater()
        self.contentwidget.deleteLater()
        self.scroll_layout.deleteLater()
        self.playback_layout.deleteLater()
        self.button_layout.deleteLater()
        self.pb_title.deleteLater()
        self.play.deleteLater()
        self.pause.deleteLater()
        self.rewind.deleteLater()
        self.record.deleteLater()
        self.delay.deleteLater()
        self.fr_display.deleteLater()
        self.pb_widget.deleteLater()

        self.bottomlayout = QHBoxLayout()
        self.scrollArea = QScrollArea()
        self.contentwidget = QWidget()
        self.pb_widget = QWidget()
        self.scroll_layout = QHBoxLayout()
        self.playback_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.pb_title = QLabel()
        self.play = QPushButton()
        self.play.setCheckable(True)
        self.pause = QPushButton()
        self.pause.setCheckable(True)
        self.rewind = QPushButton()
        self.rewind.setCheckable(True)
        self.record = QPushButton()
        self.record.setCheckable(True)
        self.delay = QSlider(Qt.Horizontal)
        self.delay.setSliderPosition(self.frame_rate)
        self.fr_display = QLabel()
        self.contentwidget.setLayout(self.scroll_layout)
        self.pb_widget.setLayout(self.playback_layout)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() and not self.scrollth.isRunning() and self.master_mode != 'live':
            e.accept()
        else:
            e.ignore()


    def dropEvent(self, e):
        if e.mimeData().hasUrls() and not self.scrollth.isRunning() and self.master_mode != 'live':
            e.accept()
            urls = e.mimeData().urls()

            for url in urls:
                fname = url.toLocalFile()
                self.table.setItem(0,0,QTableWidgetItem(fname))  
        else:
            e.ignore()

    def slider_position(self,p):
        self.frame_rate = p
        self.fr_display.setText("Frame Delay: "+str(int(1000/self.frame_rate))+" ms")

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
            self.th.set_file(self.table.item(0,0),0,self.master_mode)

            
        if self.table.item(0,0).text().lower().endswith(self.vid_formats) or os.path.isdir(self.table.item(0,0).text()):
            self.active_widget = None
            self.mode_button.setDisabled(1)
            self.scrollth.quit()
            time.sleep(1)
            self.create_scroll_layout()
            self.scrollth.start()
            self.scrollth.set_file(self.table.item(0,0))
                
        else:
            self.active_widget = None
            self.mode_button.setDisabled(0)
            self.scrollth.quit()
            time.sleep(1)
            self.clear_scroll_layout()
            self.create_scroll_layout()
            self.record.setEnabled(0)
    
    def calc_ave_fps(self,fps):
        self.ave_fps.append(fps)
        if len(self.ave_fps) == 100:
            self.ave_fps.pop(0)

        if len(self.ave_fps) > 1:
            ave = sum(self.ave_fps)/len(self.ave_fps)
            return (ave)
        else:
            return(None)


    @Slot(QImage)
    def setImage(self, data):
        self.label.setPixmap(QPixmap.fromImage(data[0]))
        self.fps = data[1]
        if self.fps is not None and self.fps !=0:
            ave_fps = self.calc_ave_fps(self.fps)
            if ave_fps is not None:
                self.fpslabel.setText(str(round(ave_fps,1))+" ms")
            else:
                self.fpslabel.setText(" ")
        
    @Slot(QImage)
    def setScrollImage(self,data):
        if self.master_mode == 'offline':      
            self.slabel=QLabel()
            self.flabel = VerticalLabel()
            self.flabel.setStyleSheet("color:white;font-weight:bold")
            self.flabel.setText("Frame " +str(data[1]))
            self.slabel.setObjectName(str(data[1]))
            self.slabel.setFixedSize(160, 120)
            self.slabel.setPixmap(QPixmap.fromImage(data[0]))
            if self.slabel.objectName() == '0':
                self.active_widget = self.slabel
                self.progressDialog = QProgressDialog("Loading Images..", None, 0, data[2], self)
                self.progressDialog.setWindowTitle(" ")
                self.slabel.setStyleSheet("border: 5px solid green;")
            self.contentwidget.layout().addWidget(self.flabel)
            self.contentwidget.layout().addWidget(self.slabel)
            self.prog_update(data[1])
            self.total_frames = data[2]
        
        elif self.master_mode == 'live':
            self.rlabel=QLabel()
            self.zlabel = VerticalLabel()
            self.zlabel.setStyleSheet("color:white;font-weight:bold")
            self.zlabel.setText("Frame " +str(data[1]))
            self.rlabel.setObjectName("liverecord"+str(data[1]))
            self.rlabel.setFixedSize(160, 120)
            self.rlabel.setPixmap(data[0])
            self.contentwidget.layout().addWidget(self.zlabel)
            self.contentwidget.layout().addWidget(self.rlabel)
            
            self.active_widget = self.findChild(QWidget,"liverecord"+str(data[1]))
            self.active_widget.setStyleSheet("border: 5px solid green;")
            widgets = self.contentwidget.findChildren(QLabel)
            for w in widgets:
                if w.objectName():
                    if w.objectName() != self.active_widget.objectName():
                        w.setStyleSheet("border:0px solid black")
            qApp.processEvents()
            QTimer.singleShot(0,partial(self.scrollArea.ensureWidgetVisible,self.active_widget))



    def prog_update(self,frame):
        if self.scrollth.isRunning():
            self.table.setDisabled(1)
            self.play.setDisabled(1)
            self.pause.setDisabled(1)
            self.rewind.setDisabled(1)
            self.record.setDisabled(1)
            self.progressDialog.setValue(frame)
            self.progressDialog.show()
        else:
            self.play.setEnabled(1)
            self.pause.setEnabled(0)
            self.record.setEnabled(1)
            self.table.setEnabled(1)
            self.progressDialog.hide()

    def playButtonClicked(self,i):
        i+=1
        self.play.setDisabled(1)
        self.play.setCheckable(0)
        self.th.set_file(self.table.item(0,0),i,self.master_mode)
        self.active_widget = self.findChild(QWidget,str(i))
        self.active_widget.setStyleSheet("border: 5px solid green;")
        self.scrollArea.ensureWidgetVisible(self.active_widget)
        widgets = self.contentwidget.findChildren(QLabel)
        for w in widgets:
            if w.objectName():
                if w.objectName() != self.active_widget.objectName():
                    w.setStyleSheet("border:0px solid black")
                
        if self.playback_mode == 'paused':
            self.play.setDisabled(0)
            self.play.setCheckable(1)
            self.rewind.setDisabled(0)
            self.rewind.setCheckable(1)
            self.table.setDisabled(0)
            self.playback_mode = 'playing'

        else:
            if i < self.total_frames-1:
                self.playback_mode = 'playing'
                self.pause.setDisabled(0)
                self.pause.setCheckable(1)
                self.table.setDisabled(1)
                QTimer.singleShot(int(1000/self.frame_rate), lambda:self.playButtonClicked(i))
                if self.recording:
                    self.saveImages(self.image_dir,i)

            elif i == self.total_frames-1:
                self.play.setDisabled(1)
                self.play.setCheckable(0)
                self.pause.setDisabled(1)
                self.pause.setCheckable(0)
                self.table.setDisabled(0)
                self.playback_mode == 'idle'
            else:
                self.play.setDisabled(0)
                self.play.setCheckable(1)
                self.table.setDisabled(0)
                self.playback_mode == 'idle'

    def rewindButtonClicked(self,i):
        i-=1
        self.rewind.setDisabled(1)
        self.rewind.setCheckable(0)
        self.th.set_file(self.table.item(0,0),i,self.master_mode)
        self.active_widget = self.findChild(QWidget,str(i))
        self.active_widget.setStyleSheet("border: 5px solid green;")
        self.scrollArea.ensureWidgetVisible(self.active_widget)
        widgets = self.contentwidget.findChildren(QLabel)
        for w in widgets:
            if w.objectName():
                if w.objectName() != self.active_widget.objectName():
                    w.setStyleSheet("border:0px solid black")
                
        if self.playback_mode == 'paused':
            self.rewind.setDisabled(0)
            self.rewind.setCheckable(1)
            self.play.setDisabled(0)
            self.play.setCheckable(1)
            self.table.setDisabled(0)
            self.playback_mode = 'rewind'

        else:
            if i > 0:
                self.playback_mode = 'rewind'
                self.pause.setDisabled(0)
                self.pause.setCheckable(1)
                self.table.setDisabled(1)
                QTimer.singleShot(int(1000/self.frame_rate), lambda:self.rewindButtonClicked(i))
                if self.recording:
                    self.saveImages(self.image_dir,i)

            elif i == 0:
                self.rewind.setDisabled(1)
                self.rewind.setCheckable(0)
                self.pause.setDisabled(1)
                self.pause.setCheckable(0)
                self.table.setDisabled(0)
                self.playback_mode == 'idle'
            else:
                self.rewind.setDisabled(0)
                self.rewind.setCheckable(1)
                self.table.setDisabled(0)
                self.playback_mode == 'idle'

    def pauseButtonClicked(self):
        self.pause.setDisabled(1)
        self.pause.setCheckable(0)
        self.th.set_file(self.table.item(0,0),int(self.active_widget.objectName()),self.master_mode)
        widgets = self.contentwidget.findChildren(QLabel)
        self.active_widget.setStyleSheet("border: 5px solid green;")
        self.scrollArea.ensureWidgetVisible(self.active_widget)
        self.table.setDisabled(0)
        for w in widgets:
            if w.objectName():
                if w.objectName() != self.active_widget.objectName():
                    w.setStyleSheet("border:0px solid black")
        self.playback_mode = 'paused'

    def saveImages(self,dir,i):
        self.label.pixmap().save(os.path.join(dir,'frame'+str(i)+'.jpg'))

    def pop_message(self):
        dlg = QMessageBox()
        dlg.setWindowTitle(" ")
        dlg.setText("Images saved to "+str(self.image_dir))
        dlg.show()

    def recordButtonClicked(self):
        if self.master_mode == 'live':
            if not self.saveTimer.isActive():
                # write video
                self.mode_button.setDisabled(1)
                self.record.setStyleSheet("background-color:red")
                self.image_dir = QFileDialog.getExistingDirectory()
                self.saveTimer.start()
                self.th2 = LiveRecord(self)
                self.th2.updatescroll.connect(self.setScrollImage)
                self.th2.set_dir(self.label,self.image_dir,1/self.frame_rate)
                self.th2.active = True                                
                self.th2.start()

            else:
                # stop writing

                self.record.setStyleSheet("background-color:gray")
                self.saveTimer.stop()
                self.th2.active = False
                self.th2.quit()                                           
                self.th2.terminate()
                time.sleep(2)
                self.active_widget = None
                self.clear_scroll_layout()
                self.create_scroll_layout()
                self.mode_button.setDisabled(0)
                self.record.setDisabled(0)


                                
        
        elif self.master_mode == 'offline':
            if not self.recording:
                self.recording = True
                self.record.setStyleSheet("background-color:red")
                self.image_dir = QFileDialog.getExistingDirectory()
            else:
                self.recording = False
                self.record.setStyleSheet("background-color:gray")     

class VerticalLabel(QLabel):

    def __init__(self, *args):
        QLabel.__init__(self, *args)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(0, self.height())
        painter.rotate(-90)
        fm = QFontMetrics(painter.font())
        xoffset = int(fm.boundingRect(self.text()).width()/2)
        yoffset = int(fm.boundingRect(self.text()).height()/2)
        x = int(self.width()/2) + yoffset
        y = int(self.height()/2) - xoffset
        painter.drawText(y, x, self.text())
        painter.end()
        
    def minimumSizeHint(self):
        size = QLabel.minimumSizeHint(self)
        return QSize(size.height(), size.width())

    def sizeHint(self):
        size = QLabel.sizeHint(self)
        return QSize(size.height(), size.width())            
        

if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec())

