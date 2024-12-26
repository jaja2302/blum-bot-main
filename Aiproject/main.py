from window_detector import WindowDetector
from screen_capture import ScreenCapture
from game_detector import GameDetector
from keyboard_controller import KeyboardController
import time

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
            maintenance_count = 0
            while not keyboard_ctrl.is_stopped():
                if keyboard_ctrl.is_game_paused():
                    time.sleep(0.1)
                    continue
                
                screenshot = screen_capture.capture_window(window_info)
                if screenshot is not None:
                    result = game_detector.detect_game_elements(screenshot)
                    
                    if result:
                        if result['status'] == 'maintenance':
                            maintenance_count += 1
                            if maintenance_count == 1:  # Hanya print sekali
                                print("\nGame sedang maintenance!")
                                print("Tekan 'S' atau 'ESC' untuk stop")
                                print("Tekan 'P' untuk pause")
                            time.sleep(5)  # Tunggu lebih lama saat maintenance
                        else:
                            if maintenance_count > 0:  # Reset counter jika game aktif
                                print("\nGame sudah aktif kembali!")
                                maintenance_count = 0
                            
                            if result['status'] == 'active':
                                print(f"Ring terdeteksi di: {result['hoop_position']}")
                                print(f"Bola siap di posisi: {result['ball_position']}")
                            
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\nProgram dihentikan!")
            
    else:
        print("Window Telegram tidak ditemukan!")

if __name__ == "__main__":
    main()
