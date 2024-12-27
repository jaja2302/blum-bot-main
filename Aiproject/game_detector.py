import cv2
import numpy as np
import json
import os
import pytesseract
from PIL import Image
from hoop_detector import HoopDetector
import time

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
        
        # Load koordinat tombol claim
        try:
            # Coba gunakan os.path untuk memastikan path yang benar
            import os
            json_path = os.path.join(os.path.dirname(__file__), 'button_claim_game_over.json')
            print(f"\nDebug: Mencoba membaca file JSON dari: {json_path}")
            
            with open(json_path, 'r') as f:
                self.button_config = json.load(f)
                print("Debug: Berhasil membaca konfigurasi tombol")
        except Exception as e:
            print(f"Debug: Error loading button config: {e}")
            print(f"Debug: Current working directory: {os.getcwd()}")
            self.button_config = None

    def start_game(self):
        """Set flag game dimulai dan mulai timer"""
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
            print("Debug: Button config tidak ditemukan!")
            return None
            
        try:
            claim_btn = self.button_config['buttons']['claim']
            absolute_x = window_info['left'] + claim_btn['x']
            absolute_y = window_info['top'] + claim_btn['y']
            
            print(f"\nDebug: Posisi tombol claim:")
            print(f"- Relatif: ({claim_btn['x']}, {claim_btn['y']})")
            print(f"- Window offset: ({window_info['left']}, {window_info['top']})")
            print(f"- Absolut: ({absolute_x}, {absolute_y})")
            
            return (absolute_x, absolute_y)
        except Exception as e:
            print(f"Debug: Error saat menghitung posisi tombol: {e}")
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
            
            # Ekstrak text dari gambar
            text = pytesseract.image_to_string(pil_image).lower()
            
            # Cek kata kunci hasil pertandingan
            result_keywords = ['defeat', 'nice', 'you scored', 'ok']
            if any(keyword in text for keyword in result_keywords):
                # Debug: Print text yang terdeteksi
                print("\nGame Over terdeteksi dengan text:")
                print(text)
                return True
            
            # Jika tidak ada keyword terdeteksi, cek warna merah
            rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            height = screenshot.shape[0]
            
            # Fokus pada area tengah
            roi = rgb[int(height*0.2):int(height*0.6), :]
            
            # Deteksi warna merah (untuk Defeat) dan hijau (untuk Nice/OK button)
            red_mask = cv2.inRange(roi, np.array([150, 0, 0]), np.array([255, 100, 100]))
            green_mask = cv2.inRange(roi, np.array([0, 150, 0]), np.array([100, 255, 100]))
            
            red_pixels = cv2.countNonZero(red_mask)
            green_pixels = cv2.countNonZero(green_mask)
            
            # Return true jika ada cukup pixel merah atau hijau
            return red_pixels > 500 or green_pixels > 1000
            
        except Exception as e:
            print(f"Error checking game over: {e}")
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
        except Exception as e:
            print(f"Debug: Error getting {button_name} button position: {e}")
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
                print(f"Debug: Terdeteksi 'Opponent Found' di layar!")
                return {
                    'state': GameState.OPPONENT_FOUND,
                    'action': 'click_go'
                }
            
            # Deteksi menu betting
            text = pytesseract.image_to_string(Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))).lower()
            if 'player vs player' in text:
                print("Debug: Terdeteksi menu betting!")
                return {
                    'state': GameState.UNKNOWN,
                    'action': 'click_bet'
                }
            
            return {
                'state': GameState.UNKNOWN,
                'action': None
            }
        except Exception as e:
            print(f"Error detecting game state: {e}")
            return None 