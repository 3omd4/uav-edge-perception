import time
import math
import cv2
from vision import FlagDetector
from telemetry import OfflineTelemetry
from storage import DataLogger
from geolocation import GeoLocator

# Configuration
MIN_FLAG_DISTANCE = 10.0  

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculates distance in meters between two GPS coordinates using Haversine"""
    if lat1 == 0 or lat2 == 0: return 9999 
    
    R = 6371000 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def main():
    print("Starting Post-Flight Analysis...")
    
    detector = FlagDetector()
    logger = DataLogger()
    locator = GeoLocator(image_width=1920, image_height=1080)
    logged_targets = []
    
    # 1. Point to the files in your data folder
    # VIDEO_PATH = "data/flight_video.mp4"       
    # TELEMETRY_PATH = "data/raw_flight_telemetry.csv" 
    VIDEO_PATH = "mock_data/test_video2.mp4"
    TELEMETRY_PATH = "mock_data/test_telemetry.csv"
    
    cap = cv2.VideoCapture(VIDEO_PATH)
    telem = OfflineTelemetry(TELEMETRY_PATH)

    if not cap.isOpened():
        print(f"Error: Could not open {VIDEO_PATH}")
        return

    print("Files loaded. Crunching data...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Finished analyzing the entire flight!")
            break
            
        # 2. THE SYNC MATH
        # Get exact video playback time in seconds
        video_time_seconds = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        
        # Calculate the exact real-world timestamp for this frame
        frame_timestamp = telem.start_time + video_time_seconds
        
        flag_found, bounding_boxes = detector.detect(frame)
        
        if flag_found:
            # 3. Pull the telemetry for this exact millisecond
            sync_data = telem.get_data_at_time(frame_timestamp)
            drone_lat = float(sync_data.get('lat', 0.0))
            drone_lon = float(sync_data.get('lon', 0.0))
            alt = float(sync_data.get('alt', 0.0))
            roll = float(sync_data.get('roll', 0.0))
            pitch = float(sync_data.get('pitch', 0.0))
            yaw = float(sync_data.get('yaw', 0.0))
            
            for (x1, y1, x2, y2, track_id) in bounding_boxes:
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                flag_lat, flag_lon = locator.pixel_to_gps(
                    center_x, center_y, drone_lat, drone_lon, alt, roll, pitch, yaw
                )

                is_new_flag = True
                for logged_lat, logged_lon in logged_targets:
                    if calculate_distance(logged_lat, logged_lon, flag_lat, flag_lon) < MIN_FLAG_DISTANCE:
                        is_new_flag = False
                        break 
                        
                if is_new_flag:
                    target_data = sync_data.copy()
                    target_data['target_lat'] = flag_lat
                    target_data['target_lon'] = flag_lon
                    
                    logger.save_detection(frame, frame_timestamp, target_data)
                    print(f"[MISSION] NEW Target (ID: {track_id}) logged at {flag_lat:.6f}, {flag_lon:.6f}")
                    logged_targets.append((flag_lat, flag_lon))

        # 4. Turn the preview window back on for the laptop!
        cv2.putText(frame, f"Active Targets: {len(bounding_boxes) if flag_found else 0}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Post-Flight Analysis", frame)
        
        # Press 'q' to quit early if needed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()