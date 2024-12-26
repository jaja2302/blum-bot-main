import cv2
import numpy as np

class HoopDetector:
    def __init__(self):
        self.missed_detections = 0

    def detect_hoop(self, screenshot):
        """Try multiple detection methods"""
        frame_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        
        # Try color detection first
        result = self.detect_hoop_color(frame_bgr)
        if result:
            return result
        
        # If color fails, try shape detection
        result = self.detect_hoop_shape(frame_bgr)
        if result:
            return result
        
        return None

    def detect_hoop_color(self, frame_bgr):
        """Detect hoop using color with adaptive ranges"""
        height = frame_bgr.shape[0]
        
        roi_top = int(height * 0.2)
        roi_bottom = int(height * 0.5)
        roi = frame_bgr[roi_top:roi_bottom, :]
        
        red_lower = np.array([0, 0, 170])
        red_upper = np.array([15, 25, 255])
        
        if self.missed_detections > 10:
            red_lower[2] = max(150, red_lower[2] - 10)
            red_upper[1] = min(35, red_upper[1] + 5)
        
        red_mask = cv2.inRange(roi, red_lower, red_upper)
        kernel = np.ones((3,3), np.uint8)
        red_mask = cv2.dilate(red_mask, kernel, iterations=1)
        
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"]) + roi_top
                return (cx, cy)
        return None

    def detect_hoop_shape(self, frame_bgr):
        """Detect hoop using shape detection"""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        edges = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            valid_contours = []
            height = frame_bgr.shape[0]
            for cnt in contours:
                if cv2.contourArea(cnt) > 100:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if y < height/2 and w > h:
                        valid_contours.append(cnt)
            
            if valid_contours:
                largest = max(valid_contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)
        return None

    def draw_target_box(self, screenshot, position):
        """Draw targeting box around hoop"""
        cx, cy = position
        box_size = 72
        target_x = cx - box_size//2
        target_y = cy - box_size//2
        
        # Draw main box
        cv2.rectangle(screenshot, 
                    (target_x, target_y), 
                    (target_x + box_size, target_y + box_size), 
                    (0, 255, 0), 2)
        
        # Draw corner markers
        marker_length = 10
        # Top-left
        cv2.line(screenshot, (target_x, target_y), (target_x + marker_length, target_y), (0, 255, 0), 2)
        cv2.line(screenshot, (target_x, target_y), (target_x, target_y + marker_length), (0, 255, 0), 2)
        # Top-right
        cv2.line(screenshot, (target_x + box_size, target_y), (target_x + box_size - marker_length, target_y), (0, 255, 0), 2)
        cv2.line(screenshot, (target_x + box_size, target_y), (target_x + box_size, target_y + marker_length), (0, 255, 0), 2)
        # Bottom-left
        cv2.line(screenshot, (target_x, target_y + box_size), (target_x + marker_length, target_y + box_size), (0, 255, 0), 2)
        cv2.line(screenshot, (target_x, target_y + box_size), (target_x, target_y + box_size - marker_length), (0, 255, 0), 2)
        # Bottom-right
        cv2.line(screenshot, (target_x + box_size, target_y + box_size), (target_x + box_size - marker_length, target_y + box_size), (0, 255, 0), 2)
        cv2.line(screenshot, (target_x + box_size, target_y + box_size), (target_x + box_size, target_y + box_size - marker_length), (0, 255, 0), 2) 