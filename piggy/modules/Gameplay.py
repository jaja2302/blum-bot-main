import numpy as np
import win32gui
import time

class WindowManager:
    def get_game_window(self):
        """Find the Telegram window"""
        def callback(hwnd, windows):
            if "Telegram" in win32gui.GetWindowText(hwnd) and win32gui.IsWindowVisible(hwnd):
                windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if not windows:
            print("Telegram window not found!")
            return None
            
        hwnd = windows[0]
        
        # Ensure window is not minimized
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
            time.sleep(0.5)  # Give window time to restore
            
        rect = win32gui.GetWindowRect(hwnd)
        x, y, x2, y2 = rect
        w = x2 - x
        h = y2 - y
        
        # Validate window dimensions
        if w <= 0 or h <= 0:
            print(f"Invalid window dimensions: {w}x{h}")
            return None
            
        print(f"Found Telegram window: {w}x{h} at ({x}, {y})")
        return (x, y, w, h)
import cv2
import numpy as np
import pyautogui
import time
import json

class BallDetector:
    def __init__(self):
        self.last_position = None
        self.current_position = None
        self.consecutive_failures = 0
        self.max_failures = 5  # Maximum consecutive failures before warning

    def calibrate_position(self):
        """Get initial ball position with improved error handling and validation"""
        try:
            with open('modules/coordinates.json', 'r') as f:
                data = json.load(f)
                if not data.get('ball_positions'):
                    self.consecutive_failures += 1
                    print(f"No ball positions found (attempt {self.consecutive_failures}/{self.max_failures})")
                    return None

                new_position = (
                    data['ball_positions'][0]['x'],
                    data['ball_positions'][0]['y']
                )
                
                # Validate coordinates
                if not all(isinstance(coord, (int, float)) for coord in new_position):
                    print("Invalid coordinate types detected")
                    return None
                    
                if not all(0 <= coord <= 2000 for coord in new_position):  # Reasonable screen bounds
                    print("Coordinates out of reasonable bounds")
                    return None

                # Reset failure counter on success
                if new_position != self.current_position:
                    self.last_position = self.current_position
                    self.current_position = new_position
                    print(f"Ball position updated: {self.current_position}")
                
                self.consecutive_failures = 0
                return self.current_position

        except FileNotFoundError:
            print("coordinates.json not found. Please ensure file exists in modules directory")
        except json.JSONDecodeError:
            print("Error parsing coordinates.json. Please check file format")
        except Exception as e:
            print(f"Error loading ball position: {str(e)}")
            
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_failures:
            print("WARNING: Multiple consecutive failures in ball detection!")
        return None

    def execute_shot(self, window_rect, target_pos):
        """Execute the shot with improved validation and error handling"""
        if not self.current_position or not target_pos:
            print("Missing current position or target position")
            return False

        if not window_rect or len(window_rect) != 4:
            print("Invalid window rectangle")
            return False

        try:
            # Validate window bounds
            x = window_rect[0] + target_pos[0]
            y = window_rect[1] + target_pos[1]
            
            if not (0 <= x <= pyautogui.size()[0] and 0 <= y <= pyautogui.size()[1]):
                print("Target position outside screen bounds")
                return False
            
            # Add small random variation to prevent detection
            x += np.random.randint(-2, 3)
            y += np.random.randint(-2, 3)
            
            # Smoother mouse movement
            pyautogui.moveTo(x, y, duration=0.1)
            time.sleep(0.05)
            pyautogui.click()
            
            return True
            
        except Exception as e:
            print(f"Error executing shot: {str(e)}")
            return False

    def update_learning(self, shot_info):
        """Update learning data with validation"""
        if not isinstance(shot_info, dict):
            print("Invalid shot info format")
            return False
            
        required_keys = ['ball_pos', 'target_pos', 'timestamp']
        if not all(key in shot_info for key in required_keys):
            print("Missing required shot information")
            return False

        try:
            with open('modules/successful_shots.json', 'a+') as f:
                try:
                    f.seek(0)
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {'shots': []}
                
                # Validate and clean shot data
                shot_info = {
                    'ball_pos': tuple(map(float, shot_info['ball_pos'])),
                    'target_pos': tuple(map(float, shot_info['target_pos'])),
                    'timestamp': float(shot_info['timestamp'])
                }
                
                data['shots'].append(shot_info)
                data['shots'] = data['shots'][-1000:]  # Keep last 1000 shots
                
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=4)
                return True
                
        except Exception as e:
            print(f"Error updating learning data: {str(e)}")
            return False

if __name__ == "__main__":
    detector = BallDetector()
    detector.calibrate_position() 