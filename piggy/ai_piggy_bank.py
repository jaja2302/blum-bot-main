import cv2
import numpy as np
import pyautogui
import time

class HoopTracker:
    def __init__(self):
        self.basket_history = []
        self.history_max = 6
        self.last_detection_time = None

    def update_history(self, position, current_time):
        """Update position history"""
        self.basket_history.append((position[0], position[1], current_time))
        if len(self.basket_history) > self.history_max:
            self.basket_history.pop(0)

def get_hoop_position(window_rect):
    """Main function to get hoop position"""
    try:
        screenshot = np.array(pyautogui.screenshot(region=window_rect))
        if screenshot is None:
            return None
            
        # Adjusted color range for better rim detection
        red_lower = np.array([0, 0, 170])
        red_upper = np.array([15, 25, 255])
        
        red_mask = cv2.inRange(cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR), red_lower, red_upper)
        kernel = np.ones((3,3), np.uint8)
        red_mask = cv2.dilate(red_mask, kernel, iterations=1)
        
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            valid_contours = []
            height = screenshot.shape[0]
            for cnt in contours:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cy = int(M["m01"] / M["m00"])
                    if cy < height/2:
                        valid_contours.append(cnt)
            
            if valid_contours:
                largest_contour = max(valid_contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    screen_x = window_rect[0] + cx
                    screen_y = window_rect[1] + cy
                    
                    return (screen_x, screen_y)
        
        return None
        
    except Exception as e:
        print(f"Error tracking hoop: {e}")
        return None

# Initialize last_pos as static variable
get_hoop_position.last_pos = None

def collect_training_data():
    """Collect training data by capturing hoop positions"""
    training_data = []
    return training_data 

    