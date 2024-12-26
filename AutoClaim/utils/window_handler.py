import pygetwindow as gw
import time
from config import COLORS

class WindowHandler:
    def find_telegram_window(self):
        """
        Mencari window Telegram dengan berbagai kemungkinan nama
        """
        possible_names = [
            "Telegram",
            "TelegramDesktop",
            "Telegram Desktop",
            "(30) Telegram",  # Untuk kasus ada notifikasi
            "(30) TON Station",  # Specific chat window
            "TON Station"
        ]
        
        found_window = None
        
        # Coba setiap kemungkinan nama
        for name in possible_names:
            windows = gw.getWindowsWithTitle(name)
            if windows:
                found_window = windows[0]
                print(f"{COLORS['GREEN']} [>] | Window found - {name}")
                break
                
        if not found_window:
            print(f"{COLORS['WHITE']} [>] | Telegram window {COLORS['YELLOW']}not found!{COLORS['RESET']}")
            print(f" {COLORS['RED']}Make sure Telegram Desktop is open and visible{COLORS['RESET']}")
            return None
            
        # Coba aktifkan window
        try:
            found_window.activate()
            time.sleep(1)  # Tunggu window aktif
            
            # Pastikan window tidak diminimize
            if found_window.isMinimized:
                found_window.restore()
                time.sleep(0.5)
                
        except Exception as e:
            print(f"{COLORS['RED']}Error activating window: {str(e)}{COLORS['RESET']}")
            return None
            
        return found_window

    def list_all_windows(self):
        """
        Debug function: Menampilkan semua window yang ada
        """
        all_windows = gw.getAllWindows()
        print("\nAll available windows:")
        for window in all_windows:
            if window.title:  # Only show windows with titles
                print(f"- {window.title}")

    def get_window_info(self, window):
        """
        Mendapatkan informasi tentang window
        """
        return {
            'title': window.title,
            'position': (window.left, window.top),
            'size': (window.width, window.height),
            'active': window.isActive,
            'visible': window.visible,
            'minimized': window.isMinimized
        }

    def ensure_window_visible(self, window):
        """
        Memastikan window terlihat dan aktif
        """
        try:
            if window.isMinimized:
                window.restore()
            window.activate()
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"{COLORS['RED']}Error ensuring window visibility: {str(e)}{COLORS['RESET']}")
            return False

    def move_window(self, window, x=None, y=None):
        """
        Memindahkan window ke posisi tertentu
        Args:
            window: Window object dari pygetwindow
            x: Posisi x (optional)
            y: Posisi y (optional)
        """
        try:
            current_x = window.left
            current_y = window.top
            
            new_x = x if x is not None else current_x
            new_y = y if y is not None else current_y
            
            window.moveTo(new_x, new_y)
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"{COLORS['RED']}Error moving window: {str(e)}{COLORS['RESET']}")
            return False

    def resize_window(self, window, width=None, height=None):
        """
        Mengubah ukuran window
        Args:
            window: Window object dari pygetwindow
            width: Lebar baru (optional)
            height: Tinggi baru (optional)
        """
        try:
            current_width = window.width
            current_height = window.height
            
            new_width = width if width is not None else current_width
            new_height = height if height is not None else current_height
            
            window.resizeTo(new_width, new_height)
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"{COLORS['RED']}Error resizing window: {str(e)}{COLORS['RESET']}")
            return False 