from pynput.mouse import Button, Controller
import random
import math
import time

class BallController:
    def __init__(self):
        self.mouse = Controller()
        self.base_power = 300
        self.last_shot_time = 0
        self.shot_cooldown = 0.1
        self.max_retries = 2  # Maksimum percobaan ulang jika gagal
        
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

    def swipe(self, start_x, start_y, end_x, end_y, duration=0.06):
        """Perform ultra-fast swipe action with validation"""
        try:
            # Add minimal randomization
            end_x += random.randint(-2, 2)
            end_y += random.randint(-2, 2)
            
            # Ensure mouse is released before starting
            self.mouse.release(Button.left)
            
            # Pre-position and press with validation
            self.mouse.position = (start_x, start_y)
            time.sleep(0.015)
            
            # Double-check position before pressing
            current_pos = self.mouse.position
            if abs(current_pos[0] - start_x) > 5 or abs(current_pos[1] - start_y) > 5:
                print("Position validation failed")
                return False
                
            self.mouse.press(Button.left)
            
            # Fast movement with position checking
            steps = 6
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
            time.sleep(0.015)
            
            # Validate final position before release
            current_pos = self.mouse.position
            if abs(current_pos[0] - end_x) > 5 or abs(current_pos[1] - end_y) > 5:
                print("Final position validation failed")
                self.mouse.release(Button.left)
                return False
                
            self.mouse.release(Button.left)
            
            # Quick return to start
            time.sleep(0.01)
            self.mouse.position = (start_x, start_y)
            
            return True
            
        except Exception as e:
            print(f"Swipe error: {e}")
            self.mouse.release(Button.left)  # Ensure mouse is released on error
            return False 