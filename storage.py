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
                # UPDATED HEADERS: Now includes both the Drone's location AND the Target's location
                writer.writerow([
                    "Timestamp", "Filename", 
                    "Drone_Lat", "Drone_Lon", "Drone_Alt", 
                    "Roll", "Pitch", "Yaw",
                    "Target_Lat", "Target_Lon"
                ])

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
                timestamp, 
                filename, 
                telemetry_data.get('lat', 0.0), 
                telemetry_data.get('lon', 0.0), 
                telemetry_data.get('alt', 0.0),
                telemetry_data.get('roll', 0.0), 
                telemetry_data.get('pitch', 0.0), 
                telemetry_data.get('yaw', 0.0),
                # Pull the calculated target coordinates we added in main.py
                telemetry_data.get('target_lat', 0.0),
                telemetry_data.get('target_lon', 0.0)
            ])