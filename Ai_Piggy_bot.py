import json
import numpy as np
from pathlib import Path

class HoopPredictor:
    def __init__(self):
        self.movement_patterns = None
        self.average_speeds = {
            'left_to_right': 0,
            'right_to_left': 0
        }
        self.common_positions = []
        self.pause_points = []
        
    def load_training_data(self, json_file='hoop_patterns.json'):
        print("Loading trained patterns...")
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        # Process and learn from the training data
        lr_speeds = [m['speed'] for m in data['left_to_right']]
        rl_speeds = [m['speed'] for m in data['right_to_left']]
        
        self.average_speeds['left_to_right'] = np.mean(lr_speeds) if lr_speeds else 0
        self.average_speeds['right_to_left'] = np.mean(rl_speeds) if rl_speeds else 0
        
        # Learn common positions and patterns
        self.common_positions = [p['x'] for p in data['positions']]
        self.pause_points = [p['position'] for p in data['center_pause']]
        
        print("Training data loaded!")
        print(f"Average L->R speed: {self.average_speeds['left_to_right']:.2f}")
        print(f"Average R->L speed: {self.average_speeds['right_to_left']:.2f}")
        
    def predict_next_position(self, current_x, current_direction):
        """Instantly predict next hoop position based on training"""
        if current_direction == 'left_to_right':
            predicted_x = current_x + self.average_speeds['left_to_right']
        else:
            predicted_x = current_x - self.average_speeds['right_to_left']
            
        return int(predicted_x)
    
    def is_good_shot_position(self, x_position):
        """Check if current position is good for shooting"""
        # Check if position is near common pause points
        for pause_x in self.pause_points:
            if abs(x_position - pause_x) < 10:
                return True
        return False

# Example bot using the predictor
class BasketballBot:
    def __init__(self):
        self.predictor = HoopPredictor()
        self.predictor.load_training_data()
        
    def play_game(self, current_hoop_x):
        # Instantly predict next position
        next_x = self.predictor.predict_next_position(
            current_hoop_x, 
            'left_to_right' if current_hoop_x < 600 else 'right_to_left'
        )
        
        # Decide if we should shoot
        should_shoot = self.predictor.is_good_shot_position(current_hoop_x)
        
        return {
            'predicted_position': next_x,
            'shoot': should_shoot
        }

# Usage example
if __name__ == "__main__":
    bot = BasketballBot()
    
    # Example game loop
    current_x = 500  # Current hoop position
    
    # Get instant prediction
    action = bot.play_game(current_x)
    print(f"Current hoop position: {current_x}")
    print(f"Predicted next position: {action['predicted_position']}")
    print(f"Should shoot: {action['shoot']}") 