import cv2
import numpy as np
import pyautogui
import time

class HoopTracker:
    def __init__(self):
        self.history = []
        self.history_max = 6
        self.last_position = None
        
    def update_history(self, position, current_time):
        """Update position history"""
        self.history.append((position[0], position[1], current_time))
        if len(self.history) > self.history_max:
            self.history.pop(0)
    
    def predict_next_position(self, current_pos):
        """Predict next position based on movement history"""
        if len(self.history) >= 2:
            prev_x = self.history[-2][0]
            curr_x = self.history[-1][0]
            time_diff = self.history[-1][2] - self.history[-2][2]
            
            if time_diff > 0:
                speed = abs(curr_x - prev_x) / time_diff
                
                # Predict based on direction
                if curr_x > prev_x:  # Moving right
                    predicted_x = current_pos[0] + (speed * 0.2)
                else:  # Moving left
                    predicted_x = current_pos[0] - (speed * 0.2)
                    
                return (int(predicted_x), current_pos[1])
        
        return current_pos

def get_hoop_position(window_rect):
    """Main function to get hoop position"""
    try:
        # Take screenshot
        screenshot = np.array(pyautogui.screenshot(region=window_rect))
        current_time = time.time()
        
        # Convert to HSV
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_RGB2HSV)
        
        # Crop UI
        height = hsv.shape[0]
        ui_height = int(height * 0.15)
        game_area = hsv[ui_height:, :]
        
        # Blue backboard detection
        lower_blue = np.array([100, 150, 150])
        upper_blue = np.array([120, 255, 255])
        blue_mask = cv2.inRange(game_area, lower_blue, upper_blue)
        
        # Clean up mask
        kernel = np.ones((3,3), np.uint8)
        blue_mask = cv2.dilate(blue_mask, kernel, iterations=1)
        blue_mask = cv2.erode(blue_mask, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            valid_contours = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 200 < area < 5000:  # Filter by area
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w)/h
                    if 0.8 < aspect_ratio < 2.5:  # Filter by shape
                        valid_contours.append(cnt)
            
            if valid_contours:
                # Get largest valid contour
                largest_contour = max(valid_contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Calculate center
                center_x = x + w//2
                center_y = y + h//2 + ui_height
                
                # Convert to screen coordinates
                screen_x = window_rect[0] + center_x
                screen_y = window_rect[1] + center_y
                
                # Create tracker instance for prediction
                tracker = HoopTracker()
                tracker.update_history((screen_x, screen_y), current_time)
                
                # Get predicted position
                predicted_pos = tracker.predict_next_position((screen_x, screen_y))
                
                return predicted_pos
            
        return None
        
    except Exception as e:
        print(f"Error tracking hoop: {e}")
        return None

def collect_training_data():
    """Collect training data by capturing hoop positions"""
    training_data = []
    return training_data 