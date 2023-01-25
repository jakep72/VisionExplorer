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
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QScreen, QPainter, QFontMetrics, QIcon, QCursor, QPalette, QBrush, QColor, QPen, QTransform
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget,QTableView,QTableWidget,
                               QScrollArea,QFrame, QTableWidgetItem,QProgressDialog,QRubberBand,QAbstractItemView, QStyle, QSlider, QToolBar, QFileDialog,QMessageBox, QDockWidget, QToolTip, QGraphicsScene,QGraphicsView,QGraphicsPixmapItem, QSizeGrip)
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

    def popups(self,row,column):
        item = self.table.item(row,column)
        if item is not None:
            if item.text().lower() == 'edgetool':
                self.band = RectROI(self.label)
                self.band.move(360-75,240-32)
                self.band.resize(150,75)
        # print(item.text())

    def mouseDoubleClickEvent(self, event):
        if self.table.item(0,0).text().lower().endswith(self.mixed_formats) or os.path.isdir(self.table.item(0,0).text()):
            self.scale = 1.0
            self.label.resize(720,480)
            self.scaled_img = None
            widget = self.childAt(event.position().x(),event.position().y())
            widgets = self.contentwidget.findChildren(QLabel)

            if self.pause.isEnabled():
                return
            
            elif widget is not None and widget.objectName() and not self.pause.isEnabled():
                self.playback_mode = 'idle'
                self.active_widget = widget
                self.th.set_file(self.table.item(0,0),widget.objectName(),self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,None)
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
    #     else:
    #         return

    # def mouseMoveEvent(self, event):
    #     self.rubberBand.setGeometry(QRect(self.origin, QPoint(event.position().x(),event.position().y())))

    def enableWindow(self):
        self.window().setDisabled(0)

    def enableAutoExp(self):
        if self.auto_button.isChecked() == True:
            self.autoexp = False
            self.exp_slider.setDisabled(0)
            self.iso_slider.setDisabled(0)
            self.contrast_slider.setDisabled(0)
            self.saturation_slider.setDisabled(0)
            self.sharpness_slider.setDisabled(0)
            self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,None)
            self.auto_button.setStyleSheet('color:white; background-color:red')
            self.auto_button.setText('Off')
            
            
        elif self.auto_button.isChecked() == False:
            self.autoexp = True
            self.exp_slider.setDisabled(1)
            self.iso_slider.setDisabled(1)
            self.contrast_slider.setDisabled(1)
            self.saturation_slider.setDisabled(1)
            self.sharpness_slider.setDisabled(1)
            self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,'AutoOn')
            self.auto_button.setStyleSheet('color:white; background-color:green')
            self.auto_button.setText('On')


    def enableLiveMode(self):
        if self.master_mode == 'offline':
            self.record.setEnabled(1)
            self.master_mode = 'live'
            self.mode_label.setText('Live')
            self.mode_label.setStyleSheet('color:green')
            self.scaled_img = None
            self.scale = 1.0
            self.label.resize(720,480)
            self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,None)
            self.window().setDisabled(1)
            QTimer.singleShot(5000,self.enableWindow)
            self.table.setDisabled(1)
            self.menu_device.setDisabled(1)
            self.viewMenu.setDisabled(1)
            self.fpslabel.setText(" ")
            if self.oak is not None:
                self.auto_button.setDisabled(1)
                self.exp_slider.setDisabled(1)
                self.iso_slider.setDisabled(1)
                self.contrast_slider.setDisabled(1)
                self.saturation_slider.setDisabled(1)
                self.sharpness_slider.setDisabled(1)
            
            
        elif self.master_mode == 'live':
            self.record.setEnabled(0)
            self.master_mode = 'offline'
            self.mode_label.setText('Offline')
            self.mode_label.setStyleSheet('color:red')
            self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,None)
            self.window().setDisabled(1)
            QTimer.singleShot(5000,self.enableWindow)
            self.table.setDisabled(0)
            self.menu_device.setDisabled(0)
            self.viewMenu.setDisabled(0)
            self.ave_fps = []
            self.fpslabel.setText(" ")
            if self.oak is not None:
                self.auto_button.setDisabled(0)
                if self.autoexp == False:
                    self.exp_slider.setDisabled(0)
                    self.iso_slider.setDisabled(0)
                    self.contrast_slider.setDisabled(0)
                    self.saturation_slider.setDisabled(0)
                    self.sharpness_slider.setDisabled(0)
                else:
                    self.exp_slider.setDisabled(1)
                    self.iso_slider.setDisabled(1)
                    self.contrast_slider.setDisabled(1)
                    self.saturation_slider.setDisabled(1)
                    self.sharpness_slider.setDisabled(1)

    def web_found(self):
        self.table.setItem(0,0,QTableWidgetItem('Webcam'))


    def oak_found(self,checked):
        action = self.sender()
        cam = action.text()
        
        if cam == 'Color Camera':
           self.table.setItem(0,0,QTableWidgetItem(self.oak_sub.objectName()+"_"+"Color"))
        elif cam == 'Mono Left Camera':
            self.table.setItem(0,0,QTableWidgetItem(self.oak_sub.objectName()+"_"+"MonoLeft"))
        elif cam == 'Mono Right Camera':
            self.table.setItem(0,0,QTableWidgetItem(self.oak_sub.objectName()+"_"+"MonoRight"))
        elif cam == 'Stereo':
            self.table.setItem(0,0,QTableWidgetItem(self.oak_sub.objectName()+"_"+"Stereo"))

    def show_progress(self):
        self.dev_dlg = QProgressDialog("Searching for Devices..", None, 0, 0, self)
        self.dev_dlg.setWindowTitle(" ")
        self.dev_dlg.show()
    
    def update_progress(self,value):
        self.dev_dlg.hide()

    def run_deviceth(self):
        self.deviceth.start()
        
    def refresh_devices(self,data):
        self.menu_device.clear()
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
                self.oak_sub.setObjectName(mxId)
                self.menu_device.addSeparator()
                for cam in cams:
                    self.cam_action = QAction(cam,self)
                    self.cam_action.triggered.connect(self.oak_found)
                    self.oak_sub.addAction(self.cam_action)
                
        
        self.refresh_action = QAction("Refresh Available Devices")
        self.refresh_action.triggered.connect(self.run_deviceth)
        self.menu_device.addAction(self.refresh_action)
        self.deviceth.quit()
        

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
        self.scale = 1.0
        self.scaled_img = None
        self.oak = None
        self.source = None
        self.saveTimer = QTimer()
        self.img_formats = ('.jpg','.bmp','.jpe','.jpeg','.tif','.tiff')
        self.vid_formats = ('.mp4','.avi','.mov','.wmv')
        self.mixed_formats = ('.mp4','.avi','.mov','.wmv','.jpg','.bmp','.jpe','.jpeg','.tif','.tiff')

        
        self.autoexp = True
        self.focus = 150
        self.exposure = 20000
        self.iso = 100
        self.brightness = 0 #-10 to 10
        self.contrast = 0
        self.saturation = 0
        self.sharpness = 0 #0-4


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
        self.label.resize(720,480)
        self.label.setStyleSheet("background-color:black")
        self.label.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.label.installEventFilter(self)

        

        self.mainscroll = QScrollArea()
        # self.mainscroll.resize(725,485
        self.mainscroll.setStyleSheet("background-color:black")
        self.mainscroll.setFixedSize(725,485)
        self.mainscroll.setWidget(self.label)
        self.mainscroll.setVisible(True)

        self.poslabel = QLabel(self)
        self.poslabel.setFixedHeight(15)
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
        leftlayout.addWidget(self.mainscroll)
        leftlayout.addWidget(self.poslabel)
        leftlayout.setContentsMargins(75,0,0,0)
        leftlayout.setSpacing(5)
        leftlayout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        
        rightlayout = QVBoxLayout()
        self.table = QTableWidget(100, 100, self)
        self.table.cellChanged.connect(self.set_source)
        self.table.cellDoubleClicked.connect(self.popups)
        self.table.setStyleSheet("background-color:white")
       
        rightlayout.addWidget(self.table)
        rightlayout.addWidget(self.fpslabel)
        rightlayout.setStretch(100,100)
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
        self.camcontrol_layout = QHBoxLayout()
        self.camcontrolwidget = QWidget()

        self.layout = QVBoxLayout()
        self.layout.addLayout(toplayout)

        self.create_scroll_layout()
        
        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=qApp.quit)
        self.menu_file.addAction(exit)

        self.viewMenu = self.menu.addMenu("View")
        self.viewMenu.addAction(QAction("Zoom &In", self, shortcut="Ctrl++", enabled=True, triggered=self.zoomIn))
        self.viewMenu.addAction(QAction("Zoom &Out", self, shortcut="Ctrl+-", enabled=True, triggered=self.zoomOut))
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(QAction("&Fit to Window", self, enabled=True, shortcut="Ctrl+F",triggered=self.fitToWindow))

        self.menu_device = self.menu.addMenu("Devices")
        self.deviceth = Load_Device_Thread(self)
        self.deviceth.updateDevices.connect(self.refresh_devices)
        self.deviceth.started.connect(self.show_progress)
        self.deviceth.loaded.connect(self.update_progress)
        
        self.refresh_action = QAction("Search for Available Devices")
        self.refresh_action.triggered.connect(self.run_deviceth)
        self.menu_device.addAction(self.refresh_action)

        self.toolbox = QDockWidget()
        self.toolbox.setStyleSheet("color:white; background-color: #26242f")
        self.toolbox.setWindowTitle("Toolbox")
        self.toolbox.setFloating(False)
        self.toolbox.setAllowedAreas(Qt.RightDockWidgetArea)
        self.toolbox_widget = QWidget()
        self.toolbox.setWidget(self.toolbox_widget)
        self.toolbox_widget.setLayout(QVBoxLayout())
        self.toolbox_widget.setStyleSheet("color:white; background-color: #26242f")



        self.findline = QPushButton("Edges")
        self.findline.clicked.connect(lambda:self.place_findline())
        self.toolbox_widget.layout().addWidget(self.findline)

        self.addDockWidget(Qt.RightDockWidgetArea,self.toolbox)

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
        self.fr_layout = QHBoxLayout()


        self.pb_title = QLabel()
        self.pb_title.setText("Frame Review")
        self.pb_title.setMaximumWidth(250)
        self.pb_title.setMaximumHeight(15)
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
        self.fr_display.setText("Frame Delay: ")
        self.fr_display.setAlignment(Qt.AlignCenter)
        self.fr_display.setStyleSheet("color:gray;font-weight:bold")

        self.contentwidget.setLayout(self.scroll_layout)
        self.pb_widget.setObjectName("pbwidget")
        self.pb_widget.setLayout(self.playback_layout)
        self.pb_widget.setFixedHeight(175)
        self.pb_widget.setFixedWidth(275)
        self.pb_widget.setStyleSheet("QWidget#pbwidget {border:1px solid white}")
        
        self.scrollArea.setObjectName("scrollarea")
        self.scrollArea.setWidget(self.contentwidget)
        self.scrollArea.setFixedHeight(175)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("QWidget#scrollarea {border:1px solid white}")
        
        self.button_layout.addWidget(self.rewind)
        self.button_layout.addWidget(self.pause)
        self.button_layout.addWidget(self.play)
        self.button_layout.addWidget(self.record)

        self.fr_layout.addWidget(self.fr_display)
        self.fr_layout.addWidget(self.delay)

        self.playback_layout.addWidget(self.pb_title)
        self.playback_layout.addLayout(self.button_layout)
        self.playback_layout.addLayout(self.fr_layout)

        
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

    def make_cam_control_display(self):
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

        self.camcontrol_layout.deleteLater()
        self.camcontrolwidget.deleteLater()

        self.camcontrol_layout = QVBoxLayout()
        self.camcontrolwidget = QWidget()
        self.exp_layout = QHBoxLayout()
        self.iso_layout = QHBoxLayout()
        self.auto_layout = QHBoxLayout()
        self.contrast_layout = QHBoxLayout()
        self.saturation_layout = QHBoxLayout()
        self.sharpness_layout = QHBoxLayout()

        self.camcontrol_title = QLabel()
        self.camcontrol_title.setText("OAK Camera Settings")
        self.camcontrol_title.setMaximumWidth(250)
        self.camcontrol_title.setMaximumHeight(15)
        self.camcontrol_title.setAlignment(Qt.AlignCenter)
        self.camcontrol_title.setStyleSheet("color:gray;font-weight:bold")

        self.auto_title = QLabel()
        self.auto_title.setText("Auto: ")
        self.auto_title.setAlignment(Qt.AlignLeft)
        self.auto_title.setStyleSheet("color:gray;font-weight:bold")

        self.auto_button = QPushButton()
        self.auto_button.setCheckable(True)
        self.auto_button.setText('On')
        self.auto_button.setFixedWidth(160)
        self.auto_button.setFixedHeight(15)
        self.auto_button.setStyleSheet("color:white; background-color:green")
        self.auto_button.clicked.connect(self.enableAutoExp)


        self.exp_title = QLabel()
        self.exp_title.setText("Exposure: ")
        self.exp_title.setAlignment(Qt.AlignLeft)
        self.exp_title.setStyleSheet("color:gray;font-weight:bold")


        self.exp_slider = QSlider(Qt.Horizontal)
        self.exp_slider.setStyleSheet(delay_style)
        self.exp_slider.setRange(100,30000)
        self.exp_slider.setSliderPosition(self.exposure)
        self.exp_slider.setSingleStep(500)
        self.exp_slider.setMaximumWidth(160)
        self.exp_slider.setDisabled(1)
        self.exp_slider.sliderReleased.connect(self.exp_position)

        self.iso_title = QLabel()
        self.iso_title.setText("ISO Sensitivity: ")
        self.iso_title.setAlignment(Qt.AlignLeft)
        self.iso_title.setStyleSheet("color:gray;font-weight:bold")


        self.iso_slider = QSlider(Qt.Horizontal)
        self.iso_slider.setStyleSheet(delay_style)
        self.iso_slider.setRange(100,1600)
        self.iso_slider.setSliderPosition(self.iso)
        self.iso_slider.setSingleStep(50)
        self.iso_slider.setMaximumWidth(160)
        self.iso_slider.setDisabled(1)
        self.iso_slider.sliderReleased.connect(self.iso_position)

        self.contrast_title = QLabel()
        self.contrast_title.setText("Contrast: ")
        self.contrast_title.setAlignment(Qt.AlignLeft)
        self.contrast_title.setStyleSheet("color:gray;font-weight:bold")


        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setStyleSheet(delay_style)
        self.contrast_slider.setRange(-10,10)
        self.contrast_slider.setSliderPosition(self.contrast)
        self.contrast_slider.setSingleStep(1)
        self.contrast_slider.setMaximumWidth(160)
        self.contrast_slider.setDisabled(1)
        self.contrast_slider.sliderReleased.connect(self.contrast_position)

        self.saturation_title = QLabel()
        self.saturation_title.setText("Saturation: ")
        self.saturation_title.setAlignment(Qt.AlignLeft)
        self.saturation_title.setStyleSheet("color:gray;font-weight:bold")


        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setStyleSheet(delay_style)
        self.saturation_slider.setRange(-10,10)
        self.saturation_slider.setSliderPosition(self.saturation)
        self.saturation_slider.setSingleStep(1)
        self.saturation_slider.setMaximumWidth(160)
        self.saturation_slider.setDisabled(1)
        self.saturation_slider.sliderReleased.connect(self.saturation_position)

        self.sharpness_title = QLabel()
        self.sharpness_title.setText("Sharpness: ")
        self.sharpness_title.setAlignment(Qt.AlignLeft)
        self.sharpness_title.setStyleSheet("color:gray;font-weight:bold")


        self.sharpness_slider = QSlider(Qt.Horizontal)
        self.sharpness_slider.setStyleSheet(delay_style)
        self.sharpness_slider.setRange(0,4)
        self.sharpness_slider.setSliderPosition(self.sharpness)
        self.sharpness_slider.setSingleStep(1)
        self.sharpness_slider.setMaximumWidth(160)
        self.sharpness_slider.setDisabled(1)
        self.sharpness_slider.sliderReleased.connect(self.sharpness_position)

        self.camcontrolwidget.setObjectName("camwidget")
        self.camcontrolwidget.setLayout(self.camcontrol_layout)
        self.camcontrolwidget.setFixedHeight(175)
        self.camcontrolwidget.setFixedWidth(275)
        self.camcontrolwidget.setStyleSheet("QWidget#camwidget {border:1px solid white}")

        
        self.auto_layout.addWidget(self.auto_title)
        self.auto_layout.addWidget(self.auto_button)


        self.exp_layout.addWidget(self.exp_title)
        self.exp_layout.addWidget(self.exp_slider)

        self.iso_layout.addWidget(self.iso_title)
        self.iso_layout.addWidget(self.iso_slider)

        self.contrast_layout.addWidget(self.contrast_title)
        self.contrast_layout.addWidget(self.contrast_slider)

        self.saturation_layout.addWidget(self.saturation_title)
        self.saturation_layout.addWidget(self.saturation_slider)

        self.sharpness_layout.addWidget(self.sharpness_title)
        self.sharpness_layout.addWidget(self.sharpness_slider) 

        self.camcontrol_layout.addWidget(self.camcontrol_title)
        self.camcontrol_layout.addLayout(self.auto_layout)
        self.camcontrol_layout.addLayout(self.exp_layout)
        self.camcontrol_layout.addLayout(self.iso_layout)
        if 'color' in self.table.item(0,0).text().lower():
            self.camcontrol_layout.addLayout(self.contrast_layout)
            self.camcontrol_layout.addLayout(self.saturation_layout)
            self.camcontrol_layout.addLayout(self.sharpness_layout)


        self.bottomlayout.addWidget(self.camcontrolwidget)

    def zoomIn(self):
        self.scaleImage(1.01)

    def zoomOut(self):
        self.scaleImage(.99)

    def fitToWindow(self):
        self.scale = 1.0
        self.label.resize(720,480)
        self.scaled_img = self.img.scaled(720,480)
        self.label.setPixmap(self.scaled_img)
        # self.scaled_img = None

    def scaleImage(self, factor):
        self.scale *= factor
        self.label.resize(self.scale * self.img.size())
        self.scaled_img = self.img.scaled(self.scale*self.img.size())
        self.label.setPixmap(self.scaled_img)
        # self.scaled_img = None
        self.adjustScrollBar(self.mainscroll.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.mainscroll.verticalScrollBar(), factor)

        # self.zoomIn.setEnabled(self.scaleFactor < 3.0)
        # self.zoomOut.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))
    

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
        QToolTip.showText(QCursor.pos(),str(int(1000/self.frame_rate))+" ms")

    def exp_position(self):
        self.exposure = self.exp_slider.value()
        event = 'exposure'
        QToolTip.showText(QCursor.pos(),str(self.exposure)+" us")
        self.scaled_img = None
        self.scale = 1.0
        self.label.resize(720,480)
        self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,event)

    def iso_position(self):
        self.iso = self.iso_slider.value()
        event = 'iso'
        QToolTip.showText(QCursor.pos(),str(self.iso))
        self.scaled_img = None
        self.scale = 1.0
        self.label.resize(720,480)
        self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,event)

    def contrast_position(self):
        self.contrast = self.contrast_slider.value()
        event = 'contrast'
        QToolTip.showText(QCursor.pos(),str(self.contrast))
        self.scaled_img = None
        self.scale = 1.0
        self.label.resize(720,480)
        self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,event)

    def saturation_position(self):
        self.saturation = self.saturation_slider.value()
        event = 'saturation'
        QToolTip.showText(QCursor.pos(),str(self.saturation))
        self.scaled_img = None
        self.scale = 1.0
        self.label.resize(720,480)
        self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,event)

    def sharpness_position(self):
        self.sharpness = self.sharpness_slider.value()
        event = 'sharpness'
        QToolTip.showText(QCursor.pos(),str(self.sharpness))
        self.scaled_img = None
        self.scale = 1.0
        self.label.resize(720,480)
        self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,event)
        

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
        if self.source == None or self.source != self.table.item(0,0).text():
            self.source = self.table.item(0,0).text()
            if self.table.item(0,0) and not self.scrollth.isRunning():
                self.th.set_file(self.table.item(0,0),0,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,None)
                self.scaled_img = None
                self.scale = 1.0
                self.label.resize(720,480)
                if self.oak is not None:
                    self.make_cam_control_display()
            
            elif self.table.item(0,0) is None:
                return

                
            if self.table.item(0,0).text().lower().endswith(self.vid_formats) or os.path.isdir(self.table.item(0,0).text()):
                self.scaled_img = None
                self.scale = 1.0
                self.label.resize(720,480)
                self.active_widget = None
                self.mode_button.setDisabled(1)
                self.scrollth.quit()
                time.sleep(1)
                self.create_scroll_layout()
                self.scrollth.start()
                self.scrollth.set_file(self.table.item(0,0))
                    
            else:
                self.active_widget = None
                self.scaled_img = None
                self.scale = 1.0
                self.label.resize(720,480)
                self.mode_button.setDisabled(0)
                self.scrollth.quit()
                time.sleep(1)
                self.clear_scroll_layout()
                self.create_scroll_layout()
                self.record.setEnabled(0)
                if self.oak is not None:
                    self.make_cam_control_display()
    
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
        self.img = QPixmap.fromImage(data[0])
        if self.scaled_img is not None:
            self.label.setPixmap(self.scaled_img)
        else:
            self.label.setPixmap(self.img)
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
        self.scaled_img = None
        self.scale = 1.0
        self.label.resize(720,480)
        self.play.setDisabled(1)
        self.play.setCheckable(0)
        self.th.set_file(self.table.item(0,0),i,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,None)
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
        self.scaled_img = None
        self.scale = 1.0
        self.label.resize(720,480)
        self.rewind.setDisabled(1)
        self.rewind.setCheckable(0)
        self.th.set_file(self.table.item(0,0),i,self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,None)
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
        self.th.set_file(self.table.item(0,0),int(self.active_widget.objectName()),self.master_mode,self.autoexp,self.focus,self.exposure,self.iso,self.brightness,self.contrast,self.saturation,self.sharpness,None)
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
        self.scaled_img = None
        self.scale = 1.0
        self.label.resize(720,480)
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
                if self.oak is not None:
                    self.make_cam_control_display()


                                
        
        elif self.master_mode == 'offline':
            if not self.recording:
                self.recording = True
                self.record.setStyleSheet("background-color:red")
                self.image_dir = QFileDialog.getExistingDirectory()
            else:
                self.recording = False
                self.record.setStyleSheet("background-color:gray")

    def place_findline(self):
        row = self.table.currentRow()
        col = self.table.currentColumn()
        if row+col != 0:
            self.table.setItem(row,col,QTableWidgetItem("EdgeTool"))

            
        
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
   
class myRubberBand(QRubberBand):
    def __init__(self,QRubberBand_Shape,QWidget_parent=None):
        super(myRubberBand,self).__init__(QRubberBand_Shape,QWidget_parent)
   
    def paintEvent(self, QPaintEvent):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(Qt.red),2))
        painter.setBrush(QBrush(QColor(Qt.transparent)))
        painter.drawRect(QPaintEvent.rect())

class RectROI(QWidget):
    def __init__(self, parent=None):
        super(RectROI, self).__init__(parent)

        self.draggable = True
        self.dragging_threshold = 5
        self.mousePressPos = None
        self.mouseMovePos = None


        self.setWindowFlags(Qt.SubWindow)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.grip1 = QSizeGrip(self)
        self.grip2 = QSizeGrip(self)
        self.grip1.setStyleSheet("background-color:transparent")
        self.grip2.setStyleSheet("background-color:transparent")
        layout.addWidget(self.grip1, 0,Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.grip2, 0,Qt.AlignRight | Qt.AlignBottom)
        self._band = myRubberBand(QRubberBand.Rectangle, self)
        self._band.show()
        self.show()

    def resizeEvent(self, event):
        self._band.resize(self.size())

    def mousePressEvent(self, event):
        if self.draggable and event.button() == Qt.RightButton:
            self.mousePressPos = event.globalPosition().toPoint()                # global
            self.mouseMovePos = event.globalPosition().toPoint() - self.pos()    # local
        super(RectROI, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & Qt.RightButton:
            globalPos = event.globalPosition().toPoint()
            moved = globalPos - self.mousePressPos
            if moved.manhattanLength() > self.dragging_threshold:
                # Move when user drag window more than dragging_threshold
                diff = globalPos - self.mouseMovePos
                self.move(diff)
                self.mouseMovePos = globalPos - self.pos()
        super(RectROI, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mousePressPos is not None:
            if event.button() == Qt.RightButton:
                moved = event.globalPosition().toPoint() - self.mousePressPos
                if moved.manhattanLength() > self.dragging_threshold:
                    # Do not call click event or so on
                    event.ignore()
                self.mousePressPos = None
        super(RectROI, self).mouseReleaseEvent(event)

        
if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec())

