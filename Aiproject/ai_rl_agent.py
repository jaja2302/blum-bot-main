import numpy as np
import math
import time
from collections import deque
# kk
class RLAgent:
    def __init__(self):
        self.last_pos = None
        self.last_time = None
        self.movement_threshold = 2  # Perubahan threshold agar lebih toleran terhadap noise
        self.last_log_time = 0
        self.log_interval = 0.05
        self.prediction_factor = 0.8  # Faktor prediksi yang telah disesuaikan

    def get_action(self, game_screen, hoop_pos):
        """Tentukan parameter tembakan berdasarkan posisi ring"""
        try:
            x, y = hoop_pos
            current_time = time.time()
            
            # Deteksi pergerakan dan kecepatan
            movement = "DIAM"
            speed_category = "DIAM"
            speed_value = 0
            
            if self.last_pos:
                dx = x - self.last_pos[0]
                dt = max(current_time - self.last_time, 1e-6)  # Hindari pembagian dengan nol
                
                if dt > 0:
                    speed_value = abs(dx) / dt
                    
                    # Log lebih sering
                    if current_time - self.last_log_time >= self.log_interval:
                        if abs(dx) > self.movement_threshold:
                            movement = "KANAN" if dx > 0 else "KIRI"
                            if speed_value > 120:
                                speed_category = "CEPAT"
                            elif speed_value > 60:
                                speed_category = "SEDANG"
                            elif speed_value > 30:
                                speed_category = "LAMBAT"
                                
                        # Debug log (opsional)
                        # print(f"Ring: ({x}, {y}) | {movement} | {speed_category} | {speed_value:.1f} px/s | dt={dt*1000:.0f}ms")
                        self.last_log_time = current_time
            
            # Hitung prediksi posisi ring
            predicted_x = x
            if self.last_pos and self.last_time:
                dx = x - self.last_pos[0]
                dt = max(current_time - self.last_time, 1e-6)  # Hindari pembagian dengan nol
                
                if dt > 0 and abs(dx) > self.movement_threshold:
                    direction = 1 if dx > 0 else -1
                    predicted_x = x + (direction * speed_value * self.prediction_factor)
                    
                    # Pastikan prediksi berada dalam dimensi layar
                    predicted_x = min(max(predicted_x, 0), game_screen.shape[1])
            
            # Update posisi terakhir
            self.last_pos = hoop_pos
            self.last_time = current_time
            
            # Gunakan predicted_x untuk perhitungan tembakan
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - 200
            
            dx = predicted_x - ball_x  # Gunakan posisi prediksi
            dy = ball_y - y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.degrees(math.atan2(dy, dx))
            
            # Sesuaikan power berdasarkan jarak
            power = min(0.85, max(0.4, distance / 350))
            
            return (angle, power)
            
        except Exception as e:
            print(f"Error menghitung tembakan: {e}")
            return (45, 0.6)

    def __init__(self):
        self.last_pos = None
        self.last_time = None
        self.movement_threshold = 1
        self.last_log_time = 0
        self.log_interval = 0.05
        self.prediction_factor = 0.8 # Faktor prediksi yang sudah disesuaikan
        
    def get_action(self, game_screen, hoop_pos):
        """Tentukan parameter tembakan berdasarkan posisi ring"""
        try:
            x, y = hoop_pos
            current_time = time.time()
            
            # Deteksi pergerakan dan kecepatan
            movement = "DIAM"
            speed_category = "DIAM"
            speed_value = 0
            
            if self.last_pos:
                dx = x - self.last_pos[0]
                dt = current_time - self.last_time if self.last_time else 0
                
                if dt > 0:
                    speed_value = abs(dx) / dt
                    
                    # Log lebih sering
                    if current_time - self.last_log_time >= self.log_interval:
                        if abs(dx) > self.movement_threshold:
                            movement = "KANAN" if dx > 0 else "KIRI"
                            if speed_value > 120:
                                speed_category = "CEPAT"
                            elif speed_value > 60:
                                speed_category = "SEDANG"
                            elif speed_value > 30:
                                speed_category = "LAMBAT"
                                
                        # print(f"Ring: ({x}, {y}) | {movement} | {speed_category} | {speed_value:.1f} px/s | dt={dt*1000:.0f}ms")
                        self.last_log_time = current_time
            
            # Hitung prediksi posisi ring
            predicted_x = x
            if self.last_pos and self.last_time:
                dx = x - self.last_pos[0]
                dt = current_time - self.last_time
                
                if dt > 0:
                    speed_value = abs(dx) / dt
                    if abs(dx) > self.movement_threshold:
                        direction = 1 if dx > 0 else -1
                        predicted_x = x + (direction * speed_value * self.prediction_factor)
                        predicted_x = min(max(predicted_x, 0), game_screen.shape[1])
            
            # Update posisi terakhir
            self.last_pos = hoop_pos
            self.last_time = current_time
            
            # Gunakan predicted_x untuk perhitungan tembakan
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - 200
            
            dx = predicted_x - ball_x  # Gunakan posisi prediksi
            dy = ball_y - y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.degrees(math.atan2(dy, dx))
            
            # Sesuaikan power berdasarkan jarak
            power = min(0.85, max(0.4, distance / 350))
            
            return (angle, power)
            
        except Exception as e:
            print(f"Error menghitung tembakan: {e}")
            return (45, 0.6) 