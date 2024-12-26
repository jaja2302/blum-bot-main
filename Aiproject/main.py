from window_detector import WindowDetector
from screen_capture import ScreenCapture
from game_detector import GameDetector
from keyboard_controller import KeyboardController
from ai_ball_controller import BallController
from ai_rl_agent import RLAgent
from score_detector import ScoreDetector
import time
import keyboard

def main():
    detector = WindowDetector()
    screen_capture = ScreenCapture()
    game_detector = GameDetector()
    keyboard_ctrl = KeyboardController()
    ball_controller = BallController()
    ai_agent = RLAgent()
    score_detector = ScoreDetector()
    
    print("Mencari window Telegram...")
    print("\nKontrol:")
    print("S - Stop program")
    print("P - Pause program")
    print("R - Resume program")
    print("Space - Play game")
    
    window_info = detector.find_window()
    
    # Add episode tracking
    episode = 0
    total_reward = 0
    last_shot_time = 0
    shot_cooldown = 1.0  # Time between shots to evaluate result
    
    if window_info:
        print(f"Window Telegram ditemukan!")
        detector.activate_window(window_info)
        
        ball_pos = (
            window_info['left'] + (window_info['width'] // 2),
            window_info['top'] + window_info['height'] - 200
        )
        
        try:
            print("\nTekan SPACE untuk memulai game!")
            
            while not keyboard_ctrl.is_stopped():
                if keyboard_ctrl.is_game_paused():
                    time.sleep(0.01)
                    continue
                    
                if keyboard.is_pressed('space'):
                    game_detector.start_game()
                    time.sleep(0.1)
                
                screenshot = screen_capture.capture_window(window_info)
                if screenshot is not None:
                    result = game_detector.detect_game_elements(screenshot)
                    
                    if result and result['status'] == 'active':
                        current_time = time.time()
                        
                        # Get current state and score
                        state = ai_agent.get_state(screenshot, result['hoop_position'])
                        current_score = score_detector.detect_score(screenshot)
                        
                        if current_time - last_shot_time >= shot_cooldown:
                            action = ai_agent.get_action(screenshot, result['hoop_position'])
                            
                            if action:
                                print(f"\nEpisode {episode} - Menembak ke ring di posisi {result['hoop_position']}")
                                success = ball_controller.execute_action(action, ball_pos)
                                
                                # Wait briefly to see the result
                                time.sleep(0.5)
                                
                                # Get new state and score
                                new_screenshot = screen_capture.capture_window(window_info)
                                new_result = game_detector.detect_game_elements(new_screenshot)
                                new_score = score_detector.detect_score(new_screenshot)
                                
                                if new_result:
                                    if new_result['status'] == 'game_over':
                                        next_state = state
                                        reward = 0
                                        done = True
                                    else:
                                        next_state = ai_agent.get_state(new_screenshot, new_result['hoop_position'])
                                        # Calculate reward based on score difference
                                        reward = 1.0 if new_score > current_score else -0.1
                                        done = False
                                    
                                    print(f"Score: {new_score} (Reward: {reward})")
                                    
                                    # Store experience
                                    ai_agent.remember(state, action, reward, next_state, done)
                                    ai_agent.train()
                                    
                                    total_reward += reward
                                    episode += 1
                                    
                                    if episode % 100 == 0:
                                        ai_agent.update_target_model()
                                        print(f"\nEpisode {episode}")
                                        print(f"Epsilon: {ai_agent.epsilon:.3f}")
                                        print(f"Average Reward: {total_reward/episode:.3f}")
                                
                                last_shot_time = current_time
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nProgram dihentikan!")
            print(f"Total Episodes: {episode}")
            print(f"Final Average Reward: {total_reward/max(1,episode):.3f}")
            
    else:
        print("Window Telegram tidak ditemukan!")

if __name__ == "__main__":
    main()
