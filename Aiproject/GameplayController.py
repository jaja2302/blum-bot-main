import numpy as np
import math
import time
import cv2
from collections import deque
from pynput.mouse import Button, Controller
import random
import os
import json

class GameplayController:
    def __init__(self):

        # for swipe action
        self.mouse = Controller()
        self.base_power = 300
        self.last_shot_time = 0
        self.shot_cooldown = 0.1
        self.max_retries = 2  # Maksimum percobaan ulang jika gagal
        self.shot_cooldown_fast = 0.1
        self.swipe_duration_fast = 0.08
        self.shot_cooldown_slow = 1.0
        self.swipe_duration_slow = 0.06
        self.base_power = 300
        

        # RL Agent properties
        self.last_pos = None
        self.last_time = None
        self.movement_threshold = 4
        self.last_log_time = 0
        self.log_interval = 0.005
        self.prediction_factor = 0.65
        self.speed_memory = deque(maxlen=3)

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
            
            predicted_x = x
            if self.last_pos and self.last_time:
                dx = x - self.last_pos[0]
                dt = current_time - self.last_time
                
                if dt > 0:
                    speed = dx / dt
                    self.speed_memory.append(speed)
                    
                    weights = [0.4, 0.3, 0.2, 0.1]
                    if len(self.speed_memory) >= 4:
                        avg_speed = sum(w * s for w, s in zip(weights, list(self.speed_memory)[-4:]))
                    else:
                        avg_speed = sum(self.speed_memory) / len(self.speed_memory)
                    
                    if abs(dx) > self.movement_threshold:
                        predicted_x = x + (avg_speed * self.prediction_factor)
                        if dx > 0:
                            predicted_x += 5
                        else:
                            predicted_x -= 5
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

    def reset_state(self):
        """Reset controller state"""
        self.last_shot_time = 0
        self.last_pos = None
        self.last_time = None
        self.speed_memory.clear() 