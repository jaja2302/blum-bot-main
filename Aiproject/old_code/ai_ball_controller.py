from pynput.mouse import Button, Controller
import random
import math
import time
import os
import json

class BallController:
    def __init__(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'setting_controller.json')
            with open(json_path, 'r') as f:
                self.setting_config = json.load(f)
        except Exception as e:
            self.setting_config = None

        self.mouse = Controller()
        self.base_power = self.setting_config['base_power']
        self.last_shot_time = 0
        self.shot_cooldown = self.setting_config['shot_cooldown']  # Default cooldown untuk mode cepat
        self.max_retries = 2  # Maksimum percobaan ulang jika gagal
       
        
    def set_mode(self, fast_mode):
        """Set shooting mode parameters"""
        if fast_mode:
            self.shot_cooldown = self.setting_config['shot_cooldown']  # 10 tembakan/detik
            self.swipe_duration = self.setting_config['swipe_duration'] 
        else:
            self.shot_cooldown = 1.0  # 1 tembakan/detik
            self.swipe_duration = 0.06 # Sedikit lebih lambat untuk swipe yang lebih halus

    def execute_action(self, action, ball_pos):
        """Execute shooting action from RLAgent with retry mechanism"""
        try:
            current_time = time.time()
            if current_time - self.last_shot_time < self.shot_cooldown:
                return False
                
            angle, power = action
            distance = power * self.base_power
            target_x = ball_pos[0] + distance * math.cos(math.radians(angle))
            target_y = ball_pos[1] - distance * math.sin(math.radians(angle))
            
            # Retry mechanism
            for attempt in range(self.max_retries):
                success = self.swipe(ball_pos[0], ball_pos[1], target_x, target_y)
                if success:
                    self.last_shot_time = current_time
                    return True
                else:
                    print(f"Retry shot {attempt + 1}/{self.max_retries}")
                    time.sleep(0.05)  # Brief pause before retry
            
            return False
            
        except Exception as e:
            print(f"Error executing shot: {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y, duration=None):
        """Perform swipe action with dynamic duration"""
        if duration is None:
            duration = self.swipe_duration  # Use mode-specific duration
        try:
            # Add minimal randomization
            # end_x += random.randint(-2, 2)
            # end_y += random.randint(-2, 2)
            
            # Ensure mouse is released before starting
            self.mouse.release(Button.left)
            
            # Pre-position and press with validation
            self.mouse.position = (start_x, start_y)
            time.sleep(0.02)
            
            # Double-check position before pressing
            current_pos = self.mouse.position
            if abs(current_pos[0] - start_x) > 5 or abs(current_pos[1] - start_y) > 5:
                print("Position validation failed")
                return False
                
            self.mouse.press(Button.left)
            
            # Fast movement with position checking
            steps = 8
            curve_height = 1.2
            
            for i in range(steps):
                progress = i / steps
                curve = math.sin(progress * math.pi) * curve_height
                
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress + curve)
                
                self.mouse.position = (current_x, current_y)
                time.sleep(duration / steps)
            
            # Ensure we reach target position
            self.mouse.position = (end_x, end_y)
            time.sleep(0.02)
            
            # Validate final position before release
            current_pos = self.mouse.position
            if abs(current_pos[0] - end_x) > 5 or abs(current_pos[1] - end_y) > 5:
                print("Final position validation failed")
                self.mouse.release(Button.left)
                return False
                
            self.mouse.release(Button.left)
            
            # Quick return to start
            time.sleep(0.015)
            self.mouse.position = (start_x, start_y)
            
            return True
            
        except Exception as e:
            print(f"Swipe error: {e}")
            self.mouse.release(Button.left)
            return False 

    def reset_state(self):
        """Reset controller state between games"""
        self.last_shot_time = 0 