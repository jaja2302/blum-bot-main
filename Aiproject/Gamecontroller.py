import math
import time
from pynput.mouse import Button, Controller
from collections import deque

class GameplayController:
    def __init__(self):
        # Mouse controller
        self.mouse = Controller()
        
        # Game parameters (disesuaikan dengan window Telegram)
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 600
        self.HOOP_Y_MIN = 210    # Batas atas dari log
        self.HOOP_Y_MAX = 335    # Batas bawah dari log
        self.BALL_Y_OFFSET = 220
        
        # Shot parameters
        self.POWER_BASE = 290    # Sedikit dikurangi untuk kontrol lebih baik
        self.MIN_POWER = 0.70    # Minimum power dinaikkan
        self.MAX_POWER = 0.92    # Maximum power diturunkan
        
        # Movement thresholds (disesuaikan dengan karakteristik pergerakan)
        self.MAX_HOOP_SPEED = 6.0  # Dari analisis log
        self.DIRECTION_CHANGE_THRESHOLD = 0.8
        
        # Prediction parameters - disesuaikan untuk prediksi lebih agresif
        self.PREDICTION_BASE_TIME = 0.12  # Ditingkatkan dari 0.08
        self.PREDICTION_SPEED_FACTOR = 0.03  # Ditingkatkan dari 0.02
        self.MAX_PREDICTION_TIME = 0.15   # Ditingkatkan dari 0.12
        
        # Mode settings - percepat sedikit cooldown
        self.shot_cooldown_fast = 0.08  # Dipercepat dari 0.09
        self.shot_cooldown_slow = 0.6
        self.swipe_duration_fast = 0.11
        self.swipe_duration_slow = 0.2
        
        # Core settings
        self.base_power = self.POWER_BASE
        self.swipe_duration = self.swipe_duration_slow  # Default to slow mode
        self.shot_cooldown = self.shot_cooldown_slow    # Default to slow mode
        
        # State tracking
        self.last_pos = None
        self.last_time = None
        self.last_shot_time = 0  # Initialize this
        self.last_speed = 0
        self.speed_history = deque(maxlen=3)
        self.direction_history = deque(maxlen=2)

    def shoot(self, game_screen, hoop_pos, window_info):
        current_time = time.time()
        if current_time - self.last_shot_time < self.shot_cooldown:
            return False

        try:
            if game_screen is None or hoop_pos is None:
                return False

            x, y = hoop_pos
            
            # Enhanced prediction for random movement
            predicted_x = x
            if self.last_pos and self.last_time:
                dt = current_time - self.last_time
                if dt > 0:
                    dx = x - self.last_pos[0]
                    current_speed = dx / dt
                    
                    # Track direction changes
                    current_direction = 1 if dx > 0 else -1
                    if self.direction_history and current_direction != self.direction_history[-1]:
                        # Pada perubahan arah, gunakan prediksi minimal
                        predicted_x = x + (current_speed * 0.08)  # Prediksi minimal 80ms
                    else:
                        # Update speed history
                        self.speed_history.append(current_speed)
                        
                        # Weighted average untuk speed (lebih berat ke speed terbaru)
                        weights = [0.5, 0.3, 0.2][:len(self.speed_history)]
                        total_weight = sum(weights)
                        weights = [w/total_weight for w in weights]
                        avg_speed = sum(w * s for w, s in zip(weights, reversed(self.speed_history)))
                        
                        # Aggressive prediction
                        prediction_time = min(
                            self.MAX_PREDICTION_TIME,
                            self.PREDICTION_BASE_TIME + abs(avg_speed) * self.PREDICTION_SPEED_FACTOR
                        )
                        
                        predicted_x = x + (avg_speed * prediction_time)
                        
                        # Increased prediction limits
                        max_prediction = 15 if abs(avg_speed) < 3 else 12  # Ditingkatkan dari 12/8
                        if abs(predicted_x - x) > max_prediction:
                            predicted_x = x + (max_prediction * (1 if avg_speed > 0 else -1))
                        
                        # Additional speed-based offset
                        if abs(avg_speed) > 2:
                            extra_offset = min(abs(avg_speed), 4)  # Max 4 pixel extra
                            predicted_x += extra_offset * (1 if avg_speed > 0 else -1)
                    
                    self.direction_history.append(current_direction)
                    
                    # Boundary check
                    predicted_x = max(100, min(predicted_x, self.SCREEN_WIDTH - 100))
                    
                    self.last_speed = current_speed

            self.last_pos = (x, y)
            self.last_time = current_time
            
            # Shot calculations
            ball_x = game_screen.shape[1] // 2
            ball_y = game_screen.shape[0] - self.BALL_Y_OFFSET
            
            dx = predicted_x - ball_x
            dy = ball_y - y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Angle calculation with height compensation
            base_angle = math.degrees(math.atan2(dy, dx))
            height_factor = (y - self.HOOP_Y_MIN) / (self.HOOP_Y_MAX - self.HOOP_Y_MIN)
            
            # Dynamic angle adjustments
            angle = base_angle
            if distance > 300:
                angle += 2.8 + (height_factor * 0.8)
            elif distance > 250:
                angle += 2.2 + (height_factor * 0.6)
            elif distance < 200:
                angle -= 1.5 + (height_factor * 0.4)
            
            # Power calculation with height consideration
            power_factor = distance / (self.SCREEN_HEIGHT * 0.55)
            power = min(self.MAX_POWER, max(self.MIN_POWER, power_factor))
            
            # Height-based power adjustment
            power *= (1 + (height_factor - 0.5) * 0.1)
            
            # Execute shot
            ball_pos = (
                window_info['left'] + window_info['width'] // 2,
                window_info['top'] + window_info['height'] - self.BALL_Y_OFFSET
            )
            
            shot_distance = power * self.base_power
            target_x = ball_pos[0] + shot_distance * math.cos(math.radians(angle))
            target_y = ball_pos[1] - shot_distance * math.sin(math.radians(angle))
            
            success = self.swipe(ball_pos[0], ball_pos[1], target_x, target_y)
            if success:
                self.last_shot_time = current_time
            return success

        except Exception as e:
            print(f"Error in shoot calculation: {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y):
        """Execute balanced swipe motion"""
        try:
            self.mouse.release(Button.left)
            time.sleep(0.02)  # Sedikit lebih lama
            
            self.mouse.position = (start_x, start_y)
            time.sleep(0.02)
            
            self.mouse.press(Button.left)
            
            # Moderate steps for balance
            steps = 9  # Tambah 1 step
            
            # Add slight curve for better lift
            curve_height = 0.9  # Sedikit lebih tinggi
            
            for i in range(steps):
                progress = i / steps
                # Smooth curve untuk mengangkat bola
                curve = math.sin(progress * math.pi) * curve_height
                
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress - curve)
                
                self.mouse.position = (current_x, current_y)
                time.sleep(self.swipe_duration / steps)
            
            self.mouse.position = (end_x, end_y)
            time.sleep(0.01)  # Tambah sedikit delay
            self.mouse.release(Button.left)
            
            time.sleep(0.02)
            self.mouse.position = (start_x, start_y)
            
            return True
            
        except Exception as e:
            print(f"Swipe error: {e}")
            self.mouse.release(Button.left)
            return False

    def set_mode(self, fast_mode):
        """Set shooting mode between fast and slow"""
        self.shot_cooldown = self.shot_cooldown_fast if fast_mode else self.shot_cooldown_slow
        self.swipe_duration = self.swipe_duration_fast if fast_mode else self.swipe_duration_slow

    def reset_state(self):
        """Reset controller state"""
        self.last_pos = None
        self.last_time = None
        self.last_shot_time = 0
        self.last_speed = 0
        self.speed_history.clear()
        self.direction_history.clear()
        self.mouse.release(Button.left)