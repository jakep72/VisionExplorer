import cv2
import depthai as dai
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox
import contextlib

class Load_Device_Thread(QThread):
    updateDevices = Signal(list)
    loaded = Signal(int)
    
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        
    def run(self):
        self.webcam = Webcam_Devices()
        self.oak = OAK_USB_Devices()
        self.loaded.emit(1)
        self.updateDevices.emit([self.webcam,self.oak])

    def quit(self):
        if self.webcam and self.oak is not None:
            num_devs = '2 devices were found!'
        elif not self.webcam and self.oak is not None:
            num_devs = '1 device was found!'
            print(2)
        elif self.webcam and self.oak is None:
            num_devs = '1 device was found!'
            print(3)
        else:
            num_devs = 'No devices were found!'
            print(4)

        dlg = QMessageBox()
        
        dlg.setWindowTitle(" ")
        dlg.setText(num_devs)
        dlg.exec()

def Webcam_Devices():
    cap = cv2.VideoCapture(0)
    if cap is None or not cap.isOpened():
        return(False)
    else:
        return(True)

def OAK_USB_Devices():
    devices = []
    for device in dai.Device.getAllAvailableDevices():
        mxId = device.getMxId()
        
        info = dai.DeviceInfo(mxId) # MXID
        #device_info = depthai.DeviceInfo("192.168.1.44") # IP Address
        #device_info = depthai.DeviceInfo("3.3.3") # USB port name
        pipeline = dai.Pipeline()
        en_cam_list = []
        with dai.Device(pipeline, info, usb2Mode=True) as dev:
            cameras = dev.getConnectedCameras()
            for cam in cameras:
                if str(cam) == 'CameraBoardSocket.RGB':
                    en_cam_list.append('Color Camera')
                elif str(cam) == 'CameraBoardSocket.LEFT':
                    en_cam_list.append('Mono Left Camera')
                elif str(cam) == 'CameraBoardSocket.RIGHT':
                    en_cam_list.append('Mono Right Camera')
            en_cam_list.append('Stereo')
        info_dict = {mxId:en_cam_list}
        devices.append(info_dict)

    return(devices)







