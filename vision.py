import cv2
import numpy as np

class FlagDetector:
    def __init__(self):
        # Tune these HSV values based on the specific sand color in your environment
        self.lower_sand = np.array([15, 50, 50])
        self.upper_sand = np.array([35, 255, 255])
        
        # Minimum area (in pixels) to be considered a flag from 50m up
        self.min_area = 50 
        self.max_area = 3000

    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create mask for sand, then invert to find anomalies (flags)
        sand_mask = cv2.inRange(hsv, self.lower_sand, self.upper_sand)
        non_sand_mask = cv2.bitwise_not(sand_mask)
        
        # Clean up noise
        kernel = np.ones((5,5), np.uint8)
        cleaned_mask = cv2.morphologyEx(non_sand_mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_area < area < self.max_area:
                return True
                
        return False