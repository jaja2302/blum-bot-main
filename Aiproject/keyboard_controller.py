import keyboard
import time
import pyautogui

class KeyboardController:
    def __init__(self):
        self.is_running = True
        self.is_paused = False
        self.fast_mode = True
        self.betting_amount = '1m'
        self.debug_shoot = False
        
        # Set up keyboard handlers
        keyboard.on_press_key('s', lambda _: self.stop_program())
        keyboard.on_press_key('esc', lambda _: self.stop_program())
        keyboard.on_press_key('p', lambda _: self.toggle_pause())
        keyboard.on_press_key('r', lambda _: self.toggle_pause())
        keyboard.on_press_key('m', lambda _: self.toggle_mode())
        keyboard.on_press_key('d', lambda _: self.toggle_debug_shoot())
        
        self.betting_options = {
            '1': '1m',
            '2': '10m',
            '3': '100m'
        }

    def stop_program(self):
        print("\nMenghentikan program...")
        self.is_running = False

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        print("\nProgram di-pause..." if self.is_paused else "\nMelanjutkan program...")

    def is_stopped(self):
        return not self.is_running

    def is_game_paused(self):
        return self.is_paused

    def toggle_mode(self):
        self.fast_mode = not self.fast_mode
        print(f"\nMode diubah ke: {'CEPAT' if self.fast_mode else 'NORMAL'}")

    def get_current_mode(self):
        return self.fast_mode

    def click_at(self, x, y):
        try:
            current_pos = pyautogui.position()
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.click()
            pyautogui.moveTo(current_pos.x, current_pos.y, duration=0.1)
        except Exception as e:
            print(f"Error saat melakukan klik: {e}")

    def get_betting_amount(self):
        return self.betting_amount

    def get_betting_input(self):
        print("\nPilih jumlah betting:")
        print("1 - untuk 1m")
        print("2 - untuk 10m") 
        print("3 - untuk 100m")
        
        while True:
            choice = input("Pilihan anda (1/2/3): ")
            if choice in self.betting_options:
                self.betting_amount = self.betting_options[choice]
                print(f"Betting amount diset ke: {self.betting_amount}")
                return self.betting_amount
            print("Input tidak valid! Pilih 1, 2, atau 3")

    def print_controls(self):
        print("\nKontrol:")
        print("S/ESC - Stop program")
        print("P/R - Pause/Resume program")
        print("M - Ganti mode (NORMAL/CEPAT)")
        print("Space - Play game")

    def toggle_debug_shoot(self):
        self.debug_shoot = not self.debug_shoot
        print("\nMode debug shoot diaktifkan..." if self.debug_shoot else "\nMode debug shoot dimatikan...")

    def is_debug_shoot(self):
        return self.debug_shoot 