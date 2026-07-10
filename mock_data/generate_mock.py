import csv
import math
import os

# Ensure the mock_data directory exists
os.makedirs("mock_data", exist_ok=True)
filepath = "mock_data/test_telemetry.csv"

# Simulation Parameters
start_lat = 29.979200  # Example: Near the Pyramids of Giza
start_lon = 31.134200
altitude = 60.0        # 60 meters high
speed = 0.000001       # Rough GPS degree offset per "tick" (moving North)
frames = 2000          # How many rows of data to generate

print(f"Generating {frames} frames of mock telemetry...")

with open(filepath, mode='w', newline='') as f:
    writer = csv.writer(f)
    
    # Header MUST match the keys used in telemetry.py
    writer.writerow(["lat", "lon", "alt", "roll", "pitch", "yaw"])
    
    for i in range(frames):
        # 1. Simulate forward movement (Latitude increasing)
        current_lat = start_lat + (i * speed)
        current_lon = start_lon
        
        # 2. Simulate Drone Wobble (using sine waves for smooth oscillating values)
        # Pitch: Drone is tilted forward 10 degrees (0.17 rad) to fly, wobbling slightly
        pitch = -0.17 + (math.sin(i / 10.0) * 0.02)
        
        # Roll: Slight left/right wind buffering
        roll = math.cos(i / 15.0) * 0.03
        
        # Yaw: Pointing straight North (0 radians)
        yaw = 0.0
        
        writer.writerow([current_lat, current_lon, altitude, roll, pitch, yaw])

print(f"Done! Saved to {filepath}")