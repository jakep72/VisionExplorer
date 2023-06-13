import os
import time
import glob
import cv2
from cv_functions import findlines
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
        
    def set_file(self, fname,frame_no,master_mode,auto,focus,exposure,iso,brightness,contrast,saturation,sharpness,event,roi):
        self.image_source =  fname.text()
        self.frame_no = int(frame_no)
        self.master_mode = master_mode
        self.auto = auto
        self.exposure = exposure
        self.iso = iso
        self.focus = focus
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self.sharpness = sharpness
        self.event = event
        self.roi = roi
        self.rect_start = None
        self.rect_end = None

        if self.roi is not None:
            point_start = self.roi.getState()['pos']
            self.rect_size = self.roi.getState()['size']
            self.rect_angle = self.roi.getState()['angle']
            x_start = int(point_start[0])
            y_start = int(point_start[1])
            width = int(self.rect_size[0])
            height = int(self.rect_size[1])
            x_end = x_start+width
            y_end = y_start+height
            self.rect_start = (x_start,y_start)
            self.rect_end = (x_end,y_end)


        
    def run(self):
        while True:
            self.status = True
            
            if self.image_source != None:

                ##### Video or Image files -- offline mode only #####
                if self.image_source.lower().endswith(self.mixed_formats):
                    source = self.image_source
                    self.cap = cv2.VideoCapture(source)
                    s = time.time()
                    if self.image_source != None and self.image_source != source:
                        self.status = False
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_no)
                    ret, frame = self.cap.read()
                    if not ret:
                        continue
        
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    if self.rect_start is not None:
                        points = findlines(frame,self.rect_start,self.rect_end)
                        x1 = points[0]
                        y1 = points[1]
                        x2 = points[2]
                        y2 = points[3]
                        # if x1 is not None:
                        #     cv2.line(frame,(x1+self.rect_start[0],y1+self.rect_start[1]),(x2+self.rect_start[0],y2+self.rect_start[1]),(255,0,0),3)
                    
                    # img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                    # img = img.scaled(720, 480)
                        e = time.time()
                        delta = 1000*(e-s)
                        self.updateFrame.emit([frame,delta,points])
                    # if self.rect_start is not None:
                    #     x1,y1,x2,y2 = findlines(frame,self.rect_start,self.rect_end)
                    #     cv2.line(frame,(x1+self.rect_start[0],y1+self.rect_start[1]),(x2+self.rect_start[0],y2+self.rect_start[1]),(255,0,0),3)
                    # frame = cv2.resize(frame,(640,480))

                    # h, w, ch = frame.shape
                    # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                    # img = img.scaled(720, 480)
                    else:
                        self.updateFrame.emit([frame,None])

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
                    s = time.time()
                    if file.lower().endswith(self.img_formats):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret,frame = self.cap.read()
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        if self.rect_start is not None:
                            points = findlines(frame,self.rect_start,self.rect_end)
                            x1 = points[0]
                            y1 = points[1]
                            x2 = points[2]
                            y2 = points[3]
                            # if x1 is not None:
                            #     cv2.line(frame,(x1+self.rect_start[0],y1+self.rect_start[1]),(x2+self.rect_start[0],y2+self.rect_start[1]),(255,0,0),3)
                        
                        # img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                        # img = img.scaled(720, 480)
                            e = time.time()
                            delta = 1000*(e-s)
                            self.updateFrame.emit([frame,delta,points])
                        # if self.rect_start is not None:
                        #     x1,y1,x2,y2 = findlines(frame,self.rect_start,self.rect_end)
                        #     cv2.line(frame,(x1+self.rect_start[0],y1+self.rect_start[1]),(x2+self.rect_start[0],y2+self.rect_start[1]),(255,0,0),3)
                        # frame = cv2.resize(frame,(640,480))

                        # h, w, ch = frame.shape
                        # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                        # img = img.scaled(720, 480)
                        else:
                            self.updateFrame.emit([frame,None])

                ##### Webcam -- offline and live mode #####
                elif self.image_source == 'Webcam':
                    source = self.image_source
                    if self.image_source != None and self.image_source != source:
                        self.status = False
                        self.cap.release()

                    self.cap = cv2.VideoCapture(0)
                    
                    if self.master_mode == 'live':
                        while self.status:
                            s = time.time()
                            if self.image_source != None and self.image_source != source:
                                self.status = False
                                self.cap.release()

                            ret, frame = self.cap.read()
                            if not ret:
                                self.status = False
                                self.cap.release()
                
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                            if self.rect_start is not None:
                                points = findlines(frame,self.rect_start,self.rect_end)
                                x1 = points[0]
                                y1 = points[1]
                                x2 = points[2]
                                y2 = points[3]
                                # if x1 is not None:
                                #     cv2.line(frame,(x1+self.rect_start[0],y1+self.rect_start[1]),(x2+self.rect_start[0],y2+self.rect_start[1]),(255,0,0),3)
                            
                            # img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                            # img = img.scaled(720, 480)
                            e = time.time()
                            delta = 1000*(e-s)
                            self.updateFrame.emit([frame,delta,points])

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
                        # h, w, ch = frame.shape
                        # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                        # img = img.scaled(720, 480)
                        self.updateFrame.emit([frame,None])
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
                elif self.image_source.split('_')[1] == 'Color':
                    source = self.image_source
                    info = dai.DeviceInfo(source.split('_')[0])
                    pipeline = make_color_pipe()
                    # Connect to device and start pipeline
                    with dai.Device(pipeline,info,usb2Mode=True) as device:

                        video = device.getOutputQueue(name="video", maxSize=1, blocking=False)
                        controlQ = device.getInputQueue(name='control',maxSize = 8,blocking=False)

                        if self.auto == False:
                            ctrl = dai.CameraControl()
                            ctrl.setManualExposure(self.exposure,self.iso)
                            ctrl.setContrast(self.contrast)
                            ctrl.setSaturation(self.saturation)
                            ctrl.setSharpness(self.sharpness)
                            controlQ.send(ctrl)
                            time.sleep(2)
                        else:
                            ctrl = dai.CameraControl()
                            ctrl.setAutoExposureLock(True)
                            ctrl.setContrast(self.contrast)
                            ctrl.setSaturation(self.saturation)
                            ctrl.setSharpness(self.sharpness)
                            controlQ.send(ctrl)
                            time.sleep(2)                            

                        if self.master_mode == 'live':
                            while self.status:
                                s = time.time()
                                if self.image_source != None and self.image_source != source:
                                    self.status = False
                                
                                videoIn = video.get()
                                frame = videoIn.getCvFrame()
                                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                                if self.rect_start is not None:
                                    points = findlines(frame,self.rect_start,self.rect_end)
                                    x1 = points[0]
                                    y1 = points[1]
                                    x2 = points[2]
                                    y2 = points[3]
                                    # if x1 is not None:
                                    #     cv2.line(frame,(x1+self.rect_start[0],y1+self.rect_start[1]),(x2+self.rect_start[0],y2+self.rect_start[1]),(255,0,0),3)
                                
                                # img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                                # img = img.scaled(720, 480)
                                e = time.time()
                                delta = 1000*(e-s)
                                self.updateFrame.emit([frame,delta,points])
                                
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
                            # h, w, ch = frame.shape
                            # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                            # img = img.scaled(720, 480)
                            self.updateFrame.emit([frame,None])
                            while self.status:
                                if self.master_mode == 'offline':
                                    if self.image_source != source:
                                        self.status = False
                                        break
                                    else:
                                        if self.event == 'exposure' or self.event == 'iso':
                                            ctrl.setManualExposure(self.exposure,self.iso)
                                            controlQ.send(ctrl)
                                            time.sleep(1)
                                            self.event = None
                                            videoIn = video.get()
                                            frame = videoIn.getCvFrame()
                                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            # h, w, ch = frame.shape
                                            # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                            # img = img.scaled(720, 480)
                                            self.updateFrame.emit([frame,None])
                                            
                                        elif self.event == 'contrast':
                                            ctrl.setContrast(self.contrast)
                                            controlQ.send(ctrl)
                                            time.sleep(1)
                                            self.event = None
                                            videoIn = video.get()
                                            frame = videoIn.getCvFrame()
                                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            # h, w, ch = frame.shape
                                            # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                            # img = img.scaled(720, 480)
                                            self.updateFrame.emit([frame,None])
                                        elif self.event == 'saturation':
                                            ctrl.setSaturation(self.saturation)
                                            controlQ.send(ctrl)
                                            time.sleep(1)
                                            self.event = None
                                            videoIn = video.get()
                                            frame = videoIn.getCvFrame()
                                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            # h, w, ch = frame.shape
                                            # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                            # img = img.scaled(720, 480)
                                            self.updateFrame.emit([frame,None])
                                        elif self.event == 'sharpness':
                                            ctrl.setSharpness(self.sharpness)
                                            controlQ.send(ctrl)
                                            time.sleep(1)
                                            self.event = None
                                            videoIn = video.get()
                                            frame = videoIn.getCvFrame()
                                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            # h, w, ch = frame.shape
                                            # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                            # img = img.scaled(720, 480)
                                            self.updateFrame.emit([frame,None])
                                        elif self.event == 'AutoOn':
                                            ctrl.setAutoExposureEnable()
                                            ctrl.setContrast(0)
                                            ctrl.setSaturation(0)
                                            ctrl.setSharpness(0)
                                            controlQ.send(ctrl)
                                            time.sleep(1)
                                            self.event = None
                                            videoIn = video.get()
                                            frame = videoIn.getCvFrame()
                                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            # h, w, ch = frame.shape
                                            # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                            # img = img.scaled(720, 480)
                                            self.updateFrame.emit([frame,None])
                                            break
                                        else:
                                            pass

                                elif self.master_mode == 'live':
                                    self.status = False
                                    break
                                    
                ##### OAK-D LITE Right Mono Camera -- offline and live mode #####
                elif self.image_source.split('_')[1] == 'MonoRight' or self.image_source.split('_')[1] == 'MonoLeft':
                    source = self.image_source
                    info = dai.DeviceInfo(source.split('_')[0])
                    if self.image_source.split('_')[1] == 'MonoRight': 
                        pipeline = make_mono_right_pipe()
                    elif self.image_source.split('_')[1] == 'MonoLeft':
                        pipeline = make_mono_left_pipe()
                    # Connect to device and start pipeline
                    with dai.Device(pipeline,info,usb2Mode=True) as device:

                        if self.image_source.split('_')[1] == 'MonoRight': 
                            qRight = device.getOutputQueue(name="right", maxSize=1, blocking=False)
                        elif self.image_source.split('_')[1] == 'MonoLeft':
                            qRight = device.getOutputQueue(name="left", maxSize=1, blocking=False)
                        
                        if self.auto == False:
                            controlQ = device.getInputQueue(name='control')
                            ctrl = dai.CameraControl()
                            ctrl.setManualExposure(self.exposure,self.iso)
                            controlQ.send(ctrl)
                            time.sleep(1)
                        else:
                            controlQ = device.getInputQueue(name='control')
                            ctrl = dai.CameraControl()
                            ctrl.setAutoExposureLock(True)
                            controlQ.send(ctrl)
                            time.sleep(1)
                        

                        if self.master_mode == 'live':
                            while self.status:
                                s = time.time()
                                if self.image_source != None and self.image_source != source:
                                    self.status = False


                                inRight = qRight.get()
                                frame = inRight.getCvFrame()
                                
                                if self.rect_start is not None:
                                    points = findlines(frame,self.rect_start,self.rect_end)
                                    x1 = points[0]
                                    y1 = points[1]
                                    x2 = points[2]
                                    y2 = points[3]
                                    # if x1 is not None:
                                    #     cv2.line(frame,(x1+self.rect_start[0],y1+self.rect_start[1]),(x2+self.rect_start[0],y2+self.rect_start[1]),(255,0,0),3)
                                
                                # img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                                # img = img.scaled(720, 480)
                                e = time.time()
                                delta = 1000*(e-s)
                                self.updateFrame.emit([frame,delta,points])

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

                            # h, w  = frame.shape
                            # img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                            # img = img.scaled(720, 480)
                            self.updateFrame.emit([frame,None])
                            while self.status:
                                if self.master_mode == 'offline':
                                    if self.image_source != source:
                                        self.status = False
                                        break
                                    else:
                                        if self.event == 'exposure' or self.event == 'iso':
                                            ctrl.setManualExposure(self.exposure,self.iso)
                                            controlQ.send(ctrl)
                                            time.sleep(1)
                                            self.event = None
                                            inRight = qRight.get()
                                            frame = inRight.getCvFrame()

                                            # h, w  = frame.shape
                                            # img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                                            # img = img.scaled(720, 480)
                                            self.updateFrame.emit([frame,None])
                                        elif self.event == 'AutoOn':
                                            ctrl.setAutoExposureEnable()
                                            controlQ.send(ctrl)
                                            time.sleep(1)
                                            self.event = None
                                            inRight = qRight.get()
                                            frame = inRight.getCvFrame()

                                            # h, w  = frame.shape
                                            # img = QImage(frame.data, w, h, QImage.Format_Grayscale8)
                                            # img = img.scaled(720, 480)
                                            self.updateFrame.emit([frame,None])
                                            break
                                        else:
                                            pass
                                elif self.master_mode == 'live':
                                    self.status = False
                                    break

                ##### OAK-D LITE Depth Camera -- offline and live mode #####
                elif self.image_source.split('_')[1] == 'Stereo':
                    source = self.image_source
                    info = dai.DeviceInfo(source.split('_')[0])
                    pipeline, depth = make_stereo_pipe()
                    # Connect to device and start pipeline
                    with dai.Device(pipeline,info,usb2Mode=True) as device:

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
                                # h, w, ch = frame.shape
                                # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                                # img = img.scaled(720, 480)
                                e = time.time()
                                delta = 1000*(e-s)
                                self.updateFrame.emit([frame,delta])

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
                            # h, w, ch = frame.shape
                            # img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                            # img = img.scaled(720, 480)
                            self.updateFrame.emit([frame,None])
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