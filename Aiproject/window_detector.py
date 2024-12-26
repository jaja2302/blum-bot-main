import pygetwindow as gw
import time
import win32gui
import win32con

class WindowDetector:
    def find_window(self, window_name="TelegramDesktop"):
        """Find Telegram window and return window object"""
        telegram_windows = gw.getWindowsWithTitle(window_name)
        
        if telegram_windows:
            window = telegram_windows[0]
            return {
                'window': window,
                'left': window.left,
                'top': window.top,
                'width': window.width,
                'height': window.height
            }
        return None

    def activate_window(self, window_info):
        """Activate and focus the window"""
        try:
            if window_info:
                # Restore window jika diminimize
                window_info['window'].restore()
                
                # Aktifkan window
                window_info['window'].activate()
                
                # Pindahkan ke foreground
                hwnd = win32gui.FindWindow(None, "TelegramDesktop")
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                
                # Tunggu window benar-benar aktif
                time.sleep(1)
                
                # Pastikan window tidak minimize
                if window_info['window'].isMinimized:
                    window_info['window'].restore()
                    time.sleep(0.5)
                
                return True
        except Exception as e:
            print(f"Error activating window: {e}")
        return False

    def get_window_region(self, window_info):
        """Get window region for clicking"""
        if window_info:
            return (
                window_info['left'],
                window_info['top'],
                window_info['width'],
                window_info['height']
            )
        return None 