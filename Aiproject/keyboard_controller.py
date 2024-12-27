import keyboard
import time
import sys
import pyautogui

class KeyboardController:
    def __init__(self):
        self.is_running = True
        self.is_paused = False
        self.fast_mode = True  # Default mode cepat
        
        # Set up keyboard event handlers
        keyboard.on_press_key('s', lambda _: self.stop_program())
        keyboard.on_press_key('esc', lambda _: self.stop_program())
        keyboard.on_press_key('p', lambda _: self.toggle_pause())
        keyboard.on_press_key('r', lambda _: self.toggle_pause())
        keyboard.on_press_key('m', lambda _: self.toggle_mode())  # Tambah handler mode

    def stop_program(self):
        """Immediately stop the program"""
        print("\nMenghentikan program...")
        self.is_running = False
        sys.exit(0)  # Force exit

    def toggle_pause(self):
        """Toggle pause state"""
        self.is_paused = not self.is_paused
        print("\nProgram di-pause..." if self.is_paused else "\nMelanjutkan program...")

    def is_stopped(self):
        """Check if program should stop"""
        return not self.is_running

    def is_game_paused(self):
        return self.is_paused 

    def press_space(self):
        """Tekan tombol spasi untuk memulai game baru"""
        try:
            keyboard.press_and_release('space')
            time.sleep(0.1)  # Delay kecil setelah menekan spasi
        except Exception as e:
            print(f"Error menekan spasi: {e}") 

    def toggle_mode(self):
        """Toggle between fast and normal mode"""
        self.fast_mode = not self.fast_mode
        mode = "CEPAT" if self.fast_mode else "NORMAL"
        print(f"\nMode diubah ke: {mode}")

    def get_current_mode(self):
        """Return current shooting mode"""
        return self.fast_mode 

    def click_at(self, x, y):
        """Melakukan klik mouse pada posisi x,y"""
        try:
            print(f"\nDebug: Melakukan klik di koordinat ({x}, {y})")
            current_pos = pyautogui.position()  # Simpan posisi mouse sekarang
            
            # Gerakkan mouse, klik, dan kembalikan ke posisi semula
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.click()
            pyautogui.moveTo(current_pos.x, current_pos.y, duration=0.1)
            
            print("Debug: Klik berhasil dilakukan")
        except Exception as e:
            print(f"Debug: Error saat melakukan klik: {e}") 