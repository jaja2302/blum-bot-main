from pyautogui import *
import pygetwindow as gw
import pyautogui
import time
import keyboard
import random
from pynput.mouse import Button, Controller
from hoop_detector import find_hoop
from ai_piggy_bank import HoopTracker

mouse = Controller()
time.sleep(0.5)

# Basic color codes for messages
putih = '\033[1;97m'
merah = '\033[1;91m'
hijau = '\033[1;92m'
kuning = '\033[1m\033[93m'
biru = '\033[1;94m'
reset = '\033[0m'

window_name = "Telegram"
check = gw.getWindowsWithTitle(window_name)

if not check:
    print(f"{putih} [>] | Window - {window_name} {kuning}not found!{reset}")
    print(f" {merah}Make sure Telegram Desktop is open and the Piggy Bank game window is visible{reset}")
else:
    print(f"{hijau} [>] | Window found - {window_name}")
    
    game_window = check[0]
    game_window.activate()
    time.sleep(1)
    
    # Get and display window dimensions
    window_rect = (
        game_window.left, game_window.top, game_window.width, game_window.height
    )
    print(f"{putih}Window Dimensions:{reset}")
    print(f"{kuning}Position: ({window_rect[0]}, {window_rect[1]}){reset}")
    print(f"{kuning}Size: {window_rect[2]}x{window_rect[3]}{reset}")
    
    # Initialize AI tracker
    tracker = HoopTracker()
    
    print(f"\n{putih}Select Mode:")
    print(f"{kuning}1. Normal Mode")
    print(f"{kuning}2. AI Training Mode")
    print(f"{kuning}3. AI Game Mode{reset}")
    mode = input(f"{putih}Enter mode (1/2/3): {reset}")
    
    paused = False
    running = True
    
    while running:
        if keyboard.is_pressed('K'):
            paused = not paused
            if paused:
                print(f"{biru}Bot paused... Press 'K' to continue{reset}")
            else:
                print(f'{biru}Bot continuing...{reset}')
            time.sleep(0.2)

        if keyboard.is_pressed('S'):
            print(f"{merah}Stopping bot...{reset}")
            running = False
            break

        if paused:
            continue

        try:
            if mode == "1":  # Normal Mode
                # Your original shooting logic here
                pass
                
            elif mode == "2":  # AI Training Mode
                hoop_pos = find_hoop(window_rect)
                if hoop_pos:
                    # Move to hoop position
                    mouse.position = hoop_pos
                    # Store position for training
                    tracker.update_history(hoop_pos, time.time())
                time.sleep(0.01)
                
            elif mode == "3":  # AI Game Mode
                hoop_pos = find_hoop(window_rect)
                if hoop_pos:
                    # Get predicted position
                    predicted_pos = tracker.predict_next_position(hoop_pos)
                    # Move to predicted position
                    mouse.position = predicted_pos
                    # Optional: Add shooting logic here
                time.sleep(0.01)
                
        except Exception as e:
            print(f"{merah}Error: {e}{reset}")
            continue
