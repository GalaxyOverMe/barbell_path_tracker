### code reference : https://github.com/nando-nando/barPathTracking

import cv2
import os
import pandas as pd
import numpy as np


input_path  = './video/'
output_path = './result/'
outputName  = os.listdir(input_path)[0][:-4]

file_path = os.path.join(input_path, os.listdir(input_path)[0]) # first video will be selected


video = cv2.VideoCapture(file_path)
# tracker = cv2.legacy_TrackerMedianFlow.create() # fast but little difference
tracker = cv2.TrackerCSRT_create() # best


returnValue, frame = video.read()
#show the frame
cv2.imshow("Frame", frame)

### select the plate boundingBox -> Only using width
plate_box = cv2.selectROI("Frame", frame)
try:
    tracker.init(frame, plate_box)
#if this fails throw exception
except:
    print("A bounding box was not correctly created. Please try again.")
(success, box) = tracker.update(frame)
(_, _, W, _) = [int(i) for i in box]




#This allows the user to select the "region of interest"
boundingBox = cv2.selectROI("Frame", frame)

#initialize the tracker with the frame and the object being tracked in the ROI

try:
    tracker.init(frame, boundingBox)
#if this fails throw exception
except:
    print("A bounding box was not correctly created. Please try again.")


#list to hold all prev posiotions of object
centerPoints = []
times = []
t = 0
fps = 30

while video.isOpened():    
    returnValue, frame = video.read()
    #if the return value is false we can break bc the video is done
    if not returnValue:
        break

    #find the next pos of object being tracked, (success is true if the object is located)
    (success, box) = tracker.update(frame)

    if success: #if true
        #gives coords for bounding box
        (x, y, w, h) = [int(i) for i in box]
        #draw it
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        #gives the pos of the center of the object to later show its prev positions
        centerOfRectangle = (int(x + w/2), int(y + h/2))
        #we append the the center of the object to later then be able to draw prev positions
        centerPoints.append(centerOfRectangle)
        #go thru the list of center points
        for i in range(len(centerPoints)):
            # we are drawing lines through the first point recorded to the most recent
            # this if statement makes sure that we dont connect the last point to the first creating a polygon
            if (i - 1) == -1:
                continue
            # connect points with a line
            cv2.line(frame, pt1 = centerPoints[i - 1], pt2 = centerPoints[i], color = (0, 0, 255), thickness = 2)
        #this circle drawn in the center shows the center
        cv2.circle(img = frame, center = centerOfRectangle, radius = 3, color = (0, 255, 0), thickness = -1)
        
        #write this frame to output video
        # videoWriter.write(frame)
        #show the frame
        cv2.imshow("Frame", frame)

        #this code allows us to assign a key that would break the object tracking
        #in this use case it is not needed but it is nice to have
        # KEY IS "q"
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        
        # print(centerOfRectangle)
        times.append(t)
        t += 1/fps


df = pd.DataFrame()
df['Time (s)'] = times.copy()
df['Camera_S_X'] = [pt[0] for pt in centerPoints]
df['Camera_S_Z'] = [pt[1] for pt in centerPoints]

plate_diameter = open('plate_diameter.txt') 
diameter = plate_diameter.readline()

scale = (int)(diameter) / W / 100 # cm -> m

# position (m)
df['Camera_S_X'] = (df['Camera_S_X'] - df['Camera_S_X'][0]) * scale
df['Camera_S_Z'] = (df['Camera_S_Z'] - df['Camera_S_Z'][0]) * scale

if np.mean(df['Camera_S_X']) < 0: df['Camera_S_X'] *= -1
df['Camera_S_Z'] *= -1

# timestep
dt = df['Time (s)'][1] - df['Time (s)'][0]
# velocity (m/s)
df['Camera_V_X'] = np.gradient(df['Camera_S_X'], dt)
df['Camera_V_Z'] = np.gradient(df['Camera_S_Z'], dt)
# acceleration (m /s /s)
df['Camera_A_X'] = np.gradient(df['Camera_V_X'], dt) # 
df['Camera_A_Z'] = np.gradient(df['Camera_V_Z'], dt) # 

df.to_csv(output_path + outputName + '.csv', index=False)

#closes video, and writer when done
# videoWriter.release()
video.release()
cv2.destroyAllWindows()    

