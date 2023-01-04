import os
import glob
import cv2
from MainScreenThread import Thread
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
        self.img_formats = ('.jpg','.bmp','.jpe','.jpeg','.tif','.tiff')
        self.vid_formats = ('.mp4','.avi','.mov','.wmv')
        self.glob_formats = "*.jpg,*.bmp,*.jpe,*.jpeg,*.tif,*.tiff"
             
    def set_file(self, fname):
        self.image_source =  fname.text()
        
    def run(self):
        if self.image_source.lower().endswith(self.vid_formats):
            cap = cv2.VideoCapture(self.image_source)
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            
            for i in range(int(total_frames)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # cv2.putText(frame,"frame #"+str(i+1),(75,75),cv2.FONT_HERSHEY_COMPLEX,4,(255,255,255),6)
                    frame = cv2.resize(frame,(160,120))

                    h, w, ch = frame.shape
                    img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                    self.updatescroll.emit([img,i,total_frames])
                    
                else:
                    self.quit()
            self.quit()

        elif os.path.isdir(self.image_source):
            # total_frames = len([glob.glob1(self.image_source,e) for e in self.glob_formats][0])
            total_frames = len([f for f_ in [glob.glob(os.path.join(self.image_source,e)) for e in self.glob_formats] for f in f_])
            i = 0
            for file in os.listdir(self.image_source):
                path = os.path.join(self.image_source,file)
                cap = cv2.VideoCapture(path)
                if file.lower().endswith(self.img_formats):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret,frame = cap.read()
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # cv2.putText(frame,"frame #"+str(i+1),(75,75),cv2.FONT_HERSHEY_COMPLEX,4,(255,255,255),6)
                    frame = cv2.resize(frame,(160,120))

                    h, w, ch = frame.shape
                    img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                    self.updatescroll.emit([img,i,total_frames])
                    i += 1
                    cap.release()  
                else:
                    self.quit()
            self.quit()