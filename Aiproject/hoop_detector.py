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
        """Optimized hoop detection without visualization"""
        try:
            # Frame skipping for performance
            if self.frame_skip > 0:
                self.frame_skip -= 1
                return self._predict_position()
            
            # Direct array slicing for detection area
            detection_area = screenshot[self.DETECTION_START_Y:self.DETECTION_END_Y]
            
            # Fast color filtering
            hoop_mask = cv2.inRange(detection_area, self.RED_LOWER_RGB, self.RED_UPPER_RGB)
            
            # Only detect ball if we have a valid hoop mask
            if np.count_nonzero(hoop_mask) > 400:
                ball_mask = cv2.inRange(detection_area, self.BALL_LOWER_RGB, self.BALL_UPPER_RGB)
                filtered_mask = cv2.bitwise_and(hoop_mask, cv2.bitwise_not(ball_mask))
            else:
                filtered_mask = hoop_mask
            
            # Fast contour finding
            contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Quick area filtering
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                
                if 400 < area < 700:
                    # Fast moment calculation
                    M = cv2.moments(largest)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        position = (cx, cy + self.DETECTION_START_Y)
                        
                        # Update tracking
                        self._update_motion(position)
                        self.last_valid_pos = position
                        self.missed_detections = 0
                        
                        # Adaptive frame skipping
                        speed = abs(self.velocity[0])
                        if speed < 2:
                            self.frame_skip = 2
                        elif speed < 5:
                            self.frame_skip = 1
                        
                        return position
            
            # Quick fallback to prediction
            self.missed_detections += 1
            if self.missed_detections < 3:
                return self._predict_position()
            
            return None
            
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