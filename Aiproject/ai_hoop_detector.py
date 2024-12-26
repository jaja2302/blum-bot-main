import cv2
import numpy as np

class HoopDetector:
    def __init__(self):
        # Initialize parameters for hoop detection
        self.hoop_color_lower = np.array([0, 0, 0])  # Adjust these values
        self.hoop_color_upper = np.array([180, 255, 30])  # based on hoop color

    def detect_hoop(self, frame):
        """
        Detect the hoop in the given frame
        Returns: (x, y) coordinates of the hoop or None if not found
        """
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Create mask for hoop color
            mask = cv2.inRange(hsv, self.hoop_color_lower, self.hoop_color_upper)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Get the center of the contour
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)
            
            return None
            
        except Exception as e:
            print(f"Error in hoop detection: {e}")
            return None 