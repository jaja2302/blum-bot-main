import pyautogui
import time
import math
import random

class BallController:
    def __init__(self):
        self.base_power = 100  # Kekuatan dasar tembakan
        pyautogui.FAILSAFE = False  # Disable failsafe

    def shoot(self, start_pos, target_pos):
        """Menembak bola ke arah target"""
        try:
            # Hitung angle dan power berdasarkan posisi
            dx = target_pos[0] - start_pos[0]
            dy = target_pos[1] - start_pos[1]
            angle = math.atan2(dy, dx)
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Tambah sedikit random untuk variasi
            power = (distance / self.base_power) * (1 + random.uniform(-0.1, 0.1))
            
            # Eksekusi tembakan
            pyautogui.moveTo(start_pos[0], start_pos[1])
            pyautogui.mouseDown()
            
            # Geser mouse sesuai angle dan power
            end_x = start_pos[0] + (power * math.cos(angle))
            end_y = start_pos[1] + (power * math.sin(angle))
            pyautogui.moveTo(end_x, end_y, duration=0.2)
            
            pyautogui.mouseUp()
            return True
            
        except Exception as e:
            print(f"Error saat menembak: {e}")
            return False 