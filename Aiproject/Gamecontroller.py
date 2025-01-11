import numpy as np
import math
import time
from pynput.mouse import Button, Controller
import os
import json

class GameplayController:
    def __init__(self):
        # Load settings
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'partial/setting_controller.json')
            with open(json_path, 'r') as f:
                self.setting_config = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            raise ValueError("Settings could not be loaded")

        swipe_config = self.setting_config['swipe_agent']
        
        # Basic settings
        self.mouse = Controller()
        self.base_power = swipe_config['base_power']
        self.shot_cooldown = 0.12
        self.swipe_duration = 0.11
        self.last_shot_time = 0
        
        # Movement tracking
        self.history_size = 6
        self.position_buffer = np.zeros(self.history_size)
        self.time_buffer = np.zeros(self.history_size)
        self.velocity_buffer = np.zeros(self.history_size - 1)
        self.buffer_index = 0
        self.buffer_filled = False
        
        # Shot parameters
        self.shot_params = {
            'close': {'power': 0.92, 'angle_adj': 1.0},
            'medium': {'power': 0.95, 'angle_adj': 1.5},
            'far': {'power': 0.98, 'angle_adj': 2.0}
        }
        
        # Tambahkan logging system
        self.shot_logger = {
            'shots': [],
            'current_game': None
        }
        
        # Create log directory if not exists
        self.log_dir = 'asset/shot_logs'
        os.makedirs(self.log_dir, exist_ok=True)

    def log_shot(self, game_screen, hoop_pos, shot_params, success=None):
        """Log data tembakan"""
        try:
            current_time = time.time()
            screen_center = game_screen.shape[1] // 2
            
            shot_data = {
                'timestamp': current_time,
                'hoop_position': {
                    'x': hoop_pos[0],
                    'y': hoop_pos[1],
                    'distance_from_center': hoop_pos[0] - screen_center
                },
                'shot_params': {
                    'angle': shot_params[0],
                    'power': shot_params[1]
                },
                'movement_data': {
                    'velocity': None,
                    'direction': None
                },
                'success': success
            }
            
            # Calculate velocity if we have enough history
            if self.buffer_filled:
                recent_velocities = self.velocity_buffer[max(0, self.buffer_index-3):self.buffer_index]
                if len(recent_velocities) > 0:
                    avg_velocity = np.mean(recent_velocities)
                    shot_data['movement_data']['velocity'] = float(avg_velocity)
                    shot_data['movement_data']['direction'] = 'right' if avg_velocity > 5 else 'left' if avg_velocity < -5 else 'center'
            
            self.shot_logger['shots'].append(shot_data)
            
        except Exception as e:
            print(f"Error logging shot: {e}")

    def save_game_log(self, game_id=None):
        """Save logged data to file"""
        if not self.shot_logger['shots']:
            return
            
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            game_id = game_id or f"game_{timestamp}"
            
            filename = os.path.join(self.log_dir, f"shots_{game_id}.json")
            
            log_data = {
                'game_id': game_id,
                'timestamp': timestamp,
                'total_shots': len(self.shot_logger['shots']),
                'shots': self.shot_logger['shots']
            }
            
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2)
                
            print(f"Shot log saved to {filename}")
            
            # Reset shot logger
            self.shot_logger['shots'] = []
            
        except Exception as e:
            print(f"Error saving shot log: {e}")

    def shoot(self, game_screen, hoop_pos):
        """Calculate shot angle and power with logging"""
        shot_params = super().shoot(game_screen, hoop_pos)
        if shot_params:
            self.log_shot(game_screen, hoop_pos, shot_params)
        return shot_params

    def swipe(self, start_pos, angle, power):
        """Execute swipe movement"""
        try:
            current_time = time.time()
            if current_time - self.last_shot_time < self.shot_cooldown:
                return False
            
            start_x, start_y = start_pos
            distance = power * self.base_power
            
            # Calculate target position
            target_x = start_x + distance * math.cos(math.radians(angle))
            target_y = start_y - distance * math.sin(math.radians(angle))
            
            # Execute swipe
            self.mouse.release(Button.left)
            time.sleep(0.02)
            
            self.mouse.position = (start_x, start_y)
            time.sleep(0.02)
            
            self.mouse.press(Button.left)
            
            # Smooth movement
            steps = 10
            x_steps = np.linspace(start_x, target_x, steps)
            y_steps = np.linspace(start_y, target_y, steps)
            step_delay = self.swipe_duration / steps
            
            for i in range(steps):
                self.mouse.position = (int(x_steps[i]), int(y_steps[i]))
                time.sleep(step_delay)
            
            self.mouse.release(Button.left)
            time.sleep(0.02)
            self.mouse.position = (start_x, start_y)
            
            self.last_shot_time = current_time
            return True
            
        except Exception as e:
            print(f"Swipe error: {e}")
            self.mouse.release(Button.left)
            return False

    def reset_state(self):
        """Reset controller state"""
        self.position_buffer.fill(0)
        self.time_buffer.fill(0)
        self.velocity_buffer.fill(0)
        self.buffer_index = 0
        self.buffer_filled = False
        self.last_shot_time = 0
        self.mouse.release(Button.left)