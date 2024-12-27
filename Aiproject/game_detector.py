import cv2
import numpy as np
import json
import os
import pytesseract
from PIL import Image
from hoop_detector import HoopDetector
import time
from game_stats import GameStats
# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class GameState:
    UNKNOWN = 'unknown'
    ACTIVE = 'active'
    GAME_OVER = 'game_over'
    FINDING_OPPONENT = 'finding_opponent'
    OPPONENT_FOUND = 'opponent_found'
    READY_TO_PLAY = 'ready_to_play'

class GameDetector:
    def __init__(self):
        self.last_state = GameState.UNKNOWN
        self.hoop_detector = HoopDetector()
        self.game_started = False
        self.game_start_time = None
        self.GAME_DURATION = 48
        self.last_hoop_pos = None
        self.game_stats = GameStats()
        
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'button_claim_game_over.json')
            with open(json_path, 'r') as f:
                self.button_config = json.load(f)
        except Exception as e:
            self.button_config = None

    def start_game(self):
        self.game_started = True
        self.game_start_time = time.time()
        self.last_state = GameState.UNKNOWN
        self.last_hoop_pos = None
        print("\nGame dimulai! Menunggu ring terdeteksi...")
        
    def stop_game(self):
        """Reset flag game dan timer"""
        self.game_started = False
        self.game_start_time = None
        self.last_state = GameState.UNKNOWN
        
    def get_claim_button_pos(self, window_info):
        """Menghitung posisi absolut tombol claim"""
        if not self.button_config:
            return None
            
        try:
            claim_btn = self.button_config['buttons']['claim']
            absolute_x = window_info['left'] + claim_btn['x']
            absolute_y = window_info['top'] + claim_btn['y']
            return (absolute_x, absolute_y)
        except Exception as e:
            return None

    def detect_game_elements(self, screenshot):
        """Deteksi ring saat game aktif"""
        try:
            if not self.game_started:
                return {
                    'status': 'waiting',
                    'message': 'Waiting for game to start'
                }
            
            current_time = time.time()
            elapsed_time = current_time - self.game_start_time
            remaining_time = max(0, self.GAME_DURATION - elapsed_time)
            
            # Cek game over di 2 detik terakhir
            if remaining_time <= 2:
                if self.is_game_over(screenshot):
                    if self.last_state != GameState.GAME_OVER:
                        print("\nGame selesai! Mengklik tombol claim...")
                        self.last_state = GameState.GAME_OVER
                        self.game_started = False
                    return {
                        'status': 'game_over',
                        'message': 'Game is over',
                        'should_claim': True  # Flag baru untuk mengindikasikan perlu klik claim
                    }
            
            # Deteksi ring tanpa spam log
            hoop_pos = self.hoop_detector.detect_hoop(screenshot)
            if hoop_pos:
                return {
                    'status': 'active',
                    'hoop_position': hoop_pos,
                    'direction': 'right' if hoop_pos[0] > 200 else 'left',
                    'height': hoop_pos[1],
                    'remaining_time': int(remaining_time)
                }
            
            return {
                'status': 'waiting',
                'message': 'Waiting for ring'
            }

        except Exception as e:
            print(f"Error dalam deteksi game: {e}")
            return None

    def is_game_over(self, screenshot):
        """Deteksi apakah game sudah selesai"""
        try:
            # Convert ke RGB untuk OCR
            pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
            text = pytesseract.image_to_string(pil_image).lower()
            
            # Cek kata kunci hasil pertandingan
            result_keywords = ['defeat', 'nice', 'winner', 'you scored', 'ok']
            if any(keyword in text for keyword in result_keywords):
                print("\n=== Hasil Pertandingan ===")
                if 'defeat' in text:
                    print("Status: DEFEAT")
                elif 'nice' in text:
                    print("Status: NICE")
                elif 'winner' in text:
                    print("Status: WINNER")
                print("========================")
                
                # Update statistik
                self.game_stats.update_stats(text)
                self.game_stats.print_stats()
                return True
            
            # Deteksi warna sebagai backup
            rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            height = screenshot.shape[0]
            roi = rgb[int(height*0.2):int(height*0.6), :]
            
            red_mask = cv2.inRange(roi, np.array([150, 0, 0]), np.array([255, 100, 100]))
            green_mask = cv2.inRange(roi, np.array([0, 150, 0]), np.array([100, 255, 100]))
            
            red_pixels = cv2.countNonZero(red_mask)
            green_pixels = cv2.countNonZero(green_mask)
            
            if red_pixels > 500 or green_pixels > 1000:
                # Jika deteksi warna menunjukkan game over tapi OCR gagal
                print("\nGame Over terdeteksi (berdasarkan warna)")
                self.game_stats.print_stats()
                return True
            
            return False
            
        except Exception as e:
            return False

    def get_button_position(self, button_name, window_info):
        """Mendapatkan posisi absolut tombol berdasarkan nama"""
        if not self.button_config:
            return None
        
        try:
            btn = self.button_config['buttons'][button_name]
            return (
                window_info['left'] + btn['x'],
                window_info['top'] + btn['y']
            )
        except Exception:
            return None

    def detect_game_state(self, screenshot):
        """Deteksi state game saat ini"""
        try:
            # Preprocessing untuk area opponent found
            height, width = screenshot.shape[:2]
            opponent_area = screenshot[height//4:height//2, width//4:3*width//4]
            
            # Convert ke grayscale dan threshold
            gray = cv2.cvtColor(opponent_area, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            
            # OCR untuk area opponent
            opponent_text = pytesseract.image_to_string(thresh).lower()
            
            # Cek opponent found
            opponent_keywords = ['opponent found', 'opponent', 'found', 'go!']
            if any(keyword in opponent_text for keyword in opponent_keywords):
                return {
                    'state': GameState.OPPONENT_FOUND,
                    'action': 'click_go'
                }
            
            # Deteksi menu betting
            text = pytesseract.image_to_string(Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))).lower()
            if 'player vs player' in text:
                return {
                    'state': GameState.UNKNOWN,
                    'action': 'click_bet'
                }
            
            return {
                'state': GameState.UNKNOWN,
                'action': None
            }
        except Exception:
            return None 