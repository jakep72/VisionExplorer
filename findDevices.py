import cv2
import depthai as dai
import contextlib

def OAK_Devices():
    deviceInfos = dai.Device.getAllAvailableDevices()
    usbSpeed = dai.UsbSpeed.HIGH

    try:
        with contextlib.ExitStack() as stack:
            # devices = []
            en_cam_list = []

            for deviceInfo in deviceInfos:
                deviceInfo: dai.DeviceInfo
                device: dai.Device = stack.enter_context(dai.Device(deviceInfo,usbSpeed))
                # devices.append(device)
                mxId = device.getMxId()
                cameras = device.getConnectedCameras()
                for cam in cameras:
                    if str(cam) == 'CameraBoardSocket.RGB':
                        en_cam_list.append('Color Camera')
                    elif str(cam) == 'CameraBoardSocket.LEFT':
                        en_cam_list.append('Mono Left Camera')
                    elif str(cam) == 'CameraBoardSocket.RIGHT':
                        en_cam_list.append('Mono Right Camera')
                en_cam_list.append('Stereo')

            devices = [mxId,en_cam_list]
                
        return(devices)
    except Exception:
        return(None)

def Webcam_Devices():
    cap = cv2.VideoCapture(0)
    if cap is None or not cap.isOpened():
        return(False)
    else:
        return(True)




