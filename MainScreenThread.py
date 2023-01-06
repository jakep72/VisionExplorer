import os
import time
import glob
import cv2
import depthai as dai
import numpy as np
from OAK_Cam import make_color_pipe, make_mono_left_pipe, make_mono_right_pipe, make_stereo_pipe
from PySide6.QtCore import Qt, QThread, Signal, Slot,QAbstractTableModel, QPoint, QRect, QSize
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QScreen
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget,QTableView,QTableWidget,
                               QScrollArea,QFrame, QTableWidgetItem,QProgressDialog,QRubberBand)
def number(f):
    return(int(f[5:-4]))

class Thread(QThread):
    updateFrame = Signal(list)
    
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

                ##### Video or Image files -- offline mode only #####
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
                    self.updateFrame.emit([img,None])

                ##### Directories of image files -- offline mode only #####         
                elif os.path.isdir(self.image_source):
                    source = self.image_source
                    if self.image_source != None and self.image_source != source:
                        self.status = False
                        return

                    try:
                        frames = sorted(os.listdir(source),key=number)
                    except ValueError:
                        frames = os.listdir(source)
                    
                    file = frames[self.frame_no]
                    path = os.path.join(source,file)
                    self.cap = cv2.VideoCapture(path)
                    if file.lower().endswith(self.img_formats):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret,frame = self.cap.read()
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = frame.shape
                        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                        img = img.scaled(720, 480)
                        self.updateFrame.emit([img,None])

                ##### Webcam -- offline and live mode #####
                elif self.image_source == '0':
                    source = self.image_source
                    if self.image_source != None and self.image_source != source:
                        self.status = False
                        self.cap.release()
                        print("1")
                        print(self.cap.isOpened())
                        print(self.status)

                    self.cap = cv2.VideoCapture(int(source))
                    
                    if self.master_mode == 'live':
                        while self.status:
                            s = time.time()
                            if self.image_source != None and self.image_source != source:
                                self.status = False
                                self.cap.release()
                                print("2")
                                print(self.cap.isOpened())
                                print(self.status)

                            ret, frame = self.cap.read()
                            if not ret:
                                self.status = False
                                self.cap.release()
                                print("3")
                                print(self.cap.isOpened())
                                print(self.status)
                
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            h, w, ch = frame.shape
                            img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                            img = img.scaled(720, 480)
                            e = time.time()
                            delta = 1000*(e-s)
                            self.updateFrame.emit([img,delta])

                            if self.master_mode == 'live':
                                pass
                            else:
                                self.cap.release()
                                self.status = False
                                break
                            
                            

                    elif self.master_mode == 'offline':
                        if self.image_source != None and self.image_source != source:
                            self.status = False
                            self.cap.release()
                        ret, frame = self.cap.read()
                        if not ret:
                            self.status = False
                            self.cap.release()
            
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = frame.shape
                        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                        img = img.scaled(720, 480)
                        self.updateFrame.emit([img,None])
                        while self.status:
                            if self.master_mode == 'offline':
                                if self.image_source != source:
                                    self.status = False
                                    self.cap.release()
                                    break
                                else:
                                    pass
                            elif self.master_mode == 'live':
                                self.status = False
                                self.cap.release()
                                break

                ##### OAK-D LITE Color Camera -- offline and live mode ####
                elif self.image_source == '1':
                    source = self.image_source
                    pipeline = make_color_pipe()
                    # Connect to device and start pipeline
                    with dai.Device(pipeline,usb2Mode=True) as device:

                        video = device.getOutputQueue(name="video", maxSize=1, blocking=False)

                        if self.master_mode == 'live':
                            while self.status:
                                s = time.time()
                                if self.image_source != None and self.image_source != source:
                                    self.status = False
                                videoIn = video.get()
                                frame = videoIn.getCvFrame()
                                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                h, w, ch = frame.shape
                                img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                img = img.scaled(720, 480)
                                e = time.time()
                                delta = 1000*(e-s)
                                self.updateFrame.emit([img,delta])
                                
                                
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
                            self.updateFrame.emit([img,None])
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
                                    
                ##### OAK-D LITE Right Mono Camera -- offline and live mode #####
                elif self.image_source == '2':
                    source = self.image_source
                    pipeline = make_mono_right_pipe()
                    # Connect to device and start pipeline
                    with dai.Device(pipeline,usb2Mode=True) as device:

                        qRight = device.getOutputQueue(name="right", maxSize=1, blocking=False)

                        if self.master_mode == 'live':
                            while self.status:
                                s = time.time()
                                if self.image_source != None and self.image_source != source:
                                    self.status = False
                                inRight = qRight.get()
                                frame = inRight.getCvFrame()
                                h, w  = frame.shape
                                img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                                img = img.scaled(720, 480)
                                e = time.time()
                                delta = 1000*(e-s)
                                self.updateFrame.emit([img,delta])

                                if self.master_mode == 'live':
                                    pass
                                else:
                                    self.status = False
                                    break
                        
                        elif self.master_mode == 'offline':
                            if self.image_source != None and self.image_source != source:
                                self.status = False
                            inRight = qRight.get()
                            frame = inRight.getCvFrame()
                            h, w  = frame.shape
                            img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                            img = img.scaled(720, 480)
                            self.updateFrame.emit([img,None])
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

                ##### OAK-D LITE Left Mono Camera -- offline and live mode #####
                elif self.image_source == '3':
                    source = self.image_source
                    pipeline = make_mono_left_pipe()
                    # Connect to device and start pipeline
                    with dai.Device(pipeline,usb2Mode=True) as device:

                        qLeft = device.getOutputQueue(name="left", maxSize=1, blocking=False)

                        if self.master_mode == 'live':
                            while self.status:
                                s = time.time()
                                if self.image_source != None and self.image_source != source:
                                    self.status = False
                                inLeft = qLeft.get()
                                frame = inLeft.getCvFrame()
                                h, w  = frame.shape
                                img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                                img = img.scaled(720, 480)
                                e = time.time()
                                delta = 1000*(e-s)
                                self.updateFrame.emit([img,delta])
                                

                                if self.master_mode == 'live':
                                    pass
                                else:
                                    self.status = False
                                    break
                        
                        elif self.master_mode == 'offline':
                            if self.image_source != None and self.image_source != source:
                                self.status = False
                            inLeft = qLeft.get()
                            frame = inLeft.getCvFrame()
                            h, w  = frame.shape
                            img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                            img = img.scaled(720, 480)
                            self.updateFrame.emit([img,None])
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

                ##### OAK-D LITE Depth Camera -- offline and live mode #####
                elif self.image_source == '4':
                    source = self.image_source
                    pipeline, depth = make_stereo_pipe()
                    # Connect to device and start pipeline
                    with dai.Device(pipeline,usb2Mode=True) as device:

                        q = device.getOutputQueue(name="disparity", maxSize=1, blocking=False)

                        if self.master_mode == 'live':
                            while self.status:
                                s = time.time()
                                if self.image_source != None and self.image_source != source:
                                    self.status = False
                                inq = q.get()
                                frame = inq.getFrame()
                                frame = (frame *(255 / depth.initialConfig.getMaxDisparity())).astype(np.uint8)
                                frame = cv2.applyColorMap(frame,cv2.COLORMAP_JET)
                                h, w, ch = frame.shape
                                img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                img = img.scaled(720, 480)
                                e = time.time()
                                delta = 1000*(e-s)
                                self.updateFrame.emit([img,delta])

                                if self.master_mode == 'live':
                                    pass
                                else:
                                    self.status = False
                                    break
                        
                        elif self.master_mode == 'offline':
                            if self.image_source != None and self.image_source != source:
                                self.status = False
                            inq = q.get()
                            frame = inq.getFrame()
                            frame = (frame *(255 / depth.initialConfig.getMaxDisparity())).astype(np.uint8)
                            frame = cv2.applyColorMap(frame,cv2.COLORMAP_JET)
                            h, w, ch = frame.shape
                            img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                            img = img.scaled(720, 480)
                            self.updateFrame.emit([img,None])
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