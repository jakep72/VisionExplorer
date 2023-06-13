import cv2
import numpy as np

def findlines(frame,rect_start,rect_end):
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
        
    roi = gray[rect_start[1]:rect_end[1],rect_start[0]:rect_end[0]]
    ret,thresh = cv2.threshold(roi,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    lsd = cv2.createLineSegmentDetector(0)

    minlen = 5
    maxgap = 10
    # lines = cv2.HoughLinesP(thresh,1,np.pi/180,80,minlen,maxgap)
    lines = lsd.detect(thresh)[0]
    # for x in range(0,len(lines)):
    # cv2.imshow('test',gray)
    # cv2.imshow('test2',roi)
    # cv2.imshow('test3',thresh)
    # cv2.waitKey(0)
    # print(lines[0][0])
    if lines is not None:
        x1 = lines[0][0][0]
        y1 = lines[0][0][1]
        x2 = lines[0][0][2]
        y2 = lines[0][0][3]

        return(x1,y1,x2,y2)
    else:
        return(None,None,None,None)