import cv2
import numpy as np
import time
from collections import deque

class HoopDetector:
    # Pre-computed constants
    DETECTION_START_Y = 150
    DETECTION_END_Y = 400
    
    # Pre-computed color arrays
    RED_LOWER_RGB = np.array([150, 0, 0], dtype=np.uint8)
    RED_UPPER_RGB = np.array([255, 50, 50], dtype=np.uint8)
    BALL_LOWER_RGB = np.array([60, 30, 0], dtype=np.uint8)
    BALL_UPPER_RGB = np.array([180, 100, 50], dtype=np.uint8)
    
    def __init__(self):
        # Use deque for fixed-size arrays (more efficient than list)
        self.position_history = deque(maxlen=5)
        self.velocity = [0, 0]
        self.last_valid_pos = None
        self.missed_detections = 0
        self.frame_skip = 0
        
    def detect_hoop(self, screenshot):
        """Optimized lightweight hoop detection"""
        try:
            if self.frame_skip > 0:
                self.frame_skip -= 1
                return self._predict_position()
            
            # Reduced detection area
            detection_area = screenshot[self.DETECTION_START_Y:self.DETECTION_END_Y:2, ::2]
            
            # Simple color filtering
            hoop_mask = cv2.inRange(detection_area, 
                                   np.array([140, 0, 0]), 
                                   np.array([255, 50, 50]))
            
            contours, _ = cv2.findContours(hoop_mask, cv2.RETR_EXTERNAL, 
                                         cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                
                if 80 < area < 400:  # Adjusted for downscaled image
                    M = cv2.moments(largest)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"]) * 2  # Scale back up
                        cy = int(M["m01"] / M["m00"]) * 2
                        position = (cx, cy + self.DETECTION_START_Y)
                        
                        self._update_motion(position)
                        self.last_valid_pos = position
                        self.missed_detections = 0
                        
                        # Simple frame skip
                        self.frame_skip = 2 if abs(self.velocity[0]) < 2 else 1
                        
                        return position
            
            self.missed_detections += 1
            return self._predict_position() if self.missed_detections < 3 else None
            
        except Exception:
            return self._predict_position() if self.last_valid_pos else None

    def _update_motion(self, position):
        """Fast motion update"""
        self.position_history.append(position)
        
        if len(self.position_history) >= 2:
            # Only calculate x velocity for performance
            prev = self.position_history[-2]
            curr = position
            self.velocity[0] = curr[0] - prev[0]

    def _predict_position(self):
        """Fast position prediction"""
        if not self.last_valid_pos:
            return None
            
        # Only predict x movement for performance
        predicted_x = self.last_valid_pos[0] + self.velocity[0]
        predicted_x = max(0, min(predicted_x, 800))
        
        return (int(predicted_x), self.last_valid_pos[1])

    def reset(self):
        """Minimal reset"""
        self.position_history.clear()
        self.velocity = [0, 0]
        self.last_valid_pos = None
        self.missed_detections = 0
        self.frame_skip = 0