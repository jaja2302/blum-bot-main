from play import MatchMoneyBot
import keyboard
import time

# Color codes for console messages
PUTIH = '\033[1;97m'
MERAH = '\033[1;91m'
HIJAU = '\033[1;92m'
KUNING = '\033[1m\033[93m'
BIRU = '\033[1;94m'
RESET = '\033[0m'

def main():
    print(f"{PUTIH}Starting Match Money Bot...{RESET}")
    bot = MatchMoneyBot()
    
    if not bot.find_window():
        print(f"{MERAH}Telegram window not found! Please make sure:")
        print("1. Telegram Desktop is open")
        print("2. Match Money game window is visible{RESET}")
        return

    print(f"{HIJAU}Window found! Bot initialized.")
    print(f"{PUTIH}Controls:")
    print(f"Press {KUNING}'P'{PUTIH} to start new game")
    print(f"Press {KUNING}'K'{PUTIH} to pause/resume")
    print(f"Press {KUNING}'D'{PUTIH} to show debug window")
    print(f"Press {KUNING}'S'{PUTIH} to stop{RESET}")

    bot.start()
    
    while True:
        if keyboard.is_pressed('S'):
            print(f"{MERAH}Stopping bot...{RESET}")
            bot.stop()
            break
            
        if keyboard.is_pressed('K'):
            bot.toggle_pause()
            time.sleep(0.2)
            
        if keyboard.is_pressed('P'):
            bot.play_game()
            time.sleep(0.2)
            
        if keyboard.is_pressed('D'):
            bot.show_debug_window()
            time.sleep(0.2)
            
        time.sleep(0.1)

if __name__ == "__main__":
    main()
