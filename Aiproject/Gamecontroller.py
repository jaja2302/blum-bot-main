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

        try:
            json_path = os.path.join(os.path.dirname(__file__), 'setting_controller.json')
            with open(json_path, 'r') as f:
                self.setting_config = json.load(f)
        except Exception as e:
            self.setting_config = None

        # for swipe action
        self.mouse = Controller()
        self.base_power = 300
        self.last_shot_time = 0
        self.shot_cooldown = 0.1
        self.max_retries = 2  # Maksimum percobaan ulang jika gagal
        self.shot_cooldown_fast = self.setting_config['swipe_agent']['shot_cooldown_fast']
        self.swipe_duration_fast = self.setting_config['swipe_agent']['swipe_duration_fast']
        self.shot_cooldown_slow = self.setting_config['swipe_agent']['shot_cooldown_slow']
        self.swipe_duration_slow = self.setting_config['swipe_agent']['swipe_duration_slow']
        self.base_power = self.setting_config['swipe_agent']['base_power']
        

        # RL Agent properties
        self.last_pos = None
        self.last_time = None
        self.movement_threshold = self.setting_config['ri_agent']['movement_threshold']
        self.last_log_time = self.setting_config['ri_agent']['last_log_time']
        self.log_interval = self.setting_config['ri_agent']['log_interval']
        self.prediction_factor = self.setting_config['ri_agent']['prediction_factor']
        self.speed_memory = deque(maxlen=self.setting_config['ri_agent']['speed_memory'])


    def set_mode(self, fast_mode):
        """Set shooting mode parameters"""
        if fast_mode:
            self.shot_cooldown = self.shot_cooldown_fast
            self.swipe_duration = self.swipe_duration_fast
        else:
            self.shot_cooldown = self.shot_cooldown_slow
            self.swipe_duration = self.swipe_duration_slow

    def get_action(self, game_screen, hoop_pos):
        """Calculate shooting angle and power with straight up shot"""
        try:
            # Fixed angle for straight up shot (90 degrees)
            angle = 90
            
            # Fixed power for consistent height
            power = 0.7  # Bisa disesuaikan antara 0.6-0.8
            
            return (angle, power)
            
        except Exception as e:
            print(f"Error calculating shot: {e}")
            return (90, 0.7)  # Default fallback

    def execute_action(self, action, ball_pos):
        """Execute shooting action with fixed upward direction"""
        try:
            current_time = time.time()
            if current_time - self.last_shot_time < self.shot_cooldown:
                return False
                
            angle, power = action
            distance = power * self.base_power
            
            target_x = ball_pos[0]
            target_y = ball_pos[1] - distance
            
            # Tambah retry dengan progressive delay
            for attempt in range(self.max_retries):
                success = self.swipe(ball_pos[0], ball_pos[1], target_x, target_y)
                if success:
                    self.last_shot_time = current_time
                    return True
                time.sleep(0.005 * (attempt + 1))  # Progressive delay
                
            return False
            
        except Exception as e:
            print(f"Error executing shot: {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y, duration=None):
        """Perform swipe action with dynamic duration"""
        if duration is None:
            duration = self.swipe_duration

        try:
            # Reset mouse state
            self.mouse.release(Button.left)
            time.sleep(0.01)  # Reduced delay
            
            # Posisi awal dengan validasi lebih ketat
            self.mouse.position = (start_x, start_y)
            time.sleep(0.01)  # Reduced delay
            
            current_pos = self.mouse.position
            if abs(current_pos[0] - start_x) > 2 or abs(current_pos[1] - start_y) > 2:  # Threshold lebih ketat
                self.mouse.position = (start_x, start_y)  # Retry positioning
                time.sleep(0.01)
                current_pos = self.mouse.position
                if abs(current_pos[0] - start_x) > 2 or abs(current_pos[1] - start_y) > 2:
                    return False
                
            self.mouse.press(Button.left)
            
            # Optimasi steps berdasarkan duration
            steps = max(5, min(15, int(duration * 1000)))  # Dynamic steps
            curve_height = 0.5  # Reduced curve height
            
            for i in range(steps):
                progress = i / steps
                curve = math.sin(progress * math.pi) * curve_height
                
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress + curve)
                
                self.mouse.position = (current_x, current_y)
                time.sleep(duration / steps)
            
            self.mouse.position = (end_x, end_y)
            self.mouse.release(Button.left)
            
            # Quick return to start
            time.sleep(0.01)
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