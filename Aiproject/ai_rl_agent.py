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
        self.shot_cooldown = 0.1
        self.velocity_history = deque(maxlen=5)  # Track last 5 velocities
        
    def get_action(self, game_screen, hoop_pos):
        """Tentukan parameter tembakan dengan prediksi pergerakan ring"""
        try:
            x, y = hoop_pos
            current_time = time.time()
            
            # Definisikan posisi bola (di tengah bawah screen)
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - 200
            
            # Kalkulasi velocity dan prediksi posisi
            velocity_x = 0
            if self.last_pos and self.last_time:
                dt = current_time - self.last_time
                if dt > 0:
                    velocity_x = (x - self.last_pos[0]) / dt
                    self.velocity_history.append(velocity_x)
                    
                    # Average velocity dari beberapa sample terakhir
                    avg_velocity = sum(self.velocity_history) / len(self.velocity_history)
                    
                    # Estimasi waktu bola mencapai ring (dalam detik)
                    distance = math.sqrt((x - ball_x)**2 + (y - ball_y)**2)
                    time_to_target = distance / 800  # Asumsi kecepatan bola ~800 pixel/s
                    
                    # Prediksi posisi ring saat bola sampai
                    predicted_x = x + (avg_velocity * time_to_target)
                    predicted_y = y  # Asumsi pergerakan horizontal
                    
                    # Log movement info
                    if current_time - self.last_log_time >= self.log_interval:
                        movement = "DIAM"
                        speed_category = "DIAM"
                        if abs(avg_velocity) > self.movement_threshold:
                            movement = "KANAN" if avg_velocity > 0 else "KIRI"
                            if abs(avg_velocity) > 120:
                                speed_category = "CEPAT"
                            elif abs(avg_velocity) > 60:
                                speed_category = "SEDANG"
                            else:
                                speed_category = "LAMBAT"
                                
                        print(f"Ring: ({x}, {y}) | {movement} | {speed_category} | "
                              f"v={abs(avg_velocity):.1f} px/s | predict=({int(predicted_x)}, {y})")
                        self.last_log_time = current_time
                    
                    # Gunakan posisi prediksi untuk kalkulasi tembakan
                    dx = predicted_x - ball_x
                    dy = ball_y - predicted_y
                    
                else:
                    dx = x - ball_x
                    dy = ball_y - y
            else:
                dx = x - ball_x
                dy = ball_y - y
            
            # Update tracking
            self.last_pos = hoop_pos
            self.last_time = current_time
            
            # Kalkulasi sudut dan power
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.degrees(math.atan2(dy, dx))
            
            # Adjust power based on distance and movement
            base_power = distance / 400
            power = min(0.8, max(0.4, base_power))
            
            # Add compensation for extreme angles
            if abs(angle) > 60:
                power *= 1.1
            
            # Skip shot if prediction uncertainty is high
            if len(self.velocity_history) >= 3:
                velocity_std = np.std(list(self.velocity_history))
                if velocity_std > 50:  # High variance in velocity
                    return None
            
            return (angle, power)
            
        except Exception as e:
            print(f"Error menghitung tembakan: {e}")
            return None 
            return (45, 0.6) 