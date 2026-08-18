import time
import csv
import os
from telemetry import TelemetrySystem

def main():
    print("Starting Flight Telemetry Logger...")
    os.makedirs("data", exist_ok=True)
    log_file = "data/raw_flight_telemetry.csv"
    
    # Connect to Pixhawk
    telem = TelemetrySystem(mode="LIVE", port="/dev/ttyTHS1")
    
    # Open CSV for writing
    with open(log_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "lat", "lon", "alt", "roll", "pitch", "yaw"])
        
        print(f"Logging live data to {log_file}. Press Ctrl+C to stop.")
        try:
            while True:
                telem.update()
                
                # Get the absolute latest data directly from the buffer
                with telem.lock:
                    if not telem.data_buffer:
                        continue
                    latest_data = telem.data_buffer[-1]
                
                # Save it with the Jetson's exact system time
                writer.writerow([
                    latest_data['timestamp'],
                    latest_data.get('lat', 0.0),
                    latest_data.get('lon', 0.0),
                    latest_data.get('alt', 0.0),
                    latest_data.get('roll', 0.0),
                    latest_data.get('pitch', 0.0),
                    latest_data.get('yaw', 0.0)
                ])
                
                # Log at roughly 30Hz to match standard video framerates
                time.sleep(0.033)
                
        except KeyboardInterrupt:
            print("\nFlight logging stopped. Data saved successfully!")

if __name__ == "__main__":
    main()