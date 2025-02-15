import math
import time
from pynput.mouse import Button, Controller
from collections import deque

class GameplayController:
    def __init__(self):
        # Mouse controller
        self.mouse = Controller()
        self.BALL_Y_OFFSET = 220  # Jarak bola dari bawah layar
        
        # Mode settings
        self.shot_cooldown_fast = 0.11
        self.shot_cooldown_slow = 0.6
        self.swipe_duration_fast = 0.1
        self.swipe_duration_slow = 0.2
        
        # Default settings
        self.shot_cooldown = self.shot_cooldown_slow
        self.swipe_duration = self.swipe_duration_slow
        self.last_shot_time = 0

    def set_mode(self, fast_mode):
        """Set shooting mode between fast and slow"""
        self.shot_cooldown = self.shot_cooldown_fast if fast_mode else self.shot_cooldown_slow
        self.swipe_duration = self.swipe_duration_fast if fast_mode else self.swipe_duration_slow

    def shoot(self, game_screen, hoop_pos, window_info):
        """Direct swipe from ball to hoop"""
        current_time = time.time()
        if current_time - self.last_shot_time < self.shot_cooldown:
            return False

        try:
            if game_screen is None or hoop_pos is None:
                return False

            # Get ball and hoop positions
            ball_pos = (
                window_info['left'] + window_info['width'] // 2,
                window_info['top'] + window_info['height'] - self.BALL_Y_OFFSET
            )
            
            # Target position (hoop position)
            target_x = window_info['left'] + hoop_pos[0]
            target_y = window_info['top'] + hoop_pos[1]
            
            # Direct swipe to target
            success = self.swipe(ball_pos[0], ball_pos[1], target_x, target_y)
            if success:
                self.last_shot_time = current_time
            return success

        except Exception as e:
            print(f"Error in shoot: {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y):
        """Execute simple straight swipe"""
        try:
            self.mouse.release(Button.left)
            time.sleep(0.01)
            
            # Posisi awal
            self.mouse.position = (start_x, start_y)
            time.sleep(0.02)
            
            # Tekan dan tahan
            self.mouse.press(Button.left)
            time.sleep(0.02)
            
            # Gerakan lurus sederhana dengan 4 steps
            steps = 4
            for i in range(steps):
                progress = i / steps
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress)
                
                self.mouse.position = (current_x, current_y)
                time.sleep(0.02)
            
            # Posisi akhir
            self.mouse.position = (end_x, end_y)
            time.sleep(0.02)
            self.mouse.release(Button.left)
            
            return True
            
        except Exception as e:
            print(f"Swipe error: {e}")
            self.mouse.release(Button.left)
            return False

    def reset_state(self):
        """Reset controller state"""
        self.last_shot_time = 0
        self.mouse.release(Button.left)

    def shoot_straight(self, game_screen, window_info):
        """Menembak lurus ke atas untuk testing"""
        current_time = time.time()
        if current_time - self.last_shot_time < self.shot_cooldown:
            return False

        try:
            ball_pos = (
                window_info['left'] + window_info['width'] // 2,
                window_info['top'] + window_info['height'] - self.BALL_Y_OFFSET
            )
            
            target_y = ball_pos[1] - 300
            
            success = self.swipe(ball_pos[0], ball_pos[1], ball_pos[0], target_y)
            if success:
                self.last_shot_time = current_time
            return success

        except Exception as e:
            print(f"Error in straight shot: {e}")
            return False