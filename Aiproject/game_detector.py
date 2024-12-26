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

class GameDetector:
    def __init__(self):
        self.last_state = GameState.UNKNOWN
        self.hoop_detector = HoopDetector()
        self.game_started = False
        self.game_start_time = None
        self.GAME_DURATION = 45  # Durasi game 45 detik
        
    def start_game(self):
        """Set flag game dimulai dan mulai timer"""
        self.game_started = True
        self.game_start_time = time.time()
        self.last_state = GameState.UNKNOWN
        print("\nGame dimulai! Menunggu ring terdeteksi...")
        
    def stop_game(self):
        """Reset flag game dan timer"""
        self.game_started = False
        self.game_start_time = None
        self.last_state = GameState.UNKNOWN
        
    def detect_game_elements(self, screenshot):
        """Deteksi ring saat game aktif"""
        try:
            # Jika game belum dimulai, tunggu
            if not self.game_started:
                return {
                    'status': 'waiting',
                    'message': 'Waiting for game to start'
                }
            
            current_time = time.time()
            elapsed_time = current_time - self.game_start_time
            remaining_time = max(0, self.GAME_DURATION - elapsed_time)
            
            # Cek game over hanya saat mendekati atau melewati batas waktu
            if remaining_time <= 2:  # Cek 2 detik sebelum dan setelah game berakhir
                if self.is_game_over(screenshot):
                    if self.last_state != GameState.GAME_OVER:
                        print("\nGame selesai! Tekan SPACE untuk memulai game baru...")
                        self.last_state = GameState.GAME_OVER
                        self.game_started = False
                    return {
                        'status': 'game_over',
                        'message': 'Game is over'
                    }
            
            # Cek active game dengan mencari ring
            hoop_pos = self.hoop_detector.detect_hoop(screenshot)
            if hoop_pos:
                if self.last_state != GameState.ACTIVE:
                    print("\nRing terdeteksi! Memulai tracking...")
                    self.last_state = GameState.ACTIVE
                
                # Log pergerakan ring dengan sisa waktu
                x, y = hoop_pos
                print(f"Ring: ({x}, {y}) | Arah: {'Kanan' if x > 200 else 'Kiri'} | Ketinggian: {y} | Waktu: {int(remaining_time)}s")
                
                return {
                    'status': 'active',
                    'hoop_position': hoop_pos,
                    'direction': 'right' if x > 200 else 'left',
                    'height': y,
                    'remaining_time': int(remaining_time)
                }
            
            # Reset state jika tidak ada ring terdeteksi
            if self.last_state != GameState.UNKNOWN:
                print("\nMenunggu ring terdeteksi...")
                self.last_state = GameState.UNKNOWN
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