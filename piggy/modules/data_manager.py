import time
import json
import os
from datetime import datetime

class DataManager:
    def __init__(self):
        self.movement_patterns = []
        self.basket_history = []
        self.history_max = 6
        self.load_existing_patterns()

    def load_existing_patterns(self):
        """Load existing patterns from previous runs"""
        try:
            if os.path.exists('training_data/ai_learning.json'):
                print("\nLoading existing patterns...")
                with open('training_data/ai_learning.json', 'r') as f:
                    data = json.load(f)
                    existing_patterns = data.get('patterns', [])
                    self.movement_patterns = existing_patterns
                    print(f"Loaded {len(existing_patterns)} existing patterns")
        except Exception as e:
            print(f"Error loading existing patterns: {e}")

    def update_history(self, position, current_time):
        """Update position history and learn movement patterns"""
        self.basket_history.append((position[0], position[1], current_time))
        if len(self.basket_history) > self.history_max:
            self.basket_history.pop(0)
            
        if len(self.basket_history) >= 2:
            prev = self.basket_history[-2]
            curr = self.basket_history[-1]
            
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            dt = curr[2] - prev[2]
            
            if dt > 0:
                pattern = {
                    'dx': dx,
                    'dy': dy,
                    'speed': (dx*dx + dy*dy)**0.5 / dt,
                    'direction': 1 if dx > 0 else -1,
                    'height': curr[1],
                    'timestamp': current_time
                }
                self.movement_patterns.append(pattern)

    def save_patterns(self, frame_count, save_type=""):
        """Save collected patterns to file"""
        try:
            os.makedirs('training_data', exist_ok=True)
            data = {
                'patterns': self.movement_patterns,
                'metadata': {
                    'total_frames': frame_count,
                    'total_patterns': len(self.movement_patterns),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            filename = 'training_data/ai_learning.json'
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            
            print(f"\n{save_type.title()} complete!")
            print(f"Total frames: {frame_count}")
            print(f"Patterns learned: {len(self.movement_patterns)}")
            print(f"Data saved to: {filename}")
            
        except Exception as e:
            print(f"\nError saving data: {e}")
            emergency_file = f'training_data/emergency_save_{int(time.time())}.json'
            with open(emergency_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Emergency save created: {emergency_file}") 