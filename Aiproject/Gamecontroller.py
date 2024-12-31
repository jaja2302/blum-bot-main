import numpy as np
import math
import time
import cv2
from collections import deque
from pynput.mouse import Button, Controller
import random
import os
import json
from datetime import datetime
from pathlib import Path
import hashlib

class GameplayController:
    def __init__(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'setting_controller.json')
            with open(json_path, 'r') as f:
                self.setting_config = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.setting_config = None

        # Load settings
        ri_config = self.setting_config['ri_agent']
        swipe_config = self.setting_config['swipe_agent']

        # Initialize swipe settings
        self.mouse = Controller()
        self.base_power = swipe_config['base_power']
        self.last_shot_time = 0
        self.shot_cooldown = 0.1
        self.max_retries = 2
        self.shot_cooldown_fast = swipe_config['shot_cooldown_fast']
        self.swipe_duration_fast = swipe_config['swipe_duration_fast']
        self.shot_cooldown_slow = swipe_config['shot_cooldown_slow']
        self.swipe_duration_slow = swipe_config['swipe_duration_slow']

        # Initialize RI agent settings
        self.movement_threshold = ri_config['movement_threshold']
        self.prediction_factor = ri_config['prediction_factor']
        self.speed_memory = deque(maxlen=ri_config['speed_memory'])
        self.speed_history = deque(maxlen=ri_config['speed_history_size'])
        self.acceleration_threshold = ri_config['acceleration_threshold']
        self.speed_state = 'normal'
        self.prediction_params = ri_config['prediction_params']
        self.speed_thresholds = ri_config['speed_states']

        # Initialize position tracking
        self.last_pos = None
        self.last_time = None

        # Add logging properties
        self.logs = []
        self.shot_logs_folder = Path("shot_logs")
        self.shot_logs_folder.mkdir(exist_ok=True)
        self.shot_patterns_file = self.shot_logs_folder / "shot_patterns.json"
        self.existing_patterns = self.load_existing_patterns()

        # Add game timing properties
        self.game_start_time = None
        self.game_duration = 45  # durasi game dalam detik
        self.early_game_threshold = 20  # 20 detik untuk fase awal yang lebih stabil
        self.mid_game_threshold = 25    # Tambah threshold mid-game
        self.late_game_threshold = 35

    def load_existing_patterns(self):
        """Load existing shot patterns from file"""
        if self.shot_patterns_file.exists():
            try:
                with open(self.shot_patterns_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_mode(self, fast_mode):
        """Set shooting mode parameters"""
        if fast_mode:
            self.shot_cooldown = self.shot_cooldown_fast
            self.swipe_duration = self.swipe_duration_fast
        else:
            self.shot_cooldown = self.shot_cooldown_slow
            self.swipe_duration = self.swipe_duration_slow

    def get_action(self, game_screen, hoop_pos):
        """Calculate shooting angle and power based on hoop position"""
        try:
            x, y = hoop_pos
            current_time = time.time()
            
            # Initialize game start time if not set
            if not self.game_start_time:
                self.game_start_time = current_time
            
            # Calculate game progress
            game_time = current_time - self.game_start_time
            
            predicted_x = x
            if self.last_pos and self.last_time:
                dx = x - self.last_pos[0]
                dt = current_time - self.last_time
                
                if dt > 0:
                    current_speed = dx / dt
                    self.speed_memory.append(current_speed)
                    self.speed_history.append(abs(current_speed))
                    
                    # Detect speed state dynamically
                    if len(self.speed_history) >= 5:
                        recent_avg = sum(list(self.speed_history)[-5:]) / 5
                        older_avg = sum(list(self.speed_history)[:-5]) / (len(self.speed_history)-5) if len(self.speed_history) > 5 else recent_avg
                        
                        acceleration = abs(recent_avg - older_avg)
                        
                        if recent_avg > self.speed_thresholds['fast_threshold'] or acceleration > self.acceleration_threshold:
                            self.speed_state = 'fast'
                        elif recent_avg > self.speed_thresholds['medium_threshold']:
                            self.speed_state = 'medium'
                        else:
                            self.speed_state = 'normal'
                    
                    # Get current state parameters
                    params = self.prediction_params[self.speed_state]
                    
                    if len(self.speed_memory) >= 4:
                        avg_speed = sum(w * s for w, s in zip(params['weights'], list(self.speed_memory)[-4:]))
                    else:
                        avg_speed = sum(self.speed_memory) / len(self.speed_memory)
                    
                    if abs(dx) > self.movement_threshold:
                        dynamic_factor = self.prediction_factor * (params['base_factor'] + 
                                       min(abs(avg_speed)/params['speed_divisor'], params['max_speed_factor']))
                        predicted_x = x + (avg_speed * dynamic_factor)
                        
                        if abs(predicted_x - x) > params['max_offset']:
                            if predicted_x > x:
                                predicted_x = x + params['max_offset']
                            else:
                                predicted_x = x - params['max_offset']
                        predicted_x = min(max(predicted_x, 100), game_screen.shape[1] - 100)
            
            self.last_pos = hoop_pos
            self.last_time = current_time
            
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - 200
            
            dx = predicted_x - ball_x
            dy = ball_y - y
            distance = math.sqrt(dx*dx + dy*dy)
            
            angle = math.degrees(math.atan2(dy, dx))
            if distance > 350:
                angle += 3
            elif distance > 250:
                angle += 2
            elif distance < 200:
                angle -= 2
                
            base_power = self.base_power / 400
            power = min(0.95, max(0.5, base_power * (distance / 300)))
            
            if distance > 350:
                power *= 1.1
            elif distance < 200:
                power *= 0.9
                
            return (angle, power)
            
        except Exception as e:
            print(f"Error calculating shot: {e}")
            return (45, 0.6)

    def execute_action(self, action, ball_pos):
        """Execute shooting action with retry mechanism"""
        try:
            current_time = time.time()
            if current_time - self.last_shot_time < self.shot_cooldown:
                return False
                
            angle, power = action
            distance = power * self.base_power
            target_x = ball_pos[0] + distance * math.cos(math.radians(angle))
            target_y = ball_pos[1] - distance * math.sin(math.radians(angle))
            
            for attempt in range(self.max_retries):
                success = self.swipe(ball_pos[0], ball_pos[1], target_x, target_y)
                if success:
                    self.last_shot_time = current_time
                    return True
                else:
                    print(f"Retry shot {attempt + 1}/{self.max_retries}")
                    time.sleep(0.05)
            
            return False
            
        except Exception as e:
            print(f"Error executing shot: {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y, duration=None):
        """Perform swipe action with dynamic duration"""
        if duration is None:
            duration = self.swipe_duration

        try:
            self.mouse.release(Button.left)
            self.mouse.position = (start_x, start_y)
            time.sleep(0.02)
            
            current_pos = self.mouse.position
            if abs(current_pos[0] - start_x) > 5 or abs(current_pos[1] - start_y) > 5:
                print("Position validation failed")
                return False
                
            self.mouse.press(Button.left)
            
            steps = 8
            curve_height = 1.2
            
            for i in range(steps):
                progress = i / steps
                curve = math.sin(progress * math.pi) * curve_height
                
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress + curve)
                
                self.mouse.position = (current_x, current_y)
                time.sleep(duration / steps)
            
            self.mouse.position = (end_x, end_y)
            time.sleep(0.02)
            
            current_pos = self.mouse.position
            if abs(current_pos[0] - end_x) > 5 or abs(current_pos[1] - end_y) > 5:
                print("Final position validation failed")
                self.mouse.release(Button.left)
                return False
                
            self.mouse.release(Button.left)
            
            time.sleep(0.015)
            self.mouse.position = (start_x, start_y)
            
            return True
            
        except Exception as e:
            print(f"Swipe error: {e}")
            self.mouse.release(Button.left)
            return False

    def save_shot_logs(self):
        """Save the collected shot logs to a JSON file"""
        if not self.logs:
            return

        # Calculate summary statistics
        shots = len(self.logs)
        distances = [log["shot_params"]["distance"] for log in self.logs]
        angles = [log["shot_params"]["angle"] for log in self.logs]
        powers = [log["shot_params"]["power"] for log in self.logs]
        speeds = [log["movement_metrics"]["speed"] for log in self.logs]

        # Create shot pattern summary
        shot_summary = {
            "total_shots": shots,
            "average_distance": float(np.mean(distances)),
            "average_angle": float(np.mean(angles)),
            "average_power": float(np.mean(powers)),
            "average_hoop_speed": float(np.mean(speeds)),
            "shot_sequence": self.logs
        }

        # Generate pattern hash
        pattern_hash = hashlib.md5(json.dumps(shot_summary, sort_keys=True).encode()).hexdigest()

        # Save pattern
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pattern_data = {
            "id": pattern_hash,
            "timestamp": timestamp,
            "pattern_data": shot_summary
        }

        # Save to individual file
        pattern_file = self.shot_logs_folder / f"shots_{pattern_hash[:8]}_{timestamp}.json"
        with open(pattern_file, 'w') as f:
            json.dump(pattern_data, f, indent=2)
            print(f"\nShot pattern saved: {pattern_file}")

        # Update patterns database
        self.existing_patterns[pattern_hash] = pattern_data
        with open(self.shot_patterns_file, 'w') as f:
            json.dump(self.existing_patterns, f, indent=2)

    def reset_state(self):
        """Reset controller state"""
        self.last_shot_time = 0
        self.last_pos = None
        self.last_time = None
        self.speed_memory.clear()
        if self.logs:  # Save logs before resetting
            self.save_shot_logs()
        self.logs = [] 