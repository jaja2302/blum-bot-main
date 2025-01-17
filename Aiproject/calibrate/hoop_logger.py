import json
import time
from datetime import datetime
from pathlib import Path
import numpy as np
from enum import Enum
import hashlib

class HoopMovement(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    STATIONARY = "STATIONARY"
    CENTER = "CENTER"

class HoopLogger:
    def __init__(self):
        self.logs = []
        self.last_pos = None
        self.last_time = None
        self.game_start_time = None
        self.movement_threshold = 5
        self.center_threshold = 30
        self.log_folder = Path("hoop_logs")
        self.log_folder.mkdir(exist_ok=True)
        self.movement_patterns_file = self.log_folder / "movement_patterns.json"
        self.existing_patterns = self.load_existing_patterns()
        
    def load_existing_patterns(self):
        """Load existing movement patterns from file"""
        if self.movement_patterns_file.exists():
            try:
                with open(self.movement_patterns_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
        
    def generate_pattern_hash(self, movements):
        """Generate a unique hash for a movement pattern"""
        movement_str = json.dumps(movements, sort_keys=True)
        return hashlib.md5(movement_str.encode()).hexdigest()
        
    def start_new_game(self):
        """Start logging a new game"""
        self.logs = []
        self.last_pos = None
        self.last_time = None
        self.game_start_time = time.time()
        
    def log_position(self, hoop_pos, screen_width):
        """Log the hoop position and calculate metrics"""
        current_time = time.time()
        x, y = hoop_pos
        screen_center = screen_width // 2
        
        # Calculate time since game start
        time_since_start = current_time - (self.game_start_time or current_time)
        
        # Initialize movement data
        movement_data = {
            "timestamp": time_since_start,
            "position": {"x": x, "y": y},
            "speed": 0,
            "acceleration": 0,
            "movement": HoopMovement.STATIONARY,
            "distance_from_center": x - screen_center
        }
        
        # Calculate speed and movement direction
        if self.last_pos and self.last_time:
            dx = x - self.last_pos[0]
            dt = current_time - self.last_time
            
            if dt > 0:
                speed = dx / dt
                movement_data["speed"] = speed
                
                # Determine movement direction
                if abs(dx) > self.movement_threshold:
                    movement_data["movement"] = (
                        HoopMovement.RIGHT if dx > 0 
                        else HoopMovement.LEFT
                    )
                elif abs(x - screen_center) < self.center_threshold:
                    movement_data["movement"] = HoopMovement.CENTER
                
                # Calculate acceleration if we have previous speed
                if len(self.logs) > 0:
                    prev_speed = self.logs[-1]["speed"]
                    movement_data["acceleration"] = (speed - prev_speed) / dt
        
        self.logs.append(movement_data)
        self.last_pos = hoop_pos
        self.last_time = current_time
        
    def save_logs(self):
        """Save the collected logs to a JSON file"""
        if not self.logs:
            return
            
        # Calculate summary statistics
        speeds = [log["speed"] for log in self.logs]
        accelerations = [log["acceleration"] for log in self.logs]
        movements = [str(log["movement"]) for log in self.logs]  # Convert Enum to str
        
        # Create movement pattern summary
        movement_summary = {
            "sequence": movements,
            "total_time": self.logs[-1]["timestamp"],
            "average_speed": float(np.mean(speeds)),
            "max_speed": float(max(speeds)),
            "average_acceleration": float(np.mean(accelerations)),
            "movement_counts": {
                str(movement): movements.count(str(movement))
                for movement in HoopMovement
            }
        }
        
        # Generate pattern hash
        pattern_hash = self.generate_pattern_hash(movement_summary)
        
        # Check if this pattern already exists
        if pattern_hash not in self.existing_patterns:
            # Save new pattern
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pattern_data = {
                "id": pattern_hash,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "occurrence_count": 1,
                "pattern_data": movement_summary,
                "detailed_logs": self.logs
            }
            
            self.existing_patterns[pattern_hash] = pattern_data
            
            # Save to individual file
            pattern_file = self.log_folder / f"pattern_{pattern_hash[:8]}_{timestamp}.json"
            with open(pattern_file, 'w') as f:
                json.dump(pattern_data, f, indent=2)
                print(f"\nNew movement pattern detected and saved: {pattern_file}")
        else:
            # Update existing pattern
            self.existing_patterns[pattern_hash]["last_seen"] = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.existing_patterns[pattern_hash]["occurrence_count"] += 1
            print(f"\nExisting movement pattern detected (ID: {pattern_hash[:8]}, "
                  f"Occurrences: {self.existing_patterns[pattern_hash]['occurrence_count']})")
        
        # Save updated patterns database
        with open(self.movement_patterns_file, 'w') as f:
            json.dump(self.existing_patterns, f, indent=2) 