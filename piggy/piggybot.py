from pyautogui import *
import pygetwindow as gw
import pyautogui
import time
import keyboard
import random
from pynput.mouse import Button, Controller
from ai_piggy_bank import HoopTracker, get_hoop_position

mouse = Controller()
time.sleep(0.5)

# Initialize tracker
tracker = HoopTracker()

# Basic color codes for messages
putih = '\033[1;97m'
merah = '\033[1;91m'
hijau = '\033[1;92m'
kuning = '\033[1m\033[93m'
biru = '\033[1;94m'
reset = '\033[0m'

window_name = "Telegram"  # Changed window name
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
    
    # Take a test screenshot to verify capture area
    try:
        test_screenshot = pyautogui.screenshot(region=window_rect)
        print(f"{hijau}Successfully captured screenshot of size: {test_screenshot.size}{reset}")
    except Exception as e:
        print(f"{merah}Error capturing screenshot: {e}{reset}")
        exit()
    
    print(f"{hijau}Game window found! Starting bot...{reset}")
    print(f"{hijau}Bot working... {putih}Press {kuning}'K'{putih} to pause.{reset}")
    print(f"{putih}Press {kuning}'S'{putih} to stop the bot.{reset}")
    
    def swipe_up(start_x, start_y, distance=200):
        # Quick movement for match mode
        if shot_delay == 0.2:  # If in match mode
            hoop_pos = get_hoop_position(window_rect)
            if hoop_pos:
                target_x, target_y = hoop_pos
            else:
                target_x, target_y = start_x, start_y - distance
                
            mouse.position = (start_x, start_y)
            time.sleep(0.02)
            mouse.press(Button.left)
            time.sleep(0.02)
            mouse.position = (target_x, target_y)
            time.sleep(0.02)
            mouse.release(Button.left)
            return

        # Slower, more controlled movement for daily mode
        mouse.position = (start_x, start_y)
        time.sleep(0.05)
        mouse.press(Button.left)
        time.sleep(0.1)
        for i in range(0, distance, 20):
            mouse.position = (start_x, start_y - i)
            time.sleep(0.01)
        mouse.position = (start_x, start_y - distance)
        time.sleep(0.05)
        mouse.release(Button.left)

    # Calculate fixed ball position once
    ball_x = window_rect[0] + (window_rect[2] // 2)
    ball_y = window_rect[1] + (window_rect[3] - 200)
    print(f"{hijau}Ball position calibrated at: ({ball_x}, {ball_y}){reset}")
    
    # Game mode selection
    print(f"\n{putih}Select Game Mode:")
    print(f"{kuning}1. Daily Mode {putih}(1 shot/sec)")
    print(f"{kuning}2. Match Mode {putih}(5+ shots/sec)")
    print(f"{kuning}3. Testing Mode {putih}(Hoop tracking only)")
    mode = input(f"{putih}Enter mode (1 or 2 or 3): {reset}")
    
    # Set delay based on mode
    if mode == "1":
        shot_delay = 1.0
        mode_name = "Daily Mode"
    elif mode == "2":
        shot_delay = 0.2
        mode_name = "Match Mode"
    else:
        shot_delay = 0.1
        mode_name = "Testing Mode"
    print(f"{hijau}Starting in {mode_name}{reset}")
    
    print(f"\n{putih}Controls:")
    print(f"{kuning}K {putih}- Pause/Resume")
    print(f"{kuning}S {putih}- Stop")
    print(f"{kuning}M {putih}- Switch Mode")
    print(f"{kuning}R {putih}- Restart/Choose Mode{reset}\n")

    paused = False
    running = True

    while running:
        if keyboard.is_pressed('K'):
            paused = not paused
            if paused:
                print(f"{biru}Bot paused... Press 'K' to continue{reset}")
            else:
                print(f'{biru}Bot continuing in {mode_name}...{reset}')
            time.sleep(0.2)

        if keyboard.is_pressed('S'):
            print(f"{merah}Stopping bot...{reset}")
            running = False
            break
            
        if keyboard.is_pressed('R'):
            print(f"{hijau}Restarting and returning to mode selection...{reset}")
            time.sleep(0.2)
            # Re-display mode selection menu
            print(f"\n{putih}Select Game Mode:")
            print(f"{kuning}1. Daily Mode {putih}(1 shot/sec)")
            print(f"{kuning}2. Match Mode {putih}(5+ shots/sec)")
            print(f"{kuning}3. Testing Mode {putih}(Hoop tracking only)")
            mode = input(f"{putih}Enter mode (1 or 2 or 3): {reset}")
            
            # Reset mode settings
            if mode == "1":
                shot_delay = 1.0
                mode_name = "Daily Mode"
            elif mode == "2":
                shot_delay = 0.2
                mode_name = "Match Mode"
            else:
                shot_delay = 0.1
                mode_name = "Testing Mode"
            print(f"{hijau}Starting in {mode_name}{reset}")
            continue

        if keyboard.is_pressed('M'):
            # Switch modes
            shot_delay = 1.0 if shot_delay == 0.2 else 0.2
            mode_name = "Daily Mode" if shot_delay == 1.0 else "Match Mode"
            print(f"{hijau}Switched to {mode_name}{reset}")
            time.sleep(0.2)

        if paused:
            continue

        try:
            if mode == "3":  # Testing mode
                hoop_pos = get_hoop_position(window_rect)
                if hoop_pos:
                    mouse.position = hoop_pos
                time.sleep(shot_delay)
            else:
                # Perform shooting action
                swipe_up(ball_x, ball_y)
                if shot_delay == 0.2:  # Match mode
                    time.sleep(0.02)
                else:  # Daily mode
                    time.sleep(1.0)
                        
        except Exception as e:
            print(f"{merah}Error: {e}{reset}")
            continue
