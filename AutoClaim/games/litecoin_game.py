from games.base_game import BaseGame
import pyautogui
import time
from config import COLORS

class LitecoinGame(BaseGame):
    name = "Litecoin Clicker"
    description = "Auto claim for Litecoin faucet"
    assets_path = "assets/litecoin/"
    
    def __init__(self, window):
        super().__init__(window)
        self.claim_counter = 0
        
    def run(self):
        print(f"\n{COLORS['GREEN']}Starting {self.name}...")
        print(f"{COLORS['WHITE']}Controls:")
        print(f"- Press {COLORS['YELLOW']}K{COLORS['WHITE']} to pause/resume")
        print(f"- Press {COLORS['YELLOW']}S{COLORS['WHITE']} to stop")
        print(f"- Press {COLORS['YELLOW']}B{COLORS['WHITE']} to return to main menu{COLORS['RESET']}\n")
        
        while self.running:
            if self.handle_hotkeys():  # Returns True if 'B' was pressed
                break
                
            if self.paused:
                time.sleep(0.1)
                continue

            # Implement Litecoin-specific logic here
            # For example:
            if self.find_and_click_button(f"{self.assets_path}claim_button.png"):
                self.claim_counter += 1
                print(f"{COLORS['GREEN']}Claimed {self.claim_counter} times{COLORS['RESET']}")
                time.sleep(3600)  # Wait 1 hour before next claim

        print(f"{COLORS['GREEN']}Total claims: {self.claim_counter}{COLORS['RESET']}") 