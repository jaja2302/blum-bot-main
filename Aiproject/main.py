from window_detector import WindowDetector
from screen_capture import ScreenCapture
from game_detector import GameDetector
from keyboard_controller import KeyboardController
import time
import pyautogui
import keyboard

def main():
    detector = WindowDetector()
    screen_capture = ScreenCapture()
    game_detector = GameDetector()
    keyboard_ctrl = KeyboardController()
    
    print("Mencari window Telegram...")
    print("\nKontrol:")
    print("S - Stop program")
    print("P - Pause program")
    print("R - Resume program")
    print("Space - Play game")
    
    window_info = detector.find_window()
    
    if window_info:
        print(f"Window Telegram ditemukan!")
        
        # Aktifkan window
        detector.activate_window(window_info)
        
        try:
            last_hoop_pos = None
            print("\nTekan SPACE untuk memulai game!")
            
            while not keyboard_ctrl.is_stopped():
                if keyboard_ctrl.is_game_paused():
                    time.sleep(0.1)
                    continue
                    
                # Cek tombol space untuk memulai game
                if keyboard.is_pressed('space'):
                    game_detector.start_game()
                    time.sleep(0.5)  # Delay untuk menghindari multiple press
                
                screenshot = screen_capture.capture_window(window_info)
                if screenshot is not None:
                    result = game_detector.detect_game_elements(screenshot)
                    
                    if result and result['status'] == 'active':
                        current_hoop_pos = result['hoop_position']
                        if current_hoop_pos != last_hoop_pos:
                            last_hoop_pos = current_hoop_pos
                            
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nProgram dihentikan!")
            
    else:
        print("Window Telegram tidak ditemukan!")

if __name__ == "__main__":
    main()
