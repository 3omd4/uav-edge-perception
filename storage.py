import cv2
import os
import csv
from datetime import datetime

class DataLogger:
    def __init__(self, base_dir="data"):
        self.frames_dir = os.path.join(base_dir, "frames")
        self.log_file = os.path.join(base_dir, "flight_logs.csv")
        
        # Ensure directories exist
        os.makedirs(self.frames_dir, exist_ok=True)
        
        # Create CSV header if file doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Filename", "Lat", "Lon", "Alt", "Roll", "Pitch", "Yaw"])

    def save_detection(self, frame, timestamp, telemetry_data):
        # Format timestamp for filename
        dt_str = datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f"flag_{dt_str}.jpg"
        filepath = os.path.join(self.frames_dir, filename)
        
        # Save Image
        cv2.imwrite(filepath, frame)
        
        # Save CSV Data
        with open(self.log_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, filename, 
                telemetry_data.get('lat', 0), telemetry_data.get('lon', 0), telemetry_data.get('alt', 0),
                telemetry_data.get('roll', 0), telemetry_data.get('pitch', 0), telemetry_data.get('yaw', 0)
            ])
        print(f"[LOG] Saved detection: {filename} at Lat/Lon: {telemetry_data.get('lat')}, {telemetry_data.get('lon')}")