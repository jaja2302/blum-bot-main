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
        self.cycle_position = None  # Track position in movement cycle

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
        """Find basket position using red rim detection with improved prediction"""
        try:
            screenshot = np.array(pyautogui.screenshot())
            current_time = time.time()
            
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
                        
                        self.basket_history.append((cx, cy, current_time))
                        if len(self.basket_history) > self.history_max:
                            self.basket_history.pop(0)
                        
                        predicted_x = cx
                        predicted_y = cy
                        
                        if len(self.basket_history) >= 2:
                            prev_x = self.basket_history[-2][0]
                            prev_y = self.basket_history[-2][1]
                            
                            # Calculate speed and time-based metrics
                            horiz_speed = abs(cx - prev_x)
                            time_diff = current_time - self.basket_history[-2][2]
                            speed_ms = horiz_speed / time_diff if time_diff > 0 else 0
                            
                            # Pattern-based prediction
                            if cx > prev_x:  # Moving right
                                if speed_ms > 200:  # Fast movement (around 1.0-1.2s cycle)
                                    predicted_x = cx + 45
                                elif speed_ms > 150:  # Medium-fast (around 1.3-1.5s cycle)
                                    predicted_x = cx + 35
                                elif speed_ms > 100:  # Medium (around 1.6-1.8s cycle)
                                    predicted_x = cx + 25
                                else:  # Slow movement or direction change (>1.8s cycle)
                                    predicted_x = cx + 20
                            else:  # Moving left
                                if speed_ms > 200:
                                    predicted_x = cx - 45
                                elif speed_ms > 150:
                                    predicted_x = cx - 35
                                elif speed_ms > 100:
                                    predicted_x = cx - 25
                                else:
                                    predicted_x = cx - 20
                            
                            # Direction change detection and compensation
                            if len(self.basket_history) >= 3:
                                prev_prev_x = self.basket_history[-3][0]
                                direction_change = (prev_x - prev_prev_x) * (cx - prev_x) < 0
                                
                                if direction_change:
                                    # Enhanced direction change compensation based on timing
                                    if time_diff < 1.2:  # Quick direction change
                                        compensation = 25
                                    else:  # Slower direction change
                                        compensation = 15
                                        
                                    if cx > prev_x:
                                        predicted_x += compensation
                                    else:
                                        predicted_x -= compensation
                            
                            # Vertical adjustment based on horizontal speed
                            if horiz_speed > 70:
                                predicted_y = cy - 25
                            elif horiz_speed > 50:
                                predicted_y = cy - 20
                            elif horiz_speed > 30:
                                predicted_y = cy - 15
                            else:
                                predicted_y = cy - 10
                            
                            return (predicted_x, predicted_y)
                        
                        return (cx, cy)
            
            # Fallback prediction
            if len(self.basket_history) >= 2:
                last_x, last_y, _ = self.basket_history[-1]
                prev_x, prev_y, _ = self.basket_history[-2]
                dx = last_x - prev_x
                dy = last_y - prev_y
                return (last_x + dx, last_y + dy)
            
            return None
            
        except Exception as e:
            print(f"Error finding basket: {e}")
            return None 

    def get_prediction(self, cx, cy, speed_ms, moving_right):
        """Enhanced prediction with simple pattern matching"""
        # Get current movement characteristics
        speed_trend = self.analyze_movement()
        
        # Base prediction adjustments
        if speed_trend == 'accelerating':
            base_offset = 50 * (speed_ms / 80)  # More aggressive for acceleration
            base_y_offset = 32
        elif speed_trend == 'decelerating':
            base_offset = 50 * (speed_ms / 100)  # Less aggressive for deceleration
            base_y_offset = 28
        else:
            base_offset = 50 * (speed_ms / 90)
            base_y_offset = 30

        # Screen zone adjustments (make more dynamic)
        screen_portion = cx / self.screen_width
        if screen_portion < 0.3:  # Left zone
            zone_multiplier = 1.2 if moving_right else 0.9
        elif screen_portion > 0.7:  # Right zone
            zone_multiplier = 0.9 if moving_right else 1.2
        else:  # Middle zone
            zone_multiplier = 1.0

        predicted_x = cx + (base_offset * zone_multiplier * (1 if moving_right else -1))
        predicted_y = cy - base_y_offset

        # Edge protection
        edge_buffer = 120
        predicted_x = max(edge_buffer, min(self.screen_width - edge_buffer, predicted_x))

        return int(predicted_x), int(predicted_y)

    def analyze_movement(self):
        """Better speed and movement analysis"""
        if len(self.basket_history) < 3:
            return None

        # Calculate acceleration
        speeds = []
        for i in range(len(self.basket_history) - 1):
            dx = self.basket_history[i+1][0] - self.basket_history[i][0]
            dt = self.basket_history[i+1][2] - self.basket_history[i][2]
            if dt > 0:
                speeds.append(abs(dx/dt))

        # Detect if speed is changing
        speed_trend = 'steady'
        if len(speeds) >= 2:
            if speeds[-1] > speeds[-2] * 1.1:
                speed_trend = 'accelerating'
            elif speeds[-1] < speeds[-2] * 0.9:
                speed_trend = 'decelerating'

        return speed_trend