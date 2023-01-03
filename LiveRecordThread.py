import os
import time
from PySide6.QtCore import QThread



class LiveRecord(QThread):

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.active = True
             
    def set_dir(self, label, dir,frame_rate):
        self.label = label
        self.dir =  dir
        self.frame_rate = frame_rate   

    def run(self):
        i = 0
        while self.active:            
            self.label.pixmap().save(os.path.join(self.dir,'frame'+str(i)+'.jpg'))
            time.sleep(self.frame_rate) 
            i+=1 