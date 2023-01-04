import os
import time
from PySide6.QtCore import QThread, Signal



class LiveRecord(QThread):
    updatescroll = Signal(list)

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
            img = self.label.pixmap()
            img = img.scaled(160, 120)        
            self.label.pixmap().save(os.path.join(self.dir,'frame'+str(i)+'.jpg'))
            self.updatescroll.emit([img,i])
            time.sleep(self.frame_rate)
            i+=1
