from pynput.mouse import Button, Controller
import random
import math
import time

class BallController:
    def __init__(self):
        self.mouse = Controller()
        self.base_power = 300  # Base power untuk jarak tembakan
        
    def execute_action(self, action, ball_pos):
        """Execute shooting action from RLAgent"""
        try:
            angle, power = action
            
            # Konversi angle dan power ke koordinat target
            distance = power * self.base_power
            target_x = ball_pos[0] + distance * math.cos(math.radians(angle))
            target_y = ball_pos[1] - distance * math.sin(math.radians(angle))
            
            # Eksekusi swipe dengan smooth movement
            self.swipe(ball_pos[0], ball_pos[1], target_x, target_y)
            return True
            
        except Exception as e:
            print(f"Error executing shot: {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y, duration=0.2):
        """Perform smooth swipe action"""
        try:
            # Add randomization
            end_x += random.randint(-3, 3)
            end_y += random.randint(-3, 3)
            
            # Start swipe
            self.mouse.position = (start_x, start_y)
            time.sleep(0.05)
            self.mouse.press(Button.left)
            
            # Smooth movement with curve
            steps = 15
            for i in range(steps):
                progress = i / steps
                curve = math.sin(progress * math.pi) * 2
                
                current_x = start_x + (end_x - start_x) * progress
                current_y = start_y + (end_y - start_y) * progress + curve
                
                self.mouse.position = (int(current_x), int(current_y))
                time.sleep(duration / steps)
            
            # Release at target
            self.mouse.position = (end_x, end_y)
            time.sleep(0.05)
            self.mouse.release(Button.left)
            
            # Return to ball position
            time.sleep(0.1)
            self.mouse.position = (start_x, start_y)
            
        except Exception as e:
            print(f"Swipe error: {e}") 