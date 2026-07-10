import os
import time
import math
import cv2
from vision import FlagDetector
from telemetry import TelemetrySystem
from storage import DataLogger
from geolocation import GeoLocator

# Configuration
MODE = os.getenv("DRONE_MODE", "MOCK") 
CAMERA_LATENCY_OFFSET = 0.4  

# Minimum distance (in meters) required before logging a NEW flag
MIN_FLAG_DISTANCE = 10.0  

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculates distance in meters between two GPS coordinates using Haversine"""
    if lat1 == 0 or lat2 == 0: return 9999 # Fallback if no GPS lock yet
    
    R = 6371000 # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def main():
    print(f"Starting Drone Mission System in {MODE} mode...")
    
    detector = FlagDetector()
    logger = DataLogger()
    locator = GeoLocator(image_width=1920, image_height=1080)

    # We now keep a LIST of all logged targets to handle multiple flags cleanly
    logged_targets = []
    
    # Initialize Inputs
    if MODE == "LIVE":
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
        telem.update()
        
        ret, frame = cap.read()
        if not ret:
            if MODE == "MOCK":
                break
            continue
            
        frame_timestamp = time.time() - CAMERA_LATENCY_OFFSET
        
        flag_found, bounding_boxes = detector.detect(frame)
        
        if flag_found:
            sync_data = telem.get_data_at_time(frame_timestamp)
            drone_lat = float(sync_data.get('lat', 0.0))
            drone_lon = float(sync_data.get('lon', 0.0))
            alt = float(sync_data.get('alt', 0.0))
            roll = float(sync_data.get('roll', 0.0))
            pitch = float(sync_data.get('pitch', 0.0))
            yaw = float(sync_data.get('yaw', 0.0))
            
            for (x1, y1, x2, y2, track_id) in bounding_boxes:
                # Get the exact center pixel of the bounding box
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # 1. Use the new 3D locator with roll, pitch, AND yaw
                flag_lat, flag_lon = locator.pixel_to_gps(
                    center_x, center_y, drone_lat, drone_lon, alt, roll, pitch, yaw
                )

                # 2. Check if this flag is far enough away from ALL previously logged flags
                is_new_flag = True
                for logged_lat, logged_lon in logged_targets:
                    dist = calculate_distance(logged_lat, logged_lon, flag_lat, flag_lon)
                    if dist < MIN_FLAG_DISTANCE:
                        is_new_flag = False
                        break # We already logged a flag this close, stop checking
                        
                # 3. Log it if it's genuinely a new location
                if is_new_flag:
                    # Make a unique dictionary copy for this specific target so 
                    # multiple flags in one frame don't overwrite each other's data
                    target_data = sync_data.copy()
                    target_data['target_lat'] = flag_lat
                    target_data['target_lon'] = flag_lon
                    
                    logger.save_detection(frame, frame_timestamp, target_data)
                    print(f"[MISSION] NEW Target (ID: {track_id}) logged at {flag_lat:.6f}, {flag_lon:.6f}")
                    
                    # Add to our historical list so we don't log it again
                    logged_targets.append((flag_lat, flag_lon))

        if MODE == "MOCK":
            cv2.imshow("Detection Preview", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.03)

    if MODE == "MOCK":
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()