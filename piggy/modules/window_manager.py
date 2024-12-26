import win32gui

class WindowManager:
    def get_game_window(self):
        """Find the Telegram window"""
        def callback(hwnd, windows):
            if "Telegram" in win32gui.GetWindowText(hwnd):
                windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if not windows:
            print("Error: Could not find Telegram window!")
            return None
            
        hwnd = windows[0]
        rect = win32gui.GetWindowRect(hwnd)
        x, y, x2, y2 = rect
        w = x2 - x
        h = y2 - y
        
        print(f"Found Telegram window: {w}x{h} at ({x}, {y})")
        return (x, y, w, h) 