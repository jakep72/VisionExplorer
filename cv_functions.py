import cv2
import numpy as np

def findlines(frame,rect_start,rect_end,method='both'):
    if rect_start[0] < 0 or rect_start[1] < 0 or rect_end[0] < 0 or rect_end[1] < 0:
        print("Region of interest out of frame!")
        return(None,None,None,None)
    
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    
    bw_offset = 5   
    roi = gray[rect_start[1]:rect_end[1],rect_start[0]:rect_end[0]]
    ret,thresh = cv2.threshold(roi,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    if thresh is None:
        return(None,None,None,None)
    lsd = cv2.createLineSegmentDetector(0)
    

    minlen = 5

    lines = lsd.detect(thresh)[0]
    if lines is not None:
        x1 = lines[0][0][0]
        y1 = lines[0][0][1]
        x2 = lines[0][0][2]
        y2 = lines[0][0][3]
        cpx = (x2-x1)/2
        cpy = (y2-y1)/2

        line_len = int(((abs(x2-x1)**2)+(abs(y2-y1)**2)**(1/2)))

        line_center_px_above = thresh[int(cpy-bw_offset),int(cpx)]
        line_center_px_below = thresh[int(cpy+bw_offset),int(cpx)]

        if x1 != x2  and line_len > minlen:
            if method == 'both':
                return(x1,y1,x2,y2)
            elif line_center_px_above < line_center_px_below and method == "b2w":
                return(x1,y1,x2,y2)
            elif line_center_px_above > line_center_px_below and method == "w2b":
                return(x1,y1,x2,y2)
            else:
                return(None,None,None,None)
        else:
            return(None,None,None,None)
    else:
        return(None,None,None,None)