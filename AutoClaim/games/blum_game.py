from games.base_game import BaseGame
import pyautogui
import time
from config import COLORS

class BlumGame(BaseGame):
    name = "Blum Clicker"
    description = "Auto clicker for Blum game"
    assets_path = "assets/blum/"
    
    def __init__(self, window):
        super().__init__(window)
        self.play_counter = 0
        
    def run(self):
        print(f"\n{COLORS['GREEN']}Starting {self.name}...")
        print(f"{COLORS['WHITE']}Controls:")
        print(f"- Press {COLORS['YELLOW']}K{COLORS['WHITE']} to pause/resume")
        print(f"- Press {COLORS['YELLOW']}S{COLORS['WHITE']} to stop")
        print(f"- Press {COLORS['YELLOW']}B{COLORS['WHITE']} to return to main menu{COLORS['RESET']}\n")
        
        game_start_time = time.time()
        last_scan_time = time.time()

        while self.running:
            if self.handle_hotkeys():  # Returns True if 'B' was pressed
                break
                
            if self.paused:
                time.sleep(0.1)
                continue

            # Your existing Blum game logic here
            # ...

        print(f"{COLORS['GREEN']}Games played: {self.play_counter}{COLORS['RESET']}") 