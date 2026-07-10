import cv2
import numpy as np

class FlagDetector:
    def __init__(self, min_area=40, max_area=4000):
        self.min_area = min_area
        self.max_area = max_area

        # Sand model: low-to-moderate saturation, warm hue band, mid-to-high value
        self.sand_hue_low, self.sand_hue_high = 10, 30
        self.sand_sat_max = 90      # sand is fairly desaturated
        self.sand_val_range = (60, 255)

        # Shape filters
        self.min_solidity = 0.55     # flags/cloth are fairly convex, not raggedy like shadows
        self.min_extent = 0.25
        self.max_aspect_ratio = 6.0  # reject long thin tracks/cracks

    def _sand_mask(self, hsv):
        h, s, v = cv2.split(hsv)
        hue_ok = (h >= self.sand_hue_low) & (h <= self.sand_hue_high)
        sat_ok = s <= self.sand_sat_max
        val_ok = (v >= self.sand_val_range[0]) & (v <= self.sand_val_range[1])
        return (hue_ok & sat_ok & val_ok).astype(np.uint8) * 255

    def detect(self, frame):
        blurred = cv2.GaussianBlur(frame, (3, 3), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        sand_mask = self._sand_mask(hsv)
        anomaly_mask = cv2.bitwise_not(sand_mask)

        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(anomaly_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if not (self.min_area < area < self.max_area):
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = max(w, h) / max(1, min(w, h))
            if aspect_ratio > self.max_aspect_ratio:
                continue

            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            if solidity < self.min_solidity:
                continue

            extent = area / (w * h) if w * h > 0 else 0
            if extent < self.min_extent:
                continue

            detections.append((x, y, w, h))
            cv2.rectangle(frame, (x-10, y-10), (x + w+10, y + h+10), (0, 255, 0), 2)
            cv2.putText(frame, "Target", (x, max(0, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return len(detections) > 0, detections