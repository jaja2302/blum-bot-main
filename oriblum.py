from pyautogui import *
import pygetwindow as gw
import pyautogui
import time
import keyboard
import random
from pynput.mouse import Button, Controller

mouse = Controller()
time.sleep(0.5)

# Basic color codes for messages
putih = '\033[1;97m'
merah = '\033[1;91m'
hijau = '\033[1;92m'
kuning = '\033[1m\033[93m'
biru = '\033[1;94m'
reset = '\033[0m'

window_name = "TelegramDesktop"
check = gw.getWindowsWithTitle(window_name)

if not check:
    print(f"{putih} [>] | Window - {window_name} {kuning}not found!{reset}")
    print(f" {merah}Make sure Telegram Desktop is open and the Blum bot window is visible{reset}")
else:
    print(f"{hijau} [>] | Window found - {window_name}")
    
    telegram_window = check[0]
    telegram_window.activate()  # Activate the Telegram window
    time.sleep(1)  # Wait for window to come to front
    
    # Check for play button first
    window_rect = (
        telegram_window.left, telegram_window.top, telegram_window.width, telegram_window.height
    )
    
    print(f"{putih}Looking for play button...{reset}")
    play_button = None
    try:
        play_button = pyautogui.locateOnScreen('play_button.png', confidence=0.6, region=window_rect)
        if not play_button:
            play_button = pyautogui.locateOnScreen('play_button.png', confidence=0.5, region=window_rect)
    except:
        pass
        
    if not play_button:
        print(f"{merah}Play button not found! Please ensure:")
        print(f"{merah}1. The game window is fully visible")
        print(f"{merah}2. The play_button.png file matches the current button appearance")
        print(f"{merah}3. The window is not covered by other windows{reset}")
        exit()
    else:
        print(f"{hijau}Play button found! Starting bot...{reset}")
        play_x, play_y = pyautogui.center(play_button)
        click(play_x, play_y)
        time.sleep(2)  # Wait a bit after clicking
        print(f"{hijau}Bot working... {putih}Press {kuning}'K'{putih} to pause.{reset}")
        print(f"{putih}Press {kuning}'S'{putih} to stop the bot.{reset}")
    
    paused = False
    play_counter = 0
    click_counter = 0
    running = True
    game_start_time = time.time()
    game_active = True
    last_scan_time = time.time()  # Track scan time properly

    def click(x, y):
        mouse.position = (x, y + random.randint(1, 3))
        mouse.press(Button.left)
        mouse.release(Button.left)

    while running:
        if keyboard.is_pressed('K'):
            paused = not paused
            if paused:
                print(f"{biru} Bot paused... \n{putih}Press {kuning}'K'{putih} to continue{reset}")
            else:
                print(f'{biru} Bot continuing...{reset}')
            time.sleep(0.2)

        if keyboard.is_pressed('S'):
            print(f"{merah}Stopping bot...")
            print(f"{putih}Total games played: {kuning}{play_counter}{reset}")
            running = False
            break

        if paused:
            continue

        window_rect = (
            telegram_window.left, telegram_window.top, telegram_window.width, telegram_window.height
        )

        current_time = time.time()
        # After 35 seconds, look for play button
        if current_time - game_start_time >= 35:
            try:
                play_button = pyautogui.locateOnScreen('play_button.png', confidence=0.7, region=window_rect)
                if play_button:
                    play_counter += 1
                    time.sleep(random.uniform(1, 2))
                    play_x, play_y = pyautogui.center(play_button)
                    click(play_x, play_y)
                    print(f"{hijau}Found and clicked Play button! Starting game #{play_counter}...{reset}")
                    game_start_time = current_time
                    game_active = True
                    time.sleep(2)
            except:
                pass
            continue

        # Auto-clicking logic during active game
        if game_active:
            try:
                current_time = time.time()
                if current_time - last_scan_time >= 0.1:
                    scrn = pyautogui.screenshot(region=window_rect)
                    width, height = scrn.size
                    clicks_this_scan = 0

                    for x in range(0, width, 15):
                        for y in range(0, height, 15):
                            r, g, b = scrn.getpixel((x, y))
                            
                            hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
                            if hex_color in ['#8b8383', '#696666', '#a4a4a4', '#8c8c8c', '#9c9494']:
                                continue
                                
                            if b < 125 and 102 <= r <= 220 and g >= 200:
                                screen_x = window_rect[0] + x
                                screen_y = window_rect[1] + y
                                click(screen_x, screen_y)
                                clicks_this_scan += 1
                                time.sleep(0.01)
                    
                    last_scan_time = current_time
                    
                    if clicks_this_scan == 0:
                        time.sleep(0.1)
                else:
                    time.sleep(0.01)
                    
            except Exception:
                # Removed error logging to prevent terminal flood
                continue
