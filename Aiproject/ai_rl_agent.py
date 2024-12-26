import numpy as np
import math
import time
from collections import deque

class RLAgent:
    def __init__(self):
        self.last_pos = None
        self.last_time = None
        self.movement_threshold = 1
        self.last_log_time = 0
        self.log_interval = 0.05
        self.last_shot_time = 0
        self.shot_cooldown = 0.1  # Ubah ke 0.1 untuk 10 tembakan/detik
        
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
                                
                        print(f"Ring: ({x}, {y}) | {movement} | {speed_category} | {speed_value:.1f} px/s | dt={dt*1000:.0f}ms")
                        self.last_log_time = current_time
            
            # Update posisi terakhir
            self.last_pos = hoop_pos
            self.last_time = current_time
            
            # Cek cooldown tembakan
            if current_time - self.last_shot_time < self.shot_cooldown:
                return None  # Skip tembakan jika masih dalam cooldown
            
            self.last_shot_time = current_time
            
            # Posisi bola dan perhitungan tembakan
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - 200
            
            dx = x - ball_x
            dy = ball_y - y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.degrees(math.atan2(dy, dx))
            power = min(0.8, max(0.4, distance / 400))
            
            return (angle, power)
            
        except Exception as e:
            print(f"Error menghitung tembakan: {e}")
            return (45, 0.6) 