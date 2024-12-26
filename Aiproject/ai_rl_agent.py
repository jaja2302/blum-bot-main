import numpy as np
import random
import math

class RLAgent:
    def __init__(self):
        self.last_hoop_pos = None
        self.last_shot_success = False
        self.base_angles = [30, 45, 60]  # Sudut dasar untuk menembak
        self.base_powers = [0.4, 0.6, 0.8]  # Power dasar untuk menembak
        
    def get_action(self, game_screen, hoop_pos):
        """Tentukan parameter tembakan berdasarkan posisi ring"""
        try:
            x, y = hoop_pos
            
            # Prediksi pergerakan ring
            hoop_direction = 0
            if self.last_hoop_pos:
                hoop_direction = x - self.last_hoop_pos[0]  # Positif = ke kanan, Negatif = ke kiri
            self.last_hoop_pos = hoop_pos
            
            # Hitung jarak dari posisi bola (tengah bawah)
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - 200
            dx = x - ball_x
            dy = ball_y - y  # Dibalik karena koordinat y terbalik
            
            # Hitung sudut berdasarkan posisi ring
            base_angle = math.degrees(math.atan2(dy, dx))
            
            # Sesuaikan sudut berdasarkan pergerakan ring
            if abs(hoop_direction) > 5:  # Jika ring bergerak signifikan
                prediction_factor = 15  # Seberapa jauh kita prediksi
                if hoop_direction > 0:  # Ring bergerak ke kanan
                    base_angle -= prediction_factor
                else:  # Ring bergerak ke kiri
                    base_angle += prediction_factor
            
            # Hitung power berdasarkan jarak
            distance = math.sqrt(dx*dx + dy*dy)
            max_distance = math.sqrt(game_screen.shape[1]**2 + game_screen.shape[0]**2)
            base_power = min(0.8, distance / max_distance + 0.3)  # Minimal 0.3, maksimal 0.8
            
            # Sesuaikan power berdasarkan ketinggian ring
            height_factor = 1.0 - (y / game_screen.shape[0])  # 0 = atas, 1 = bawah
            power = base_power * (1 + height_factor * 0.2)  # Tambah power untuk ring yang lebih tinggi
            
            # Tambah sedikit random untuk variasi (lebih kecil dari sebelumnya)
            angle = base_angle + random.uniform(-2, 2)
            power = power + random.uniform(-0.05, 0.05)
            
            # Batasi nilai
            angle = max(20, min(70, angle))
            power = max(0.3, min(0.9, power))
            
            print(f"\nRing bergerak: {'Kanan' if hoop_direction > 0 else 'Kiri' if hoop_direction < 0 else 'Diam'}")
            print(f"Menembak dengan sudut {angle:.1f}° dan power {power:.2f}")
            
            return (angle, power)
            
        except Exception as e:
            print(f"Error menghitung tembakan: {e}")
            return (45, 0.6)  # Default values 