import cv2
import numpy as np

def findlines(frame,rect_start,rect_end):
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    bw_offset = 5   
    roi = gray[rect_start[1]:rect_end[1],rect_start[0]:rect_end[0]]
    ret,thresh = cv2.threshold(roi,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    lsd = cv2.createLineSegmentDetector(0)

    minlen = 5000
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
        cpx = (x2-x1)/2
        cpy = (y2-y1)/2

        line_len = int(((abs(x2-x1)**2)+(abs(y2-y1)**2)**(1/2)))

        # line_left_px_above = thresh[int(y1-bw_offset),int(x1)]
        # line_left_px_below = thresh[int(y1+bw_offset),int(x1)]

        line_center_px_above = thresh[int(cpy-bw_offset),int(cpx)]
        line_center_px_below = thresh[int(cpy+bw_offset),int(cpx)]

        # line_right_px_above = thresh[int(y2-bw_offset),int(x2)]
        # line_right_px_below = thresh[int(y2+bw_offset),int(x2)]
        
        # ave_above = (int(line_left_px_above)+int(line_center_px_above)+int(line_right_px_above))/3
        # ave_below = (int(line_left_px_below)+int(line_center_px_below)+int(line_right_px_below))/3

        if x1 != x2 and line_center_px_above < line_center_px_below and line_len > minlen:
            return(x1,y1,x2,y2)
        else:
            return(None,None,None,None)
    else:
        return(None,None,None,None)