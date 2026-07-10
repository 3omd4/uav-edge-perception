import time
import csv
from pymavlink import mavutil

class TelemetrySystem:
    def __init__(self, mode="LIVE", port="/dev/ttyTHS1", baud=57600):
        self.mode = mode
        self.history = [] # Stores (timestamp, data_dict)
        self.max_history_len = 100 # Keep last 100 readings
        
        if self.mode == "LIVE":
            print(f"Connecting to Pixhawk on {port}...")
            self.master = mavutil.mavlink_connection(port, baud=baud)
            self.master.wait_heartbeat()
            print("Pixhawk connected!")
        else:
            print("Loading Mock Telemetry...")
            self.mock_data = self._load_mock_data("mock_data/test_telemetry.csv")
            self.mock_index = 0

    def _load_mock_data(self, filepath):
        # Load a pre-recorded CSV for simulation
        data = []
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        except FileNotFoundError:
            print("[WARNING] Mock telemetry file not found. Using static zeroes.")
        return data

    def update(self):
        """Called constantly in the main loop to read the latest Pixhawk data"""
        current_time = time.time()
        data = {'lat': 0, 'lon': 0, 'alt': 0, 'roll': 0, 'pitch': 0, 'yaw': 0}
        
        if self.mode == "LIVE":
            # Fetch latest MAVLink messages
            msg = self.master.recv_match(type=['GLOBAL_POSITION_INT', 'ATTITUDE'], blocking=False)
            if msg:
                if msg.get_type() == 'GLOBAL_POSITION_INT':
                    data['lat'] = msg.lat / 1e7
                    data['lon'] = msg.lon / 1e7
                    data['alt'] = msg.relative_alt / 1000.0 # meters
                elif msg.get_type() == 'ATTITUDE':
                    data['roll'] = msg.roll
                    data['pitch'] = msg.pitch
                    data['yaw'] = msg.yaw
        else:
            # Simulate fetching data
            if self.mock_data and self.mock_index < len(self.mock_data):
                data = self.mock_data[self.mock_index]
                self.mock_index += 1

        # Store in rolling buffer
        self.history.append((current_time, data))
        if len(self.history) > self.max_history_len:
            self.history.pop(0)

    def get_data_at_time(self, target_timestamp):
        """Finds the telemetry data closest to the camera frame's timestamp"""
        if not self.history:
            return {'lat': 0, 'lon': 0, 'alt': 0, 'roll': 0, 'pitch': 0, 'yaw': 0}
            
        # Find the telemetry entry closest to our target timestamp
        closest_entry = min(self.history, key=lambda x: abs(x[0] - target_timestamp))
        return closest_entry[1]