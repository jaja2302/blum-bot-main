import numpy as np
import win32gui
import win32ui
import win32con
from PIL import Image

class ScreenCapture:
    def __init__(self):
        self.game_region = None  # Will store the game area coordinates

    def capture_window(self, hwnd):
        """Capture a window's content given its handle"""
        # Get window dimensions
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        # Create device context
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        # Create bitmap object
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(save_bitmap)

        # Copy screen into bitmap
        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

        # Convert bitmap to numpy array
        bmpinfo = save_bitmap.GetInfo()
        bmpstr = save_bitmap.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        
        # Clean up
        win32gui.DeleteObject(save_bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        return np.array(img)

    def set_game_region(self, region):
        """Set the specific region of the window where the game is located"""
        self.game_region = region

    def get_game_screen(self, hwnd):
        """Capture only the game area within the window"""
        full_screen = self.capture_window(hwnd)
        if self.game_region:
            x1, y1, x2, y2 = self.game_region
            return full_screen[y1:y2, x1:x2]
        return full_screen 