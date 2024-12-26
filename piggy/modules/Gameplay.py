import cv2
import numpy as np
import pyautogui
import win32gui
import time
import json
from pynput.mouse import Button, Controller
import pytesseract

class WindowManager:
    def get_game_window(self):
        """Find the Telegram window"""
        def callback(hwnd, windows):
            if "Telegram" in win32gui.GetWindowText(hwnd):
                windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if not windows:
            print("Telegram window not found!")
            return None
            
        hwnd = windows[0]
        rect = win32gui.GetWindowRect(hwnd)
        x, y, x2, y2 = rect
        w = x2 - x
        h = y2 - y
        
        print(f"Found Telegram window: {w}x{h} at ({x}, {y})")
        return (x, y, w, h)

class BallDetector:
    def __init__(self):
        self.window_manager = WindowManager()
        self.mouse = Controller()
        self.shot_delay = 0.2
        self.start_time = time.time()
        self.game_stats = self.load_game_stats()
        self.current_game = {
            'shots': [],
            'score': 0,
            'success_rate': 0
        }

    def load_game_stats(self):
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

    def save_game_stats(self):
        with open('modules/game_stats.json', 'w') as f:
            json.dump(self.game_stats, f, indent=4)

    def record_shot(self, hoop_pos, score_changed):
        """Record shot data"""
        self.current_game['shots'].append({
            'hoop_pos': hoop_pos,
            'success': score_changed,
            'time': time.time() - self.start_time
        })

    def analyze_game(self, final_score):
        self.game_stats['games_played'] += 1
        self.game_stats['high_score'] = max(self.game_stats['high_score'], final_score)
        
        successful_shots = len([shot for shot in self.current_game['shots'] if shot['success']])
        total_shots = len(self.current_game['shots'])
        
        if successful_shots > 0:
            # Tambahkan posisi ring yang berhasil ke best_positions
            successful_positions = [shot['hoop_pos'] for shot in self.current_game['shots'] if shot['success']]
            self.game_stats['best_positions'].extend(successful_positions)
            # Batasi jumlah best_positions yang disimpan
            self.game_stats['best_positions'] = self.game_stats['best_positions'][-100:]
        
        self.game_stats['total_shots'] += total_shots
        self.game_stats['successful_shots'] += successful_shots
        
        self.save_game_stats()
        return successful_shots, total_shots

    def print_game_summary(self, final_score):
        successful_shots, total_shots = self.analyze_game(final_score)
        success_rate = (successful_shots / total_shots * 100) if total_shots > 0 else 0
        
        print("\n=== Game Summary ===")
        print(f"Final Score: {final_score}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Games Played: {self.game_stats['games_played']}")
        print(f"High Score: {self.game_stats['high_score']}")
        
        return success_rate > 50  # Return True jika success rate di atas 50%

    def shoot_to_hoop(self, window_rect, hoop_pos):
        """Shoot dari posisi bola tetap ke ring"""
        try:
            with open('modules/coordinates.json', 'r') as f:
                coordinates = json.load(f)
            
            if coordinates['ball_positions'] and hoop_pos:
                ball_pos = coordinates['ball_positions'][0]
                # Konversi ke koordinat layar
                start_x = window_rect[0] + ball_pos['x']
                start_y = window_rect[1] + ball_pos['y']
                target_x = window_rect[0] + hoop_pos[0]
                target_y = window_rect[1] + hoop_pos[1]

                # Quick swipe
                self.mouse.position = (start_x, start_y)
                time.sleep(0.02)
                self.mouse.press(Button.left)
                time.sleep(0.02)
                self.mouse.position = (target_x, target_y)
                time.sleep(0.02)
                self.mouse.release(Button.left)
                time.sleep(0.02)

                return True

        except Exception as e:
            print(f"Error during shoot: {e}")
        
        return False

    def reset_timer(self):
        """Reset timer untuk game baru"""
        self.start_time = time.time()

if __name__ == "__main__":
    detector = BallDetector()
    detector.calibrate_position() 