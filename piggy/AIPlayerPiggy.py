import numpy as np
import json
import time
from modules.hoop_detector import HoopDetector
from modules.score_detector import ScoreDetector
from modules.data_manager import DataManager
from modules.window_manager import WindowManager
from modules.Gameplay import BallDetector

class AIPlayerPiggy:
    def __init__(self):
        self.ball_detector = BallDetector()
        self.hoop_detector = HoopDetector()
        self.score_detector = ScoreDetector()
        self.data_manager = DataManager()
        self.window_manager = WindowManager()
        
        # Load game stats
        try:
            with open('modules/game_stats.json', 'r') as f:
                self.game_stats = json.load(f)
        except:
            self.game_stats = {
                'games_played': 0,
                'high_score': 0,
                'total_shots': 0,
                'successful_shots': 0,
                'best_positions': []
            }

    def calculate_weighted_position(self, target_pos):
        """Calculate weighted position with improved learning"""
        weights = []
        positions = []
        
        # Dynamic learning rate based on success rate
        success_rate = self.game_stats['successful_shots'] / max(1, self.game_stats['total_shots'])
        learning_rate = max(0.1, 1.0 - success_rate)
        
        # Get recent successful positions
        recent_positions = self.game_stats['best_positions'][-50:]
        
        for pos in recent_positions:
            distance = ((pos[0]-target_pos[0])**2 + (pos[1]-target_pos[1])**2)**0.5
            
            # Adaptive distance threshold based on success rate
            distance_threshold = 60 if success_rate > 0.3 else 100
            
            if distance < distance_threshold:
                # Weight calculation considering recency and success
                recency_weight = 1.0
                distance_weight = 1 / (distance + 1)
                movement_weight = self.calculate_movement_weight(pos, target_pos)
                
                total_weight = (recency_weight + distance_weight + movement_weight) / 3
                weights.append(total_weight)
                positions.append(pos)
        
        if not weights:
            # Exploration mode - try new positions
            return (
                target_pos[0] + np.random.normal(0, 20 * learning_rate),
                target_pos[1] + np.random.normal(0, 10 * learning_rate)
            )
        
        # Calculate weighted average position
        weights = np.array(weights) / sum(weights)
        weighted_x = sum(w * p[0] for w, p in zip(weights, positions))
        weighted_y = sum(w * p[1] for w, p in zip(weights, positions))
        
        # Add adaptive noise for exploration
        noise_x = np.random.normal(0, 10 * learning_rate)
        noise_y = np.random.normal(0, 5 * learning_rate)
        
        return (weighted_x + noise_x, weighted_y + noise_y)

    def calculate_movement_weight(self, pos, target_pos):
        """Calculate weight based on hoop movement pattern"""
        try:
            with open('modules/movement_log.json', 'r') as f:
                movement_data = json.load(f)
                
            similar_movements = []
            for movement in movement_data.get('movements', []):
                if abs(movement['position'][0] - target_pos[0]) < 30:
                    similar_movements.append(movement)
            
            if similar_movements:
                avg_speed = sum(m['speed'] for m in similar_movements) / len(similar_movements)
                avg_direction = sum(1 if m['velocity'][0] > 0 else -1 for m in similar_movements) / len(similar_movements)
                return 1.0 + (avg_speed / 100) * abs(avg_direction)
                
        except Exception as e:
            print(f"Error analyzing movement: {e}")
        
        return 1.0

    def update_game_stats(self, success, hoop_pos):
        """Update game statistics"""
        self.game_stats['total_shots'] += 1
        if success:
            self.game_stats['successful_shots'] += 1
            self.game_stats['best_positions'].append([int(hoop_pos[0]), int(hoop_pos[1])])
        
        # Save updated stats
        with open('modules/game_stats.json', 'w') as f:
            json.dump(self.game_stats, f, indent=4)

if __name__ == "__main__":
    try:
        print("Starting initialization...")
        ai_player = AIPlayerPiggy()
        print("AI Player initialized")
        
        print("\n=== AI Hoop Learning System ===")
        print("Please open the Telegram Piggy Bank game\n")
        print("Controls:")
        print("SPACE - Pause/Resume")
        print("Q     - Quit Bot")
        print("E     - End Current Game\n")
        
        input("Press Enter when ready...")
        print("Starting game loop...")
        
        # Main game loop
        while True:
            try:
                # Get game window
                window_rect = ai_player.window_manager.get_game_window()
                if not window_rect:
                    print("Please open Telegram window")
                    time.sleep(2)
                    continue

                # Get current positions
                ball_pos = ai_player.ball_detector.calibrate_position()
                if not ball_pos:
                    print("Could not detect ball position")
                    time.sleep(0.5)
                    continue
                
                # Get target position using weighted calculation
                target_pos = ai_player.calculate_weighted_position(ball_pos)
                
                # Execute shot
                success = ai_player.ball_detector.execute_shot(window_rect, target_pos)
                
                if success:
                    # Update stats and learning
                    ai_player.update_game_stats(True, target_pos)
                    ai_player.ball_detector.update_learning({
                        'ball_pos': ball_pos,
                        'target_pos': target_pos,
                        'timestamp': time.time()
                    })
                
                time.sleep(0.5)  # Add small delay between shots
                
            except KeyboardInterrupt:
                print("\nStopping game loop...")
                break
            except Exception as e:
                print(f"Error in game loop: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc() 