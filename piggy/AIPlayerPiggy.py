import cv2
import numpy as np
import pyautogui
import time
import keyboard
from datetime import datetime
from modules.hoop_detector import HoopDetector
from modules.score_detector import ScoreDetector
from modules.data_manager import DataManager
from modules.window_manager import WindowManager
from modules.Gameplay import BallDetector
import pytesseract
import signal
import sys
import json

class AIPlayerPiggy:
    def __init__(self):
        self.hoop_detector = HoopDetector()
        self.score_detector = ScoreDetector()
        self.data_manager = DataManager()
        self.window_manager = WindowManager()
        self.ball_detector = BallDetector()
        self.frame_count = 0
        self.last_score = 0
        self.game_active = True
        self.game_stats = self.load_game_stats()
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C interrupt"""
        print("\n\nCtrl+C detected! Saving game data...")
        self.data_manager.save_patterns(self.frame_count, "emergency_save")
        print("\nGame data saved successfully!")
        sys.exit(0)

    def is_game_over(self, screenshot):
        """Deteksi game over dengan OCR"""
        try:
            # Crop bagian tengah screenshot
            height, width = screenshot.shape[:2]
            top_section = screenshot[int(height*0.3):int(height*0.7), int(width*0.2):int(width*0.8)]
            
            # Convert ke grayscale
            gray = cv2.cvtColor(top_section, cv2.COLOR_BGR2GRAY)
            
            # Threshold untuk teks putih
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Deteksi teks
            text = pytesseract.image_to_string(thresh).lower().strip()
            
            # Cek kata kunci game over
            game_over_keywords = ['nice!', 'defeat!', 'you scored', 'ok']
            
            if any(keyword in text for keyword in game_over_keywords):
                print("\nGame Over detected!")
                self.game_active = False
                return True
                
            return False
            
        except Exception as e:
            print(f"Error checking game over: {e}")
            return False

    def load_game_stats(self):
        """Load game statistics"""
        try:
            with open('modules/game_stats.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'games_played': 0,
                'high_score': 0,
                'total_shots': 0,
                'successful_shots': 0,
                'best_positions': []
            }

    def save_game_stats(self, current_score=0):
        """Save updated game statistics"""
        try:
            self.game_stats['games_played'] += 1
            self.game_stats['high_score'] = max(self.game_stats['high_score'], current_score)
            
            # Update shot statistics
            successful_shots = len([shot for shot in self.ball_detector.current_game['shots'] if shot['success']])
            total_shots = len(self.ball_detector.current_game['shots'])
            
            self.game_stats['total_shots'] += total_shots
            self.game_stats['successful_shots'] += successful_shots
            
            # Save successful shot positions for learning
            if successful_shots > 0:
                successful_positions = [shot['hoop_pos'] for shot in self.ball_detector.current_game['shots'] if shot['success']]
                self.game_stats['best_positions'].extend(successful_positions)
                # Keep only last 100 successful positions
                self.game_stats['best_positions'] = self.game_stats['best_positions'][-100:]
            
            # Save to file
            with open('modules/game_stats.json', 'w') as f:
                json.dump(self.game_stats, f, indent=4)
            
            # Print game summary
            print("\n=== Game Summary ===")
            print(f"Games Played: {self.game_stats['games_played']}")
            print(f"Current Score: {current_score}")
            print(f"High Score: {self.game_stats['high_score']}")
            if total_shots > 0:
                print(f"Success Rate: {(successful_shots/total_shots*100):.1f}%")
            if self.game_stats['total_shots'] > 0:
                print(f"Total Success Rate: {(self.game_stats['successful_shots']/self.game_stats['total_shots']*100):.1f}%")
            print()
            
        except Exception as e:
            print(f"\nError saving game stats: {e}")
            # Create backup of stats
            try:
                backup_file = f'modules/game_stats_backup_{int(time.time())}.json'
                with open(backup_file, 'w') as f:
                    json.dump(self.game_stats, f, indent=4)
                print(f"Backup saved to: {backup_file}")
            except:
                print("Failed to create backup")

    def learn_from_game(self):
        while True:  # Loop untuk multiple games
            print("\nStarting new game...")
            print("\nControls:")
            print("SPACE - Pause/Resume")
            print("Q     - Quit Bot")
            print("E     - End Current Game")
            
            window_rect = self.window_manager.get_game_window()
            if not window_rect:
                return
                
            x, y, w, h = window_rect
            self.frame_count = 0
            self.last_score = 0
            self.paused = False
            self.game_active = True
            self.ball_detector.current_game = {'shots': [], 'score': 0, 'success_rate': 0}  # Reset game data
            
            try:
                while self.game_active:
                    if keyboard.is_pressed('q'):
                        print("\nStopping bot...")
                        self.save_game_stats(self.last_score)
                        self.data_manager.save_patterns(self.frame_count, "manual_save")
                        time.sleep(0.3)
                        return
                        
                    if keyboard.is_pressed('e'):
                        print("\nManually ending current game...")
                        self.save_game_stats(self.last_score)
                        self.game_active = False
                        break
                        
                    if keyboard.is_pressed('space'):
                        self.paused = not self.paused
                        print("\nBot PAUSED" if self.paused else "\nBot RESUMED")
                        time.sleep(0.3)
                    
                    if self.paused:
                        time.sleep(0.1)
                        continue
                    
                    screenshot = np.array(pyautogui.screenshot(region=(x, y, w, h)))
                    self.frame_count += 1
                    
                    if self.is_game_over(screenshot):
                        self.save_game_stats(self.last_score)
                        print("\nStart new game? (y/n)")
                        time.sleep(0.3)
                        while True:
                            if keyboard.is_pressed('y'):
                                print("\nStarting new game...")
                                time.sleep(0.3)
                                break
                            if keyboard.is_pressed('n'):
                                return
                        break
                    
                    hoop_pos = self.hoop_detector.detect_hoop(screenshot)
                    current_score = self.score_detector.detect_score(screenshot)
                    
                    if current_score and current_score != self.last_score:
                        self.ball_detector.record_shot(hoop_pos, True)
                        self.last_score = current_score
                    
                    if hoop_pos and self.game_active:
                        # Use best positions for learning
                        if self.game_stats['best_positions']:
                            closest_good_pos = min(self.game_stats['best_positions'], 
                                                 key=lambda p: ((p[0]-hoop_pos[0])**2 + (p[1]-hoop_pos[1])**2)**0.5)
                            # Adjust shot based on learned positions
                            adjusted_pos = (
                                int((hoop_pos[0] + closest_good_pos[0])/2),
                                int((hoop_pos[1] + closest_good_pos[1])/2)
                            )
                            if self.ball_detector.shoot_to_hoop(window_rect, adjusted_pos):
                                self.ball_detector.record_shot(hoop_pos, False)
                                time.sleep(0.2)
                        else:
                            if self.ball_detector.shoot_to_hoop(window_rect, hoop_pos):
                                self.ball_detector.record_shot(hoop_pos, False)
                                time.sleep(0.2)
                    
                    cv2.imshow('AI Learning', screenshot)
                    if cv2.waitKey(1) & 0xFF == 27:
                        self.save_game_stats(self.last_score)
                        return
                        
            except Exception as e:
                print(f"\nError: {e}")
                self.save_game_stats(self.last_score)
                
            finally:
                cv2.destroyAllWindows()

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

if __name__ == "__main__":
    ai_player = AIPlayerPiggy()
    print("=== AI Hoop Learning System ===")
    print("Please open the Telegram Piggy Bank game")
    print("\nControls:")
    print("SPACE - Pause/Resume")
    print("Q     - Quit Bot")
    print("E     - End Current Game")
    input("\nPress Enter when ready...")
    
    try:
        ai_player.learn_from_game()
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
    finally:
        ai_player.data_manager.save_patterns(ai_player.frame_count, "final_save") 