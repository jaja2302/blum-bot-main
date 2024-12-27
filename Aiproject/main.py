from window_detector import WindowDetector
from screen_capture import ScreenCapture
from game_detector import GameDetector, GameState
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
    print("M - Ganti mode (NORMAL/CEPAT)")
    print("Space - Play game")
    
    # Perbaikan input betting amount
    print("\nPilih jumlah betting:")
    print("1 - untuk 1m")
    print("2 - untuk 10m")
    print("3 - untuk 100m")
    
    betting_options = {
        '1': '1m',
        '2': '10m',
        '3': '100m'
    }
    
    while True:
        choice = input("Pilihan anda (1/2/3): ")
        if choice in betting_options:
            betting_amount = betting_options[choice]
            keyboard_ctrl.set_betting_amount(betting_amount)
            game_detector.game_stats.set_betting_amount(betting_amount)  # Update game stats
            print(f"Betting amount diset ke: {betting_amount}")
            break
        print("Input tidak valid! Pilih 1, 2, atau 3")
    
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
                ball_controller.set_mode(keyboard_ctrl.get_current_mode())
                
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
                            # print(f"\nMenembak ke ring di posisi {hoop_pos}")
                            ball_controller.execute_action(action, ball_pos)
                    elif result and result['status'] == 'game_over' and result.get('should_claim'):
                        claim_pos = game_detector.get_button_position('claim', window_info)
                        if claim_pos:
                            # print("\nDebug: Clicking claim button")
                            keyboard_ctrl.click_at(claim_pos[0], claim_pos[1])
                            time.sleep(0.5)
                            # Mulai alur post-game dengan mengirim screen_capture
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
    time.sleep(1)
    
    current_state = None
    has_clicked_bet = False
    retry_count = 0
    MAX_RETRIES = 30
    
    while True:
        if retry_count >= MAX_RETRIES:
            print("\nDebug: Melebihi batas percobaan (10x), menghentikan program...")
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
            # Gunakan betting amount yang dipilih
            button_name = f'go_versus_player_{keyboard_ctrl.get_betting_amount()}'
            pos = game_detector.get_button_position(button_name, window_info)
            if pos:
                keyboard_ctrl.click_at(pos[0], pos[1])
                has_clicked_bet = True
                time.sleep(2)
                
        elif state['state'] == GameState.OPPONENT_FOUND:
            pos = game_detector.get_button_position('go_versus_player', window_info)
            if pos:
                keyboard_ctrl.click_at(pos[0], pos[1])
                time.sleep(5)  # Tunggu 2 detik
                # Langsung klik Let's go dengan koordinat yang sudah ada
                pos = game_detector.get_button_position('letsgo_play_the_game', window_info)
                if pos:
                    keyboard_ctrl.click_at(pos[0], pos[1])
                    time.sleep(2)  # Tunggu 3 detik sebelum mulai game
                    game_detector.start_game()
                    return
        
        time.sleep(2)

if __name__ == "__main__":
    main()
