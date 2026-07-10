import os
import time
import cv2
from vision import FlagDetector
from telemetry import TelemetrySystem
from storage import DataLogger

# Configuration
MODE = os.getenv("DRONE_MODE", "MOCK") # Set to "LIVE" on the Jetson
CAMERA_LATENCY_OFFSET = 0.4  # Seconds. Adjust based on your GoPro setup

def main():
    print(f"Starting Drone Mission System in {MODE} mode...")
    
    detector = FlagDetector()
    logger = DataLogger()
    
    # Initialize Inputs
    if MODE == "LIVE":
        # Adjust 0 to your video capture device index or GStreamer pipeline
        cap = cv2.VideoCapture(0) 
        telem = TelemetrySystem(mode="LIVE", port="/dev/ttyTHS1")
    else:
        cap = cv2.VideoCapture("mock_data/test_video.mp4")
        telem = TelemetrySystem(mode="MOCK")

    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    print("System Initialized. Starting mission loop...")
    
    while True:
        # 1. Update Telemetry continuously
        telem.update()
        
        # 2. Grab Frame
        ret, frame = cap.read()
        if not ret:
            if MODE == "MOCK":
                print("End of test video.")
                break
            continue
            
        # The true time the frame was captured (accounting for GoPro delay)
        frame_timestamp = time.time() - CAMERA_LATENCY_OFFSET
        
        # 3. Process Vision
        if detector.detect(frame):
            # 4. If flag found, get telemetry for THAT EXACT past timestamp
            sync_data = telem.get_data_at_time(frame_timestamp)
            
            # 5. Save everything
            logger.save_detection(frame, frame_timestamp, sync_data)
            
            # Sleep briefly to avoid saving 30 frames of the same flag in one second
            time.sleep(1.0) 

        # Add a small sleep in MOCK mode so it doesn't process the video at 1000fps
        if MODE == "MOCK":
            time.sleep(0.03)

if __name__ == "__main__":
    main()