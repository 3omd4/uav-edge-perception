import cv2
import numpy as np

# Note: Make sure sort.py is in your directory, or you have it installed
from sort import Sort 

class FlagDetector:
    def __init__(self, max_age=3, min_hits=10, iou_threshold=0.1, blur_threshold=25):
        # Initialize the SORT tracker for cross-frame temporal validation
        self.tracker = Sort(max_age=max_age, min_hits=min_hits, iou_threshold=iou_threshold)
        self.blur_threshold = blur_threshold

    def _calculate_blurriness(self, image):
        """Calculates the variance of the Laplacian to measure focus/blur"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def _get_raw_boxes(self, image):
        """Extracts candidate boxes using HLS edge detection"""
        H, _, S = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HLS))
        kernel = np.ones((3, 3), np.uint8)

        edges_S = cv2.dilate(
            cv2.Canny(S, 35, 140), kernel, borderType=cv2.BORDER_REPLICATE, iterations=3
        )
        edges_H = cv2.dilate(
            cv2.Canny(H, 20, 55), kernel, borderType=cv2.BORDER_REPLICATE, iterations=3
        )

        # Combine bitwise AND and dilation
        binary_image = cv2.dilate(
            cv2.bitwise_and(edges_H, edges_S),
            kernel,
            borderType=cv2.BORDER_REPLICATE,
            iterations=3,
        )

        contours, _ = cv2.findContours(
            binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        boxes = []
        for cont in contours:
            x, y, w, h = cv2.boundingRect(cont)
            # Filter non-square shapes (h/w should be near 1.0)
            if 0.7 < (h / w) < 1.3:
                boxes.append((x, y, w, h))
                
        return boxes

    def detect(self, frame):
        # 1. Blur Check (Currently disabled in your script, but ready to use)
        # blurry = self._calculate_blurriness(frame)
        # if blurry > self.blur_threshold:
        #     # Image is too blurry, skip tracking this frame
        #     return False, []
            
        # 2. Get Raw Detections
        raw_boxes = self._get_raw_boxes(frame)
        
        # 3. Format for SORT [x1, y1, x2, y2, score]
        tracks_input = []
        for x, y, w, h in raw_boxes:
            tracks_input.append([x, y, x + w, y + h, 1.0])
            
        # 4. Update Tracker
        # (SORT requires us to pass an empty array if nothing was found)
        if len(tracks_input) > 0:
            tracked_objects = self.tracker.update(np.array(tracks_input))
        else:
            tracked_objects = self.tracker.update(np.empty((0, 5)))
            
        detections = []
        
        # 5. Process Confirmed Tracks and Draw
        for track in tracked_objects:
            x1, y1, x2, y2, track_id = track.astype(int)
            detections.append((x1, y1, x2, y2, track_id))
            
            # Draw the bounding box
            cv2.rectangle(frame, (x1-10, y1-10), (x2+10, y2+10), color=(255, 0, 0), thickness=2)
            
            # Draw the ID
            cv2.putText(
                frame,
                f"ID: {track_id}",
                (x1, y1 - 10),
                fontFace=cv2.FONT_HERSHEY_PLAIN,
                fontScale=2,
                color=(255, 0, 0),
                thickness=2,
            )

        # Returns True if at least one tracked, confirmed object exists
        return len(detections) > 0, detections