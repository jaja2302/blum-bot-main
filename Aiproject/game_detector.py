import cv2
import numpy as np
import json
import os
import pytesseract
from PIL import Image
from hoop_detector import HoopDetector

class GameDetector:
    def __init__(self):
        # Load koordinat bola dari JSON
        try:
            json_path = os.path.join('modules', 'coordinates.json')
            with open(json_path) as f:
                coords = json.load(f)
                self.ball_position = coords['ball_positions'][0]
        except FileNotFoundError:
            print("Warning: coordinates.json tidak ditemukan")
            self.ball_position = {'x': 198, 'y': 501}  # Default coordinates
        
        # Inisialisasi HoopDetector
        self.hoop_detector = HoopDetector()
        self.last_status = None
        
        # Setup path Tesseract jika belum di environment PATH
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def detect_game_elements(self, screenshot):
        """Deteksi semua elemen game dalam screenshot"""
        try:
            # 1. Cek maintenance terlebih dahulu
            if self.is_maintenance_screen(screenshot):
                if self.last_status != 'maintenance':
                    print("Game sedang maintenance...")
                    self.last_status = 'maintenance'
                return {
                    'status': 'maintenance',
                    'message': 'Game sedang maintenance'
                }

            # 2. Cek hoop terlebih dahulu
            hoop_pos = self.hoop_detector.detect_hoop(screenshot)
            if not hoop_pos:
                if self.last_status != 'no_hoop':
                    print("Ring tidak terdeteksi, menunggu...")
                    self.last_status = 'no_hoop'
                return {
                    'status': 'waiting',
                    'message': 'Ring tidak terdeteksi'
                }

            # 3. Jika hoop terdeteksi, lanjutkan dengan deteksi lainnya
            self.last_status = 'active'
            return {
                'status': 'active',
                'ball_position': (self.ball_position['x'], self.ball_position['y']),
                'hoop_position': hoop_pos,
                'ball_found': True
            }

        except Exception as e:
            print(f"Error dalam deteksi game: {e}")
            return None

    def is_maintenance_screen(self, screenshot):
        """Deteksi maintenance screen menggunakan OCR"""
        try:
            # Convert ke PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
            
            # Ekstrak text dari gambar
            text = pytesseract.image_to_string(pil_image).lower()
            
            # Cek keywords maintenance
            maintenance_keywords = [
                'technical timeout',
                'maintenance',
                'we\'ll be back',
                'oink'
            ]
            
            # Jika ada keyword maintenance, return True
            if any(keyword in text for keyword in maintenance_keywords):
                if self.last_status != 'maintenance':
                    print("Terdeteksi maintenance screen!")
                    self.last_status = 'maintenance'
                return True
                
            return False
            
        except Exception as e:
            print(f"Error dalam OCR: {e}")
            return False 