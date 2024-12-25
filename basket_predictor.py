import cv2
import numpy as np
import pyautogui

class BasketPredictor:
    def __init__(self):
        self.screen_width = None
        self.last_valid_center = None

    def get_basket_position(self):
        """Find basket position using just the red rim with strict filtering"""
        try:
            screenshot = np.array(pyautogui.screenshot())
            
            # Very specific red rim detection
            red_lower = np.array([170, 0, 0])  # RGB values
            red_upper = np.array([255, 30, 30])
            
            # Create mask for red pixels
            red_mask = cv2.inRange(screenshot, red_lower, red_upper)
            
            # Small kernel for noise removal
            kernel = np.ones((2,2), np.uint8)
            red_mask = cv2.erode(red_mask, kernel, iterations=1)
            red_mask = cv2.dilate(red_mask, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Filter contours by y-position (upper half of screen)
                height = screenshot.shape[0]
                valid_contours = []
                
                for cnt in contours:
                    M = cv2.moments(cnt)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])
                        # Check if contour is in upper part of screen
                        if cy < height/2:
                            valid_contours.append(cnt)
                
                if valid_contours:
                    # Get the rim points
                    all_points = np.concatenate(valid_contours)
                    leftmost = all_points[all_points[:,:,0].argmin()][0][0]
                    rightmost = all_points[all_points[:,:,0].argmax()][0][0]
                    
                    # Calculate center with a tiny right offset
                    center_x = leftmost + (rightmost - leftmost) // 2 + 3
                    
                    # Get y position from highest contour
                    highest_contour = min(valid_contours, 
                                        key=lambda c: cv2.moments(c)["m01"] / cv2.moments(c)["m00"])
                    M = cv2.moments(highest_contour)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])
                        
                        # Store this as last valid center
                        self.last_valid_center = (center_x, cy - 25)
                        return self.last_valid_center
            
            # If no valid detection, return last known position
            return self.last_valid_center
            
        except Exception as e:
            print(f"Error finding basket: {e}")
            return self.last_valid_center

    def get_basket_speed(self):
        """Dummy method to maintain compatibility with piggybot.py"""
        return 0