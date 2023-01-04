import os
import time
import glob
import cv2
import depthai as dai
from OAK_Cam import make_pipe
from PySide6.QtCore import Qt, QThread, Signal, Slot,QAbstractTableModel, QPoint, QRect, QSize
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QScreen
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget,QTableView,QTableWidget,
                               QScrollArea,QFrame, QTableWidgetItem,QProgressDialog,QRubberBand)

class Thread(QThread):
    updateFrame = Signal(QImage)
    
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.image_source = None
        self.status = True
        self.cap = True
        self.img_formats = ('.jpg','.bmp','.jpe','.jpeg','.tif','.tiff')
        self.vid_formats = ('.mp4','.avi','.mov','.wmv')
        self.mixed_formats = ('.mp4','.avi','.mov','.wmv','.jpg','.bmp','.jpe','.jpeg','.tif','.tiff')
        self.glob_formats = ['*.jpg','*.bmp','*.jpe','*.jpeg','*.tif','*.tiff']
        
    def set_file(self, fname,frame_no,master_mode):
        self.image_source =  fname.text()
        self.frame_no = int(frame_no)
        self.master_mode = master_mode
        
    def run(self):
        while True:
            self.status = True
              
            if self.image_source != None:
                if self.image_source.lower().endswith(self.mixed_formats):
                    source = self.image_source
                    self.cap = cv2.VideoCapture(source)
                    
                    if self.image_source != None and self.image_source != source:
                        self.status = False
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_no)
                    ret, frame = self.cap.read()
                    if not ret:
                        continue
        
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # frame = cv2.resize(frame,(640,480))

                    h, w, ch = frame.shape
                    img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                    img = img.scaled(720, 480)
                    self.updateFrame.emit(img)
                          
                elif os.path.isdir(self.image_source):
                    source = self.image_source
                    if self.image_source != None and self.image_source != source:
                        self.status = False
                    # frames = glob.glob1(source,"*.jpg")
                    # frames = [glob.glob1(source,e) for e in self.glob_formats][0]
                    frames = [f for f_ in [glob.glob(os.path.join(source,e)) for e in self.glob_formats] for f in f_]
                    file = frames[self.frame_no]
                    path = os.path.join(source,file)
                    self.cap = cv2.VideoCapture(path)
                    if file.lower().endswith(self.img_formats):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret,frame = self.cap.read()
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        # cv2.putText(frame,"frame #"+str(i+1),(75,75),cv2.FONT_HERSHEY_COMPLEX,4,(255,255,255),6)
                        # frame = cv2.resize(frame,(640,480))

                        h, w, ch = frame.shape
                        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                        img = img.scaled(720, 480)
                        self.updateFrame.emit(img)

                elif self.image_source == '1':
                    source = self.image_source
                    pipeline = make_pipe()
                    # Connect to device and start pipeline
                    with dai.Device(pipeline,usb2Mode=True) as device:

                        video = device.getOutputQueue(name="video", maxSize=1, blocking=False)

                        if self.master_mode == 'live':
                            while self.status:
                                if self.image_source != None and self.image_source != source:
                                    self.status = False
                                videoIn = video.get()
                                frame = videoIn.getCvFrame()
                                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                h, w, ch = frame.shape
                                img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                img = img.scaled(720, 480)
                                self.updateFrame.emit(img)
                                if self.master_mode == 'live':
                                    pass
                                else:
                                    self.status = False
                                    break
                        
                        elif self.master_mode == 'offline':
                            if self.image_source != None and self.image_source != source:
                                self.status = False
                            videoIn = video.get()
                            frame = videoIn.getCvFrame()
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            h, w, ch = frame.shape
                            img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                            img = img.scaled(720, 480)
                            self.updateFrame.emit(img)
                            while self.status:
                                if self.master_mode == 'offline':
                                    if self.image_source != source:
                                        self.status = False
                                        break
                                    else:
                                        pass
                                elif self.master_mode == 'live':
                                    self.status = False
                                    break
                                    
                elif self.image_source == '0':
                    source = self.image_source
                    if self.image_source != None and self.image_source != source:
                        self.status = False
                        self.cap.release()

                    self.cap = cv2.VideoCapture(int(source))
                    
                    if self.master_mode == 'live':
                        while self.status:
                            if self.image_source != None and self.image_source != source:
                                self.status = False
                            ret, frame = self.cap.read()
                            if not ret:
                                self.status = False
                
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            # frame = cv2.resize(frame,(640,480))

                            h, w, ch = frame.shape
                            img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                            img = img.scaled(720, 480)
                            self.updateFrame.emit(img)

                    elif self.master_mode == 'offline':
                        if self.image_source != None and self.image_source != source:
                            self.status = False
                        ret, frame = self.cap.read()
                        if not ret:
                            self.status = False
            
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        # frame = cv2.resize(frame,(640,480))

                        h, w, ch = frame.shape
                        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                        img = img.scaled(720, 480)
                        self.updateFrame.emit(img)
                        while self.status:
                            if self.master_mode == 'offline':
                                if self.image_source != source:
                                    self.status = False
                                    break
                                else:
                                    pass
                            elif self.master_mode == 'live':
                                self.status = False
                                break
           
            else:
                pass