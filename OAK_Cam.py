import cv2
import depthai as dai
import time

def make_color_pipe():
# Create pipeline
    pipeline = dai.Pipeline()

    # Define source and output
    camRgb = pipeline.create(dai.node.ColorCamera)
    xoutVideo = pipeline.create(dai.node.XLinkOut)
    controlIn = pipeline.create(dai.node.XLinkIn)

    controlIn.setStreamName("control")
    xoutVideo.setStreamName("video")

    # Properties
    camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
    camRgb.setVideoSize(1280, 720)
    camRgb.setFps(35)

    # xoutVideo.input.setBlocking(False)
    # xoutVideo.input.setQueueSize(1)

    # Linking
    camRgb.video.link(xoutVideo.input)
    controlIn.out.link(camRgb.inputControl)
    return (pipeline)

def make_mono_right_pipe():
    pipeline = dai.Pipeline()

    monoRight = pipeline.create(dai.node.MonoCamera)
    xoutRight = pipeline.create(dai.node.XLinkOut)
    controlIn = pipeline.create(dai.node.XLinkIn)

    controlIn.setStreamName("control")
    xoutRight.setStreamName("right")

    monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)
    monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_480_P)
    monoRight.setFps(99)

    monoRight.out.link(xoutRight.input)
    controlIn.out.link(monoRight.inputControl)

    return(pipeline)

def make_mono_left_pipe():
    pipeline = dai.Pipeline()

    monoLeft = pipeline.create(dai.node.MonoCamera)
    xoutLeft = pipeline.create(dai.node.XLinkOut)
    controlIn = pipeline.create(dai.node.XLinkIn)

    controlIn.setStreamName("control")
    xoutLeft.setStreamName("left")

    monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
    monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_480_P)
    monoLeft.setFps(99)

    monoLeft.out.link(xoutLeft.input)
    controlIn.out.link(monoLeft.inputControl)

    return(pipeline)

def make_stereo_pipe():
    ext = False
    sub = True
    lr = True

    pipeline = dai.Pipeline()

    monoLeft = pipeline.create(dai.node.MonoCamera)
    monoRight = pipeline.create(dai.node.MonoCamera)
    depth = pipeline.create(dai.node.StereoDepth)
    xout = pipeline.create(dai.node.XLinkOut)

    xout.setStreamName('disparity')

    monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)

    monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

    depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
    depth.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)

    depth.setLeftRightCheck(lr)
    depth.setExtendedDisparity(ext)
    depth.setSubpixel(sub)

    monoLeft.out.link(depth.left)
    monoRight.out.link(depth.right)
    depth.disparity.link(xout.input)

    return(pipeline,depth)



# pipeline = make_mono_left_pipe()
# with dai.Device(pipeline,usb2Mode=True) as device:

#     qRight = device.getOutputQueue(name="right", maxSize=1, blocking=False)

#     times = []
#     for i in range(1000):
#         s = time.time()
#         inRight = qRight.get()
#         frame = inRight.getCvFrame()
#         # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         frame = cv2.resize(frame,(720,480))
        
#         cv2.imshow('frame',frame)
#         if cv2.waitKey(1) == ord('q'):
#             break
#         e = time.time()
#         print(i)
#         times.append(e-s)
#         i+=1
#     ave = sum(times)/len(times)
#     print('mean: '+str(ave)) 


# pipeline = make_color_pipe()
#                     # Connect to device and start pipeline
# with dai.Device(pipeline,usb2Mode=True) as device:

#     video = device.getOutputQueue(name="video", maxSize=1, blocking=False)

#     times = []
#     for i in range(1000):
#         s = time.time()
#         videoIn = video.get()
#         frame = videoIn.getCvFrame()
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         # frame = cv2.resize(frame,(720,480))
        
#         cv2.imshow('frame',frame)
#         if cv2.waitKey(1) == ord('q'):
#             break
#         e = time.time()
#         print(e-s)
#         times.append(e-s)
#         i+=1
#     ave = sum(times)/len(times)
#     print('mean: '+str(ave))    
        
