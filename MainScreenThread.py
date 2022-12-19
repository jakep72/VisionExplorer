import cv2
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

                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame,(640,480))

                    h, w, ch = frame.shape
                    img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                    # scaled_img = img.scaled(640, 480, Qt.KeepAspectRatio)
                    
                    self.updateFrame.emit(img)
                # sys.exit(-1)
            else:
                pass