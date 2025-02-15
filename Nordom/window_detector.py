import pygetwindow as gw
import time
import win32gui
import win32con

class WindowDetector:

    def __init__(self):
        self.window_name = "Mini App: Nordom Gates"

    def find_window(self):
        """Find Telegram window and return window object"""
        windows = gw.getWindowsWithTitle(self.window_name)
        
        if not windows:
            windows = [w for w in gw.getAllWindows() if "Nordom Gates" in w.title]
        
        if windows:
            window = windows[0]
            print(f"Found window: {window.title}")
            return {
                'window': window,
                'left': window.left,
                'top': window.top,
                'width': window.width,
                'height': window.height
            }
            
        print("Available windows:")
        for w in gw.getAllWindows():
            if w.title:
                print(f"- {w.title}")
                
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
                hwnd = win32gui.FindWindow(None, window_info['window'].title)
                if hwnd:
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