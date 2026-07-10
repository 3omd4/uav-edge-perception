import math
import numpy as np

class GeoLocator:
    def __init__(self, image_width=1920, image_height=1080, hfov_deg=94.4):
        self.width = image_width
        self.height = image_height
        
        self.hfov = math.radians(hfov_deg)
        self.vfov = 2 * math.atan(math.tan(self.hfov / 2) * (image_height / image_width))
        
        self.R = 6378137.0 # Earth radius in meters

    def get_rotation_matrix(self, roll, pitch, yaw):
        """Creates a 3D rotation matrix from Roll, Pitch, and Yaw (in radians)"""
        # Roll (Rotation around X axis)
        Rx = np.array([
            [1, 0, 0],
            [0, math.cos(roll), -math.sin(roll)],
            [0, math.sin(roll), math.cos(roll)]
        ])
        
        # Pitch (Rotation around Y axis)
        Ry = np.array([
            [math.cos(pitch), 0, math.sin(pitch)],
            [0, 1, 0],
            [-math.sin(pitch), 0, math.cos(pitch)]
        ])
        
        # Yaw (Rotation around Z axis)
        Rz = np.array([
            [math.cos(yaw), -math.sin(yaw), 0],
            [math.sin(yaw), math.cos(yaw), 0],
            [0, 0, 1]
        ])
        
        # Combined rotation: Yaw * Pitch * Roll
        return Rz @ Ry @ Rx

    def pixel_to_gps(self, pixel_x, pixel_y, drone_lat, drone_lon, alt_m, roll_rad, pitch_rad, yaw_rad):
        if alt_m <= 0:
            return drone_lat, drone_lon 
            
        # 1. Center the pixel coordinates
        cx = pixel_x - (self.width / 2)
        cy = pixel_y - (self.height / 2)
        
        # 2. Calculate angles from center
        angle_x = cx * (self.hfov / self.width)
        angle_y = cy * (self.vfov / self.height)
        
        # 3. Create a 3D vector for the camera ray
        # In standard drone NED (North, East, Down) coordinates:
        # Camera X (Right) maps to Drone Y (East)
        # Camera Y (Down in image) maps to Drone -X (Backward/South)
        # Camera Z (Optical Axis) maps to Drone +Z (Down)
        cam_vector = np.array([
            -math.tan(angle_y), # X: Forward/Backward
            math.tan(angle_x),  # Y: Left/Right
            1.0                 # Z: Down
        ])
        
        # 4. Rotate the vector using the drone's actual IMU attitude
        R = self.get_rotation_matrix(roll_rad, pitch_rad, yaw_rad)
        rotated_vector = R @ cam_vector
        
        # 5. Prevent divide-by-zero if the drone is banking beyond 90 degrees
        if rotated_vector[2] <= 0.01:
            return drone_lat, drone_lon
            
        # 6. Scale the vector so its Down (Z) component matches our actual Altitude
        scale = alt_m / rotated_vector[2]
        offset_north = rotated_vector[0] * scale
        offset_east = rotated_vector[1] * scale
        
        # 7. Apply meter offsets to GPS
        d_lat = offset_north / self.R
        d_lon = offset_east / (self.R * math.cos(math.pi * drone_lat / 180))
        
        flag_lat = drone_lat + (d_lat * 180 / math.pi)
        flag_lon = drone_lon + (d_lon * 180 / math.pi)
        
        return flag_lat, flag_lon