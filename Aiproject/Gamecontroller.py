import numpy as np
import math
import time
from collections import deque
from pynput.mouse import Button, Controller
import os
import json
from pathlib import Path

class GameplayController:
    def __init__(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'partial/setting_controller.json')
            with open(json_path, 'r') as f:
                self.setting_config = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            raise ValueError("Settings could not be loaded")

        # Load settings
        ri_config = self.setting_config['ri_agent']
        swipe_config = self.setting_config['swipe_agent']

        # Swipe settings (unchanged)
        self.mouse = Controller()
        self.base_power = swipe_config['base_power']
        self.last_shot_time = 0
        self.shot_cooldown = 0.1
        self.max_retries = 2
        self.shot_cooldown_fast = swipe_config['shot_cooldown_fast']
        self.swipe_duration_fast = swipe_config['swipe_duration_fast']
        self.shot_cooldown_slow = swipe_config['shot_cooldown_slow']
        self.swipe_duration_slow = swipe_config['swipe_duration_slow']

        # Optimized RI agent settings
        self.speed_memory = deque(maxlen=3)  # Reduced from original
        self.speed_history = deque(maxlen=10)  # Reduced for less memory usage
        self.speed_state = 'normal'
        self.speed_thresholds = ri_config['speed_states']
        
        # Enhanced prediction factors with better medium speed handling
        self.prediction_factors = {
            'very_slow': 0.45,
            'slow': 0.52,      
            'normal': 0.58,    # Slightly reduced
            'medium': 0.62,    # Adjusted for better medium speed accuracy
            'fast': 0.72      
        }
        
        # Lead time compensation with refined medium speed values
        self.lead_time_compensation = {
            'very_slow': 0.08,
            'slow': 0.12,
            'normal': 0.14,    # Slightly reduced
            'medium': 0.16,    # Reduced for better medium speed control
            'fast': 0.22
        }
        
        # Add speed transition dampening
        self.speed_dampening = {
            'very_slow': 1.0,
            'slow': 0.95,
            'normal': 0.90,
            'medium': 0.85,
            'fast': 0.80
        }
        
        # Position tracking
        self.last_pos = None
        self.last_time = None
        
        # Game state
        self.game_start_time = None

    def execute_action(self, action, window_info):
        current_time = time.time()
        if current_time - self.last_shot_time < self.shot_cooldown:
            return False
            
        angle, power = action
        distance = power * self.base_power
        
        ball_pos = (
            window_info['left'] + window_info['width'] // 2,
            window_info['top'] + window_info['height'] - 220
        )
        
        target_x = ball_pos[0] + distance * math.cos(math.radians(angle))
        target_y = ball_pos[1] - distance * math.sin(math.radians(angle))
        
        success = self.swipe(ball_pos[0], ball_pos[1], target_x, target_y)
        if success:
            self.last_shot_time = current_time
        return success

    def get_action(self, game_screen, hoop_pos):
        try:
            if game_screen is None or hoop_pos is None:
                return (45, 0.6)

            x, y = hoop_pos
            current_time = time.time()

            if not self.game_start_time:
                self.game_start_time = current_time

            # Calculate speed and update state
            predicted_x = x
            if self.last_pos and self.last_time:
                dt = current_time - self.last_time
                if dt > 0:
                    speed = (x - self.last_pos[0]) / dt
                    self.speed_memory.append(speed)
                    self.speed_history.append(abs(speed))

                    # Enhanced speed state determination with smoothing
                    if len(self.speed_history) >= 3:
                        recent_speeds = list(self.speed_history)[-3:]
                        avg_speed = sum(recent_speeds) / 3
                        
                        # Add trend detection
                        speed_trend = 0
                        if len(recent_speeds) >= 2:
                            speed_trend = recent_speeds[-1] - recent_speeds[0]
                        
                        # Adjust thresholds based on trend
                        trend_factor = 1.0 + (speed_trend * 0.1)
                        
                        if avg_speed < 60 * trend_factor:
                            new_state = 'very_slow'
                        elif avg_speed < 70 * trend_factor:
                            new_state = 'slow'
                        elif avg_speed < 85 * trend_factor:
                            new_state = 'normal'
                        elif avg_speed < 120 * trend_factor:
                            new_state = 'medium'
                        else:
                            new_state = 'fast'
                            
                        # Smooth state transitions
                        if new_state != self.speed_state:
                            # Only change state if we detect the same new state multiple times
                            if not hasattr(self, 'state_change_counter'):
                                self.state_change_counter = {}
                            
                            if new_state not in self.state_change_counter:
                                self.state_change_counter[new_state] = 1
                            else:
                                self.state_change_counter[new_state] += 1
                            
                            required_counts = {
                                'very_slow': 2,
                                'slow': 2,
                                'normal': 3,
                                'medium': 3,
                                'fast': 2
                            }
                            
                            if self.state_change_counter.get(new_state, 0) >= required_counts[new_state]:
                                self.speed_state = new_state
                                self.state_change_counter.clear()

                    # Enhanced prediction calculation with smoothed transitions
                    if len(self.speed_memory) >= 2:
                        avg_speed = sum(self.speed_memory) / len(self.speed_memory)
                        
                        # Add system latency compensation with dampening
                        lead_time = self.lead_time_compensation[self.speed_state]
                        dampening = self.speed_dampening[self.speed_state]
                        
                        # Calculate base prediction
                        base_prediction = avg_speed * (self.prediction_factors[self.speed_state] * dampening + lead_time)
                        
                        # Add direction-based compensation
                        direction = 1 if avg_speed > 0 else -1
                        direction_factor = min(abs(avg_speed) / 100, 1.0)  # Normalize speed influence
                        extra_offset = direction * (abs(avg_speed) * 0.12 * direction_factor)  # Reduced from 0.15
                        
                        # Apply predictions with game phase adjustment
                        game_time = time.time() - self.game_start_time if self.game_start_time else 0
                        if game_time < 5:  # Early game adjustment
                            base_prediction *= 0.85
                            extra_offset *= 0.8
                        
                        predicted_x = x + base_prediction + extra_offset
                        
                        # Ensure prediction stays within bounds
                        predicted_x = min(max(predicted_x, 100), game_screen.shape[1] - 100)

            self.last_pos = hoop_pos
            self.last_time = current_time

            # Simplified shooting angle and power calculation
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - 200

            dx = predicted_x - ball_x
            dy = ball_y - y
            distance = math.sqrt(dx*dx + dy*dy)

            # Enhanced angle adjustment with dynamic compensation
            angle = math.degrees(math.atan2(dy, dx))
            
            # Dynamic angle adjustment based on distance and speed
            speed_magnitude = abs(sum(self.speed_memory) / len(self.speed_memory)) if self.speed_memory else 0
            
            if distance > 300:
                angle += 2 + (speed_magnitude * 0.01)  # Add extra angle for faster speeds
            elif distance > 250:
                angle += 1.5 + (speed_magnitude * 0.008)
            elif distance < 200:
                angle -= 1 + (speed_magnitude * 0.005)
                
            # Additional minor adjustment for extreme sides
            if predicted_x > game_screen.shape[1] * 0.7:  # Right side
                angle += 0.8
            elif predicted_x < game_screen.shape[1] * 0.3:  # Left side
                angle -= 0.8

            # Simplified power calculation
            power = min(0.95, max(0.5, (distance / 300) * (self.base_power / 400)))
            if distance > 300:
                power *= 1.05

            return (angle, power)

        except Exception as e:
            print(f"Error in get_action: {e}")
            return (45, 0.6)

    def set_mode(self, fast_mode):
        self.shot_cooldown = self.shot_cooldown_fast if fast_mode else self.shot_cooldown_slow
        self.swipe_duration = self.swipe_duration_fast if fast_mode else self.swipe_duration_slow

    def reset_state(self):
        """Reset all game state variables for a new game"""
        # Reset timing variables
        self.last_shot_time = 0
        self.game_start_time = None
        self.last_time = None
        
        # Reset position tracking
        self.last_pos = None
        
        # Reset speed tracking
        self.speed_memory.clear()
        self.speed_history.clear()
        self.speed_state = 'normal'
        
        # Release mouse button just in case
        self.mouse.release(Button.left)
        
        print("Game state reset completed")

    def swipe(self, start_x, start_y, end_x, end_y):
        """Optimized swipe action for CPU-only systems"""
        try:
            # Reset mouse state
            self.mouse.release(Button.left)
            time.sleep(0.02)
            
            # Set initial position
            self.mouse.position = (start_x, start_y)
            time.sleep(0.02)
            
            self.mouse.press(Button.left)
            
            # Simplified movement with fewer steps
            steps = 10  # Reduced number of steps for better performance
            duration = self.swipe_duration
            
            for i in range(steps):
                progress = i / steps
                
                # Linear interpolation for smoother movement
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress)
                
                self.mouse.position = (current_x, current_y)
                time.sleep(duration / steps)
            
            # Ensure we reach the final position
            self.mouse.position = (end_x, end_y)
            self.mouse.release(Button.left)
            
            # Quick return to start
            time.sleep(0.02)
            self.mouse.position = (start_x, start_y)
            
            return True
            
        except Exception as e:
            print(f"Swipe error: {e}")
            self.mouse.release(Button.left)
            return False