import cv2
import numpy as np
import pyautogui
import time
import json
import os
import win32gui
from datetime import datetime

class HoopTracker:
    def __init__(self):
        self.basket_history = []
        self.history_max = 6
        self.last_detection_time = None
        self.movement_patterns = []
        self.missed_detections = 0
        self.total_detections = 0
        self.load_existing_patterns()

    def load_existing_patterns(self):
        """Load existing patterns from previous runs"""
        try:
            if os.path.exists('training_data/ai_learning.json'):
                print("\nLoading existing patterns...")
                with open('training_data/ai_learning.json', 'r') as f:
                    data = json.load(f)
                    existing_patterns = data.get('patterns', [])
                    self.movement_patterns = existing_patterns
                    print(f"Loaded {len(existing_patterns)} existing patterns")
        except Exception as e:
            print(f"Error loading existing patterns: {e}")

    def update_history(self, position, current_time):
        """Update position history and learn movement patterns"""
        self.basket_history.append((position[0], position[1], current_time))
        if len(self.basket_history) > self.history_max:
            self.basket_history.pop(0)
            
        # Learn from movement if we have enough history
        if len(self.basket_history) >= 2:
            prev = self.basket_history[-2]
            curr = self.basket_history[-1]
            
            # Calculate movement
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            dt = curr[2] - prev[2]
            
            if dt > 0:  # Avoid division by zero
                pattern = {
                    'dx': dx,
                    'dy': dy,
                    'speed': np.sqrt(dx*dx + dy*dy) / dt,
                    'direction': 1 if dx > 0 else -1,
                    'height': curr[1],
                    'timestamp': current_time
                }
                self.movement_patterns.append(pattern)

    def get_game_window(self):
        """Find the Telegram window"""
        def callback(hwnd, windows):
            if "Telegram" in win32gui.GetWindowText(hwnd):
                windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if not windows:
            print("Error: Could not find Telegram window!")
            return None
            
        # Get the first Telegram window found
        hwnd = windows[0]
        rect = win32gui.GetWindowRect(hwnd)
        x, y, x2, y2 = rect
        w = x2 - x
        h = y2 - y
        
        print(f"Found Telegram window: {w}x{h} at ({x}, {y})")
        return (x, y, w, h)

    def detect_hoop(self, screenshot):
        """Try multiple detection methods"""
        frame_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        
        # Try color detection first
        result = self.detect_hoop_color(frame_bgr)
        if result:
            if self.missed_detections > 0:
                print("\nDetection resumed (color method)")
            return result
        
        # If color fails, try shape detection
        result = self.detect_hoop_shape(frame_bgr)
        if result:
            if self.missed_detections > 0:
                print("\nDetection resumed (shape method)")
            return result
        
        return None

    def detect_hoop_color(self, frame_bgr):
        """Detect hoop using color with adaptive ranges"""
        # Get frame dimensions
        height = frame_bgr.shape[0]
        
        # Limit detection to middle-upper part of screen (exclude timer area)
        roi_top = int(height * 0.2)  # Skip top 20% where timer is
        roi_bottom = int(height * 0.5)  # Only check upper half
        roi = frame_bgr[roi_top:roi_bottom, :]
        
        # Start with base values
        red_lower = np.array([0, 0, 170])
        red_upper = np.array([15, 25, 255])
        
        # If missing too many detections, try adjusting ranges
        if self.missed_detections > 10:
            red_lower[2] = max(150, red_lower[2] - 10)
            red_upper[1] = min(35, red_upper[1] + 5)
        
        red_mask = cv2.inRange(roi, red_lower, red_upper)
        kernel = np.ones((3,3), np.uint8)
        red_mask = cv2.dilate(red_mask, kernel, iterations=1)
        
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            valid_contours = []
            for cnt in contours:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    valid_contours.append(cnt)
            
            if valid_contours:
                largest_contour = max(valid_contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"]) + roi_top  # Add offset back
                    return (cx, cy)
        
        return None

    def detect_hoop_shape(self, frame_bgr):
        """Detect hoop using shape detection"""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Look for rectangular shapes (backboard)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            valid_contours = []
            height = frame_bgr.shape[0]
            for cnt in contours:
                if cv2.contourArea(cnt) > 100:  # Minimum size
                    x, y, w, h = cv2.boundingRect(cnt)
                    if y < height/2 and w > h:  # Upper half and wider than tall
                        valid_contours.append(cnt)
            
            if valid_contours:
                largest = max(valid_contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)
        
        return None

    def learn_from_game(self):
        """Learn hoop movement patterns from live game"""
        print("\nStarting AI learning process...")
        print("Using enhanced detection with adaptive color and shape detection")
        
        # Get Telegram window
        window_rect = self.get_game_window()
        if not window_rect:
            return
            
        x, y, w, h = window_rect
        start_time = time.time()
        frame_count = 0
        last_save_time = time.time()
        
        print("\nTracking hoop movement...")
        print("Press 'q' to quit, 'Esc' for emergency exit")
        print("Press 's' to save current progress")
        
        try:
            while True:
                # Capture Telegram window
                screenshot = np.array(pyautogui.screenshot(region=(x, y, w, h)))
                frame_count += 1
                current_time = time.time() - start_time
                
                # Detect hoop
                hoop_pos = self.detect_hoop(screenshot)
                self.total_detections += 1
                
                if hoop_pos:
                    # Reset missed detection counter when we find the hoop
                    if self.missed_detections > 0:
                        print("\nHoop detection resumed!")
                        self.missed_detections = 0
                    
                    cx, cy = hoop_pos
                    self.update_history((cx, cy), current_time)
                    
                    # Draw green targeting box
                    box_size = 72
                    target_x = cx - box_size//2
                    target_y = cy - box_size//2
                    
                    # Draw main green box and markers
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
                    
                    # Show detection stats
                    if len(self.movement_patterns) > 0:
                        latest = self.movement_patterns[-1]
                        cv2.putText(screenshot, f"Speed: {latest['speed']:.1f}", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(screenshot, f"Direction: {'Right' if latest['direction'] > 0 else 'Left'}", 
                                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    self.missed_detections += 1
                    cv2.putText(screenshot, "Lost Detection!", (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Display stats
                cv2.putText(screenshot, f"Frame: {frame_count}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(screenshot, f"Patterns: {len(self.movement_patterns)}", (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(screenshot, f"Missed: {self.missed_detections}", (10, 180), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Auto-save every 5 minutes
                if time.time() - last_save_time > 300:
                    self.save_patterns(frame_count, "auto_save")
                    last_save_time = time.time()
                
                cv2.imshow('AI Learning', screenshot)
                
                # Key handling
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # q or ESC
                    print("\nStopping and saving data...")
                    break
                elif key == ord('s'):  # Manual save
                    self.save_patterns(frame_count, "manual_save")
                
        except Exception as e:
            print(f"\nError occurred: {e}")
        finally:
            cv2.destroyAllWindows()
            self.save_patterns(frame_count, "final_save")

    def save_patterns(self, frame_count, save_type=""):
        """Save collected patterns to file"""
        try:
            os.makedirs('training_data', exist_ok=True)
            data = {
                'patterns': self.movement_patterns,
                'metadata': {
                    'total_frames': frame_count,
                    'total_patterns': len(self.movement_patterns),
                    'missed_detections': self.missed_detections,
                    'detection_rate': (self.total_detections - self.missed_detections) / self.total_detections if self.total_detections > 0 else 0,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            filename = 'training_data/ai_learning.json'
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            
            print(f"\n{save_type.title()} complete!")
            print(f"Total frames: {frame_count}")
            print(f"Patterns learned: {len(self.movement_patterns)}")
            print(f"Detection rate: {data['metadata']['detection_rate']:.2%}")
            print(f"Data saved to: {filename}")
            
        except Exception as e:
            print(f"\nError saving data: {e}")
            emergency_file = f'training_data/emergency_save_{int(time.time())}.json'
            with open(emergency_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Emergency save created: {emergency_file}")

if __name__ == "__main__":
    tracker = HoopTracker()
    print("=== AI Hoop Learning System ===")
    print("Please open the Telegram Piggy Bank game")
    input("Press Enter when ready...")
    
    tracker.learn_from_game() 
