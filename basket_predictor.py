import cv2
import numpy as np
import pyautogui
import time

class BasketPredictor:
    def __init__(self):
        self.basket_history = []
        self.history_max = 5
        self.last_detection_time = None

    def get_basket_speed(self):
        if len(self.basket_history) >= 2:
            prev_x = self.basket_history[-2][0]
            curr_x = self.basket_history[-1][0]
            return abs(curr_x - prev_x)
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
                            
                            horiz_speed = abs(cx - prev_x)
                            vert_speed = abs(cy - prev_y)
                            
                            # Horizontal prediction with momentum
                            if cx > prev_x:  # Moving right
                                if horiz_speed > 70:
                                    predicted_x = cx + 25
                                elif horiz_speed > 40:
                                    predicted_x = cx + 20
                                else:
                                    predicted_x = cx + 15
                            elif cx < prev_x:  # Moving left
                                if horiz_speed > 70:
                                    predicted_x = cx - 25
                                elif horiz_speed > 40:
                                    predicted_x = cx - 20
                                else:
                                    predicted_x = cx - 15
                            
                            # Pattern detection
                            if len(self.basket_history) >= 3:
                                prev_prev_x = self.basket_history[-3][0]
                                if (prev_x - prev_prev_x) * (cx - prev_x) < 0:
                                    if cx > prev_x:
                                        predicted_x += 10
                                    else:
                                        predicted_x -= 10
                            
                            # Vertical prediction
                            if cy > prev_y:  # Moving down
                                if vert_speed > 20:
                                    predicted_y = cy + 15
                                else:
                                    predicted_y = cy + 10
                            else:  # Moving up
                                if vert_speed > 20:
                                    predicted_y = cy - 15
                                else:
                                    predicted_y = cy - 10
                            
                            # Additional vertical adjustment
                            if horiz_speed > 60:
                                predicted_y -= 20
                            elif horiz_speed > 30:
                                predicted_y -= 15
                            
                            # Screen edge handling
                            screen_width = screenshot.shape[1]
                            if cx < screen_width * 0.3:
                                predicted_x += 15
                            elif cx > screen_width * 0.7:
                                predicted_x -= 15
                            
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