import cv2
import numpy as np
import pyautogui
import time
from datetime import datetime
from modules.hoop_detector import HoopDetector
from modules.score_detector import ScoreDetector
from modules.data_manager import DataManager
from modules.window_manager import WindowManager
import pytesseract

class AIPlayerPiggy:
    def __init__(self):
        self.hoop_detector = HoopDetector()
        self.score_detector = ScoreDetector()
        self.data_manager = DataManager()
        self.window_manager = WindowManager()
        
        self.basket_history = []
        self.history_max = 6
        self.missed_detections = 0
        self.total_detections = 0

    def learn_from_game(self):
        """Learn hoop movement patterns from live game"""
        print("\nStarting AI learning process...")
        print("Using enhanced detection with adaptive color and shape detection")
        
        # Get Telegram window
        window_rect = self.window_manager.get_game_window()
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
                screenshot = np.array(pyautogui.screenshot(region=(x, y, w, h)))
                frame_count += 1
                current_time = time.time() - start_time
                
                # Detect hoop and score
                hoop_pos = self.hoop_detector.detect_hoop(screenshot)
                score = self.score_detector.detect_score(screenshot)
                
                # Check for game end
                if self.score_detector.detect_game_end(screenshot):
                    print("\nGame finished! Detected end game message")
                    self.data_manager.save_patterns(frame_count, "game_end_save")
                    break
                
                self.total_detections += 1
                
                if hoop_pos:
                    if self.missed_detections > 0:
                        print("\nHoop detection resumed!")
                        self.missed_detections = 0
                    
                    self.data_manager.update_history(hoop_pos, current_time)
                    self.hoop_detector.draw_target_box(screenshot, hoop_pos)
                else:
                    self.missed_detections += 1
                    cv2.putText(screenshot, "Lost Detection!", (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Display stats
                self.draw_stats(screenshot, frame_count, score, current_time)
                
                # Auto-save every 5 minutes
                if time.time() - last_save_time > 300:
                    self.data_manager.save_patterns(frame_count, "auto_save")
                    last_save_time = time.time()
                
                cv2.imshow('AI Learning', screenshot)
                
                if self.handle_keys():
                    break
                
        except Exception as e:
            print(f"\nError occurred: {e}")
        finally:
            cv2.destroyAllWindows()
            self.data_manager.save_patterns(frame_count, "final_save")

    def draw_stats(self, screenshot, frame_count, score, game_time):
        h, w = screenshot.shape[:2]
        cv2.putText(screenshot, f"Frame: {frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(screenshot, f"Score: {score}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(screenshot, f"Time: {game_time}", (w - 150, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def handle_keys(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # q or ESC
            print("\nStopping and saving data...")
            self.data_manager.save_patterns(self.total_detections, "final_save")
            return True
        elif key == ord('s'):  # Manual save
            self.data_manager.save_patterns(self.total_detections, "manual_save")
        return False

    def detect_game_end(self, screenshot):
        """Detect if game ended by looking for 'Nice!' text"""
        # Convert to grayscale
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # Threshold for white text
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Use OCR to detect text
        try:
            text = pytesseract.image_to_string(thresh).lower().strip()
            return "nice" in text or "ok" in text
        except:
            return False

if __name__ == "__main__":
    ai_player = AIPlayerPiggy()
    print("=== AI Hoop Learning System ===")
    print("Please open the Telegram Piggy Bank game")
    input("Press Enter when ready...")
    
    ai_player.learn_from_game() 