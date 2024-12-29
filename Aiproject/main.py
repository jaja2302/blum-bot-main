from window_detector import WindowDetector
from screen_capture import ScreenCapture
from game_detector import GameDetector, GameState
from keyboard_controller import KeyboardController
from Gamecontroller import GameplayController
import time
import keyboard

def main():
    detector = WindowDetector()
    screen_capture = ScreenCapture()
    game_detector = GameDetector()
    keyboard_ctrl = KeyboardController()
    gameplay_controller = GameplayController()
    
    print("Mencari window Telegram...")
    keyboard_ctrl.print_controls()
    
    # Get betting amount from user
    betting_amount = keyboard_ctrl.get_betting_input()
    game_detector.game_stats.set_betting_amount(betting_amount)
    
    window_info = detector.find_window()
    
    if window_info:
        print(f"Window Telegram ditemukan!")
        print("Mode awal: CEPAT")
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
                    
                # Update mode tembakan
                gameplay_controller.set_mode(keyboard_ctrl.get_current_mode())
                
                if keyboard.is_pressed('space'):
                    game_detector.start_game()
                    time.sleep(0.1)
                
                screenshot = screen_capture.capture_window(window_info)
                if screenshot is not None:
                    result = game_detector.detect_game_elements(screenshot)
                    
                    if result and result['status'] == 'active':
                        hoop_pos = result['hoop_position']
                        action = gameplay_controller.get_action(screenshot, hoop_pos)
                        
                        if action:  # Jika AI memutuskan untuk menembak
                            # print(f"\nMenembak ke ring di posisi {hoop_pos}")
                            gameplay_controller.execute_action(action, ball_pos)
                    elif result and result['status'] == 'game_over' and result.get('should_claim'):
                        print("\nPermainan selesai! Membersihkan state...")
                        game_detector.stop_game()
                        gameplay_controller.reset_state()
                        
                        claim_pos = game_detector.get_button_position('claim', window_info)
                        if claim_pos:
                            keyboard_ctrl.click_at(claim_pos[0], claim_pos[1])
                            time.sleep(0.5)
                            handle_post_game_flow(game_detector, keyboard_ctrl, window_info, screen_capture)
                        else:
                            print("\nDebug: Posisi tombol claim tidak ditemukan!")
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nProgram dihentikan!")
            
    else:
        print("Window Telegram tidak ditemukan!")

def handle_post_game_flow(game_detector, keyboard_ctrl, window_info, screen_capture):
    """Menangani alur setelah game selesai"""
    print("\nMencari pertandingan baru...")
    time.sleep(1)
    
    current_state = None
    has_clicked_bet = False
    retry_count = 0
    MAX_RETRIES = 30
    
    while True:
        if retry_count >= MAX_RETRIES:
            print("Gagal menemukan pertandingan, menghentikan program...")
            return
            
        screenshot = screen_capture.capture_window(window_info)
        if screenshot is None:
            continue
            
        state = game_detector.detect_game_state(screenshot)
        if not state:
            continue
            
        if current_state != state['state']:
            current_state = state['state']
            retry_count = 0
        else:
            retry_count += 1
            
        if state['state'] == GameState.UNKNOWN and not has_clicked_bet:
            button_name = f'go_versus_player_{keyboard_ctrl.get_betting_amount()}'
            pos = game_detector.get_button_position(button_name, window_info)
            if pos:
                keyboard_ctrl.click_at(pos[0], pos[1])
                has_clicked_bet = True
                print("Memilih jumlah taruhan...")
                time.sleep(2)
                
        elif state['state'] == GameState.OPPONENT_FOUND:
            print("Lawan ditemukan!")
            pos = game_detector.get_button_position('go_versus_player', window_info)
            if pos:
                keyboard_ctrl.click_at(pos[0], pos[1])
                time.sleep(5)
                pos = game_detector.get_button_position('letsgo_play_the_game', window_info)
                if pos:
                    keyboard_ctrl.click_at(pos[0], pos[1])
                    # print("\nGame dimulai!")
                    time.sleep(3)
                    game_detector.start_game()
                    return
        
        time.sleep(2)

if __name__ == "__main__":
    main()
