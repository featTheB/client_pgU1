import numpy as np
import cv2
import time
import math
import os


class VideoProcessing():
    def __init__(self, cameraPort=0):
        self.cameraPort = cameraPort
        self.pastCentroidX = 1
        self.pastCentroidY = 1
        self.roi =50
        self.rpc = 0.0015 # radian per pixel
        self.ro = 0.01 # radian error
        self.hCameraLaser = 25
        self.distance = 0
    def camera_config(self):
        """start the camera"""
        self.cap = cv2.VideoCapture(self.cameraPort)
        return self.cap
    def laserColor(self):
        """get the color of the laser from the laserConfig file  in the hsv descriptor the red is in the upper end 
        and the lower end so that why there is for boundries"""
        with open(os.path.join('calibration','laserColor.txt'), 'r') as file:

            text = file.readlines()
            color = []
            for line in text:
                if line != '':
                    start = line.find(':') + 1
                    end = line.find(';')
                    substring = line[start:end]
                    hsv = substring.split(',')

                    color.append([float(hsv[0]), float(hsv[1]), float(hsv[2])])
                else:
                    break

            self.upperRedUp = color[0]
            # hsv range are h:0-360, s:0-100, v:0-100 and openCv hsv range are h:0-180, s:0-255, v:0-255
            self.upperRedUp[0] = self.upperRedUp[0] / 2
            self.upperRedUp[1] = self.upperRedUp[1] * (255 / 100)
            self.upperRedUp[2] = self.upperRedUp[2] * (255 / 100)
            self.upperRedUp = np.array(self.upperRedUp)
            
            self.upperRedLow = color[1]
            self.upperRedLow[0] = self.upperRedLow[0] / 2
            self.upperRedLow[1] = self.upperRedLow[1] * (255 / 100)
            self.upperRedLow[2] = self.upperRedLow[2] * (255 / 100)
            self.upperRedLow = np.array(self.upperRedLow)
            
            self.lowerRedUp = color[2]
            self.lowerRedUp[0] = self.lowerRedUp[0] / 2
            self.lowerRedUp[1] = self.lowerRedUp[1] * (255 / 100)
            self.lowerRedUp[2] = self.lowerRedUp[2] * (255 / 100)
            self.lowerRedUp = np.array(self.lowerRedUp)
            
            self.lowerRedLow = color[3]
            self.lowerRedLow[0] = self.lowerRedLow[0] / 2
            self.lowerRedLow[1] = self.lowerRedLow[1] * (255 / 100)
            self.lowerRedLow[2] = self.lowerRedLow[2] * (255 / 100)
            self.lowerRedLow = np.array(self.lowerRedLow)
            
    def configLaserColor(self, upperRedUp, upperRedLow, lowerRedUp, lowerRedLow):
        """ change the color range of the laser"""
        text = 'upper Red Up :{};\nupper Red low:{};\nlower Red Up :{};\nlower Red low:{};'.format(
            upperRedUp, upperRedLow, lowerRedUp, lowerRedLow)
        print(text)
        with open('calibration\laserColor.txt', 'w') as file:
            file.write(text)

    def run_camera_debug(self):
        """run the camera for the debuging"""
        self.laserColor()
        while True:
            self.ret, self.frame = self.cap.read()
            mask, res = self.distanceDetection()[0:2]
            print("the laser is {} mm away".format(self.distance))
            k = cv2.waitKey(5) & 0xFF
            cv2.imshow('frame', self.frame)
            cv2.imshow('mask',mask)
            cv2.imshow('res',res)             
            if k == 27:
                break

        cv2.destroyAllWindows()
        self.cap.release()

    def distanceDetection(self):
        """find the distance between the camera and the laser"""
        hsvFrame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)

        maskUp = cv2.inRange(hsvFrame, self.lowerRedUp, self.upperRedUp)

        maskLow = cv2.inRange(hsvFrame, self.lowerRedLow, self.upperRedLow)

        mask = cv2.bitwise_or(maskUp, maskLow)
        res = cv2.bitwise_and(self.frame, self.frame, mask=mask)
        
        centerFrameY = int(round(mask.shape[0]/2))
        centerFrameX = int(round(mask.shape[1]/2))        
        
        x1 = centerFrameX-self.roi
        x2 = centerFrameX+self.roi
        
        y1 = centerFrameY-self.roi
        y2 = centerFrameY+self.roi
        maskAnalyse = mask[y1:y2,x1:x2]
        newMask = np.zeros((mask.shape[0],mask.shape[1]))
        newMask[y1:y2,x1:x2] = maskAnalyse
        
        laserPos = np.nonzero(newMask)
        cv2.rectangle(self.frame, (x1, y1), (x2, y2), (0,255,0), 2)
        
        centroidY = round(np.average(laserPos[0])) 
        centroidX = round(np.average(laserPos[1])) 
        
        if math.isnan(centroidX) or math.isnan(centroidY):
            centroidX = self.pastCentroidX
            centroidY =self.pastCentroidY
        else:
            centroidX,centroidY = (int(centroidX),int(centroidY))
        

        cv2.circle(self.frame, (centerFrameX, centerFrameY), 5, (255, 0, 0),-1)
        cv2.circle(self.frame, (centroidX, centroidY), 5, (0, 0, 255),-1)
        
        deltaCentreLaser = centerFrameY - centroidY
        theta =deltaCentreLaser*self.rpc+self.ro
        self.distance = self.hCameraLaser/math.tan(theta)
        
        return (mask,res,deltaCentreLaser)
    def calibration_theta_distance(self,nb):
        self.laserColor()
        for i in range(nb):
            self.cap = cv2.VideoCapture(self.cameraPort)
            self.ret, self.frame = self.cap.read()
            result = self.distanceDetection()[2]
            print('distance between laser and center of frame = {}'.format(result))
            cv2.imshow('frame', self.frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            self.cap.release()            
        
    def kill_camera(self):

        cv2.destroyAllWindows()
        self.cap.release()
