import pygetwindow as gw
import time

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

    def activate_window(self, window):
        """Activate and focus the window"""
        if window:
            window['window'].activate()
            time.sleep(1)  # Wait for window to activate
            return True
        return False 