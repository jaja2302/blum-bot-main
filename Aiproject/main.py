from window_detector import WindowDetector
from screen_capture import ScreenCapture
from game_detector import GameDetector
from keyboard_controller import KeyboardController
from ai_ball_controller import BallController
from ai_rl_agent import RLAgent
import time
import keyboard

def main():
    detector = WindowDetector()
    screen_capture = ScreenCapture()
    game_detector = GameDetector()
    keyboard_ctrl = KeyboardController()
    ball_controller = BallController()
    ai_agent = RLAgent()
    
    print("Mencari window Telegram...")
    print("\nKontrol:")
    print("S - Stop program")
    print("P - Pause program")
    print("R - Resume program")
    print("Space - Play game")
    
    window_info = detector.find_window()
    
    if window_info:
        print(f"Window Telegram ditemukan!")
        detector.activate_window(window_info)
        
        # Posisi bola tetap (di tengah bawah window)
        ball_pos = (
            window_info['left'] + (window_info['width'] // 2),  # x tengah
            window_info['top'] + window_info['height'] - 200    # y bawah
        )
        print(f"\nPosisi bola: ({ball_pos[0]}, {ball_pos[1]})")
        
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
                        hoop_pos = result['hoop_position']
                        action = ai_agent.get_action(screenshot, hoop_pos)
                        
                        if action:  # Jika AI memutuskan untuk menembak
                            print(f"\nMenembak ke ring di posisi {hoop_pos}")
                            ball_controller.execute_action(action, ball_pos)
                            
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nProgram dihentikan!")
            
    else:
        print("Window Telegram tidak ditemukan!")

if __name__ == "__main__":
    main()
