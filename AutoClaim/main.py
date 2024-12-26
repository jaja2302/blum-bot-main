import logging
from utils.window_handler import WindowHandler
from utils.game_config import get_all_games, get_game_config, get_button_text
from config import COLORS
import pyautogui
import pytesseract
import cv2
import numpy as np
import time
import psutil
import subprocess
import pygetwindow as gw

# Set path to tesseract executable - PENTING: Sesuaikan dengan lokasi instalasi di komputer Anda
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Verifikasi Tesseract terinstall
try:
    # Test OCR dengan gambar sederhana
    test_image = np.zeros((100, 100), dtype=np.uint8)
    pytesseract.image_to_string(test_image)
    print(f"{COLORS['GREEN']}Tesseract OCR initialized successfully!{COLORS['RESET']}")
except Exception as e:
    print(f"{COLORS['RED']}Error initializing Tesseract OCR: {str(e)}")
    print(f"Please make sure Tesseract is installed and the path is correct:")
    print(f"Current path: {pytesseract.pytesseract.tesseract_cmd}{COLORS['RESET']}")
    exit(1)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GameController:
    def __init__(self):
        self.window_handler = WindowHandler()
        self.games = get_all_games()
        
    def ensure_telegram_running(self):
        """
        Memastikan Telegram berjalan, jika tidak akan menjalankannya
        """
        telegram_running = False
        telegram_path = r"C:\Users\{username}\AppData\Roaming\Telegram Desktop\Telegram.exe"
        
        # Cek apakah Telegram sudah berjalan
        for proc in psutil.process_iter(['name']):
            try:
                if "telegram" in proc.info['name'].lower():
                    telegram_running = True
                    print(f"{COLORS['GREEN']}Telegram process found!{COLORS['RESET']}")
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if not telegram_running:
            print(f"{COLORS['YELLOW']}Telegram not running. Starting Telegram...{COLORS['RESET']}")
            try:
                subprocess.Popen(telegram_path)
                time.sleep(5)  # Tunggu Telegram startup
            except Exception as e:
                print(f"{COLORS['RED']}Error starting Telegram: {str(e)}{COLORS['RESET']}")
                return False
                
        return True

    def get_telegram_window(self):
        """
        Mendapatkan window Telegram dan memastikan visible
        """
        try:
            # Coba beberapa nama proses Telegram yang umum
            process_names = ["Telegram.exe", "telegram", "Telegram Desktop"]
            
            # Cari proses Telegram
            telegram_pid = None
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if any(name.lower() in proc.info['name'].lower() for name in process_names):
                        telegram_pid = proc.info['pid']
                        print(f"{COLORS['GREEN']}Found Telegram process (PID: {telegram_pid}){COLORS['RESET']}")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not telegram_pid:
                return None
                
            # Cari window berdasarkan PID
            time.sleep(2)  # Tunggu window load
            windows = gw.getAllWindows()
            
            for window in windows:
                try:
                    if "telegram" in window.title.lower():
                        window.activate()
                        window.restore()  # Un-minimize jika diminimize
                        time.sleep(1)
                        
                        # Return region (x, y, width, height)
                        return (window.left, window.top, window.width, window.height)
                except Exception:
                    continue
                    
            return None
            
        except Exception as e:
            print(f"{COLORS['RED']}Error getting Telegram window: {str(e)}{COLORS['RESET']}")
            return None

    def find_text_on_screen(self, text_to_find, debug=True):
        """
        Mencari teks di layar menggunakan OCR dengan region Telegram
        """
        try:
            # Pastikan Telegram berjalan dan dapatkan window-nya
            if not self.ensure_telegram_running():
                return None
                
            region = self.get_telegram_window()
            if not region:
                print(f"{COLORS['RED']}Could not find Telegram window!{COLORS['RESET']}")
                return None
            
            # Ambil screenshot dari window Telegram
            screenshot = pyautogui.screenshot(region=region)
            
            # Convert ke format yang bisa dibaca OpenCV
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Convert ke grayscale
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Threshold untuk mendapatkan teks hitam pada background putih
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Debug: Simpan screenshot untuk analisis
            if debug:
                cv2.imwrite('debug_telegram_window.png', screenshot)
                print(f"{COLORS['YELLOW']}Debug screenshot saved as 'debug_telegram_window.png'{COLORS['RESET']}")
            
            # Gunakan OCR
            data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT)
            
            # Debug: Print semua teks yang ditemukan
            if debug:
                print(f"\n{COLORS['YELLOW']}Detected text in Telegram window:{COLORS['RESET']}")
                for i, text in enumerate(data['text']):
                    if text.strip():
                        print(f"- '{text}'")
            
            # Cari teks yang cocok (case insensitive)
            for i, text in enumerate(data['text']):
                if text.strip() and text_to_find.lower() in text.lower():
                    x = data['left'][i] + region[0]
                    y = data['top'][i] + region[1]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    print(f"{COLORS['GREEN']}Found text '{text}' at ({x}, {y}){COLORS['RESET']}")
                    return (x + w//2, y + h//2)
            
            return None
            
        except Exception as e:
            print(f"{COLORS['RED']}Error during OCR: {str(e)}{COLORS['RESET']}")
            return None

    def find_and_click_button(self, button_text):
        """
        Mencari dan mengklik button berdasarkan teks menggunakan OCR
        """
        try:
            # Tunggu sebentar untuk memastikan chat sudah terbuka
            time.sleep(2)
            
            print(f"{COLORS['WHITE']}Looking for text: {button_text}{COLORS['RESET']}")
            
            # Coba beberapa kali jika tidak langsung ketemu
            for attempt in range(3):
                coords = self.find_text_on_screen(button_text)
                
                if coords:
                    x, y = coords
                    print(f"{COLORS['GREEN']}Clicking at coordinates ({x}, {y}){COLORS['RESET']}")
                    pyautogui.click(x, y)
                    time.sleep(1)
                    return True
                else:
                    print(f"{COLORS['YELLOW']}Attempt {attempt + 1}: Text not found, waiting...{COLORS['RESET']}")
                    time.sleep(2)
                    
            print(f"{COLORS['RED']}Text '{button_text}' not found after all attempts!{COLORS['RESET']}")
            return False
                
        except Exception as e:
            print(f"{COLORS['RED']}Error finding text: {str(e)}{COLORS['RESET']}")
            return False

    def start_game(self, game_key):
        """
        Memulai game setelah chat terbuka
        """
        game_config = get_game_config(game_key)
        if not game_config:
            return False
            
        # Tunggu chat benar-benar terbuka
        time.sleep(3)
        
        print(f"{COLORS['WHITE']}Waiting for game interface to load...{COLORS['RESET']}")
        
        # Cari dan klik Launch button
        launch_button = get_button_text(game_key, 'launch_game')
        if not self.find_and_click_button(launch_button):
            # Jika gagal dengan teks lengkap, coba dengan teks partial
            if not self.find_and_click_button("Launch"):
                print(f"{COLORS['RED']}Could not find launch button!{COLORS['RESET']}")
                return False
        
        return True

    def search_chat(self, game_key):
        """
        Mencari chat di Telegram menggunakan search
        """
        game_config = get_game_config(game_key)
        if not game_config:
            print(f"{COLORS['RED']}Game configuration not found!{COLORS['RESET']}")
            return False

        try:
            print(f"{COLORS['WHITE']}Opening search...{COLORS['RESET']}")
            
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'k')
            time.sleep(1)
            
            print(f"{COLORS['WHITE']}Typing search query: {game_config['username']}{COLORS['RESET']}")
            
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            time.sleep(0.5)
            
            pyautogui.write(game_config['username'], interval=0.1)
            time.sleep(1.5)
            
            print(f"{COLORS['WHITE']}Selecting chat...{COLORS['RESET']}")
            pyautogui.press('enter')
            time.sleep(1)
            
            print(f"{COLORS['GREEN']}Chat {game_config['name']} selected!{COLORS['RESET']}")
            return True
            
        except Exception as e:
            print(f"{COLORS['RED']}Error during search: {str(e)}{COLORS['RESET']}")
            return False

    def run(self):
        print(f"\n{COLORS['WHITE']}Checking Telegram window...{COLORS['RESET']}")
        
        window = self.window_handler.find_telegram_window()
        if not window:
            print(f"{COLORS['RED']}Please open Telegram Desktop first!{COLORS['RESET']}")
            return
            
        self.window_handler.ensure_window_visible(window)
            
        while True:
            self.display_menu()
            
            try:
                choice = input(f"\n{COLORS['WHITE']}Select game number to run [{COLORS['YELLOW']}0-{len(self.games)}{COLORS['WHITE']}]: {COLORS['RESET']}")
                
                if choice == '0':
                    print(f"{COLORS['GREEN']}Goodbye!{COLORS['RESET']}")
                    break
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(self.games):
                    game_key, game_name, _ = self.games[choice_idx]
                    print(f"{COLORS['WHITE']}Starting {game_name}...{COLORS['RESET']}")
                    
                    # Pastikan window aktif
                    self.window_handler.ensure_window_visible(window)
                    
                    # Cari dan buka chat
                    if self.search_chat(game_key):
                        # Mulai game
                        if self.start_game(game_key):
                            print(f"{COLORS['GREEN']}Game {game_name} started successfully!{COLORS['RESET']}")
                        else:
                            print(f"{COLORS['RED']}Failed to start {game_name}!{COLORS['RESET']}")
                    break
                else:
                    print(f"{COLORS['RED']}Invalid choice!{COLORS['RESET']}")
                    
            except ValueError:
                print(f"{COLORS['RED']}Please enter a valid number!{COLORS['RESET']}")
            except Exception as e:
                logger.error(f"Error: {str(e)}")

    def display_menu(self):
        print(f"\n{COLORS['GREEN']}=== Available Games ==={COLORS['RESET']}")
        for idx, (key, name, username) in enumerate(self.games, 1):
            print(f"{COLORS['WHITE']}[{COLORS['YELLOW']}{idx}{COLORS['WHITE']}] {name} ({COLORS['BLUE']}{username}{COLORS['WHITE']})")
        print(f"{COLORS['WHITE']}[{COLORS['YELLOW']}0{COLORS['WHITE']}] Exit{COLORS['RESET']}")

def main():
    controller = GameController()
    controller.run()

if __name__ == "__main__":
    main()
