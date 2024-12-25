import cv2
import numpy as np
import pyautogui
import time

class BasketPredictor:
    def __init__(self):
        self.basket_history = []
        self.history_max = 6
        self.last_detection_time = None
        self.cycle_start_time = None
        self.last_speed = 0
        self.cycle_position = None
        self.last_positions = []
        self.movement_type = None

    def get_basket_speed(self):
        if len(self.basket_history) >= 2:
            prev_x = self.basket_history[-2][0]
            curr_x = self.basket_history[-1][0]
            time_diff = self.basket_history[-1][2] - self.basket_history[-2][2]
            if time_diff > 0:
                self.last_speed = abs(curr_x - prev_x) / time_diff
            return self.last_speed
        return 0

    def get_basket_position(self):
        """Find basket position using combined detection methods"""
        try:
            screenshot = np.array(pyautogui.screenshot())
            current_time = time.time()
            
            # Convert to HSV for better detection
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_RGB2HSV)
            
            # Blue backboard detection
            lower_blue = np.array([100, 100, 100])
            upper_blue = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # White net detection
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            white_mask = cv2.inRange(hsv, lower_white, upper_white)
            
            # Combine with existing red rim detection
            red_lower = np.array([0, 0, 170])
            red_upper = np.array([15, 25, 255])
            red_mask = cv2.inRange(cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR), red_lower, red_upper)
            
            # Combine all masks
            combined_mask = cv2.bitwise_or(cv2.bitwise_or(blue_mask, white_mask), red_mask)
            
            # Clean up mask
            kernel = np.ones((3,3), np.uint8)
            combined_mask = cv2.dilate(combined_mask, kernel, iterations=1)
            combined_mask = cv2.erode(combined_mask, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                valid_contours = []
                height = screenshot.shape[0]
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if 200 < area < 5000:  # Filter by area
                        x, y, w, h = cv2.boundingRect(cnt)
                        if y < height/2:  # Upper half only
                            aspect_ratio = float(w)/h
                            if 1.2 < aspect_ratio < 2.5:  # Filter by shape
                                valid_contours.append(cnt)
                
                if valid_contours:
                    largest_contour = max(valid_contours, key=cv2.contourArea)
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    cx = x + w//2
                    cy = y + h//2
                    
                    # Track movement pattern
                    self.last_positions.append(cx)
                    if len(self.last_positions) > 2:
                        self.last_positions.pop(0)
                    
                    # Determine movement type
                    if len(self.last_positions) > 1:
                        speed = self.last_positions[-1] - self.last_positions[-2]
                        if abs(speed) < 2:
                            self.movement_type = "center_pause"
                        elif speed > 0:
                            self.movement_type = "left_to_right"
                        else:
                            self.movement_type = "right_to_left"
                    
                    # Rest of your existing prediction logic
                    self.basket_history.append((cx, cy, current_time))
                    if len(self.basket_history) > self.history_max:
                        self.basket_history.pop(0)
                    
                    # Enhanced prediction based on movement type
                    predicted_x = cx
                    predicted_y = cy
                    
                    if len(self.basket_history) >= 2:
                        # Calculate current speed and direction
                        time_diff = current_time - self.basket_history[-2][2]
                        distance = cx - self.basket_history[-2][0]
                        current_speed = distance / time_diff if time_diff > 0 else 0
                        
                        # Predict future position based on current movement
                        prediction_time = 0.3  # Adjust this value based on your game's timing
                        
                        if self.movement_type == "center_pause":
                            predicted_x = cx  # No adjustment during pause
                        elif self.movement_type == "left_to_right":
                            predicted_x = cx + (current_speed * prediction_time)
                        elif self.movement_type == "right_to_left":
                            predicted_x = cx + (current_speed * prediction_time)
                        
                        # Add bounds checking
                        screen_width = screenshot.shape[1]
                        predicted_x = max(0, min(predicted_x, screen_width))
                        
                        return (int(predicted_x), predicted_y)
                    
                    return (cx, cy)
            
            # Your existing fallback logic
            return None
            
        except Exception as e:
            print(f"Error finding basket: {e}")
            return None 