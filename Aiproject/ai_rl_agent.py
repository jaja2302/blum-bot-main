import numpy as np
import math
import time
import cv2
from collections import deque
import pyautogui  # For simulating mouse/keyboard input
import os
import json

class RLAgent:
    def __init__(self):
        # self.last_pos = None
        # self.last_time = None
        # self.movement_threshold = 5  # Reduced to detect subtle movements
        # self.last_log_time = 0
        # self.log_interval = 0.0005  # Faster updates
        # self.prediction_factor = 0.65  # Slightly increased prediction
        # self.speed_memory = deque(maxlen=3)  # Shorter memory for faster response
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'setting_controller.json')
            with open(json_path, 'r') as f:
                self.setting_config = json.load(f)
        except Exception as e:
                self.button_config = None
        self.last_pos = None
        self.last_time = None
        self.movement_threshold = self.setting_config['movement_threshold']  # Lebih toleran terhadap pergerakan kecil
        self.last_log_time = 0
        self.log_interval = self.setting_config['log_interval']  # Sedikit lebih cepat untuk respons
        self.prediction_factor = self.setting_config['prediction_factor']  # Mengurangi prediksi untuk stabilitas
        self.speed_memory = deque(maxlen=self.setting_config['speed_memory'])  # Memori pendek untuk respons cepat


    def get_action(self, game_screen, hoop_pos):
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
                    
                    avg_speed = sum(self.speed_memory) / len(self.speed_memory)
                    if abs(dx) > self.movement_threshold:
                        predicted_x = x + (avg_speed * self.prediction_factor)
                        predicted_x = min(max(predicted_x, 100), game_screen.shape[1] - 100)
            
            self.last_pos = hoop_pos
            self.last_time = current_time
            
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - 200
            
            dx = predicted_x - ball_x
            dy = ball_y - y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.degrees(math.atan2(dy, dx))
            
            base_power = distance / 400
            power = min(0.9, max(0.45, base_power))
            
            if distance > 300:
                angle += 2
            elif distance < 200:
                angle -= 1
                
            return (angle, power)
            
        except Exception as e:
            print(f"Error menghitung tembakan: {e}")
            return (45, 0.6)

def shoot(angle, power):
    """Implement shooting mechanics using pyautogui"""
    try:
        # Convert angle and power to mouse movement
        mouse_x = int(math.cos(math.radians(angle)) * (power * 100))
        mouse_y = int(math.sin(math.radians(angle)) * (power * 100))
        
        # Perform shooting action
        pyautogui.mouseDown()
        pyautogui.moveRel(mouse_x, -mouse_y, duration=0.1)  # Negative y because screen coordinates
        pyautogui.mouseUp()
        
        # Add delay between shots
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error during shooting: {e}")

def process_frame(frame):
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    hoop_pos = None
    if contours:
        # Find the largest contour
        largest = max(contours, key=cv2.contourArea)
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(largest)
        
        # Calculate center position
        hoop_pos = (x + w//2, y + h//2)
        
    return hoop_pos

def main():
    agent = RLAgent()
    
    # Initialize game/video capture
    cap = cv2.VideoCapture(0) # or game window capture
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        hoop_pos = process_frame(frame)
        if hoop_pos:
            angle, power = agent.get_action(frame, hoop_pos)
            shoot(angle, power)
            
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()