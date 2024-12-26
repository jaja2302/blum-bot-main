import cv2
import numpy as np
import pyautogui
import time
import json
import os

class HoopTracker:
    def __init__(self):
        self.basket_history = []
        self.history_max = 6
        self.last_detection_time = None
        self.movement_patterns = []
        self.last_prediction = None
        self.load_patterns()

    def load_patterns(self):
        """Load movement patterns from training data"""
        try:
            if os.path.exists('training_data/ai_learning.json'):
                with open('training_data/ai_learning.json', 'r') as f:
                    data = json.load(f)
                    self.movement_patterns = data.get('patterns', [])
                    print(f"Loaded {len(self.movement_patterns)} movement patterns")
        except Exception as e:
            print(f"Error loading patterns: {e}")

    def predict_next_position(self, current_pos, current_time):
        """Predict next hoop position based on learned patterns"""
        if not self.basket_history or not self.movement_patterns:
            return current_pos

        # Get recent movement
        if len(self.basket_history) >= 2:
            prev = self.basket_history[-2]
            curr = self.basket_history[-1]
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            dt = curr[2] - prev[2]
            
            if dt > 0:
                current_speed = ((dx*dx + dy*dy) ** 0.5) / dt
                direction = 1 if dx > 0 else -1
                height = curr[1]

                # Find similar patterns
                similar_patterns = []
                for pattern in self.movement_patterns:
                    if (abs(pattern['speed'] - current_speed) < 20 and
                        pattern['direction'] == direction and
                        abs(pattern['height'] - height) < 30):
                        similar_patterns.append(pattern)

                if similar_patterns:
                    # Use average of similar patterns to predict
                    avg_dx = sum(p['dx'] for p in similar_patterns) / len(similar_patterns)
                    avg_dy = sum(p['dy'] for p in similar_patterns) / len(similar_patterns)
                    
                    predicted_x = current_pos[0] + avg_dx
                    predicted_y = current_pos[1] + avg_dy
                    
                    self.last_prediction = (predicted_x, predicted_y)
                    return self.last_prediction

        return current_pos

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
            
        # Try color detection first
        red_lower = np.array([0, 0, 170])
        red_upper = np.array([15, 25, 255])
        
        red_mask = cv2.inRange(cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR), red_lower, red_upper)
        kernel = np.ones((3,3), np.uint8)
        red_mask = cv2.dilate(red_mask, kernel, iterations=1)
        
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        current_time = time.time()
        position = None
        
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
                    position = (screen_x, screen_y)

        # If we have a tracker instance, use it to predict next position
        if hasattr(get_hoop_position, 'tracker'):
            if position:
                get_hoop_position.tracker.update_history(position, current_time)
                return get_hoop_position.tracker.predict_next_position(position, current_time)
            elif get_hoop_position.tracker.last_prediction:
                return get_hoop_position.tracker.last_prediction
                
        return position
        
    except Exception as e:
        print(f"Error tracking hoop: {e}")
        return None

# Initialize tracker instance
get_hoop_position.tracker = HoopTracker()

def collect_training_data():
    """Collect training data by capturing hoop positions"""
    training_data = []
    return training_data 

    