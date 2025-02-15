import pygetwindow as gw

class WindowDetector:
    def __init__(self):
        self.window_name = "TelegramDesktop"
        
    def find_window(self):
        """Find Telegram window and return its info"""
        windows = gw.getWindowsWithTitle(self.window_name)
        if windows:
            window = windows[0]
            return {
                'left': window.left,
                'top': window.top,
                'width': window.width,
                'height': window.height
            }
        return None 