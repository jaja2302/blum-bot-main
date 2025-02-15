import tkinter as tk
from PIL import ImageTk, Image
import pyautogui
import time
from window_detector import WindowDetector

class Calibrator:
    def __init__(self):
        self.doors = []
        self.go_back_pos = None
        self.claim_pos = None
        self.window_detector = WindowDetector()
        self.markers = []  # Untuk menyimpan referensi marker
        self.callback = None  # Tambahkan callback
        
    def create_marker(self, canvas, x, y, color='red'):
        """Membuat marker visual di canvas"""
        marker = canvas.create_oval(x-5, y-5, x+5, y+5, fill=color, outline='white')
        # Tambahkan label
        label = canvas.create_text(x, y-15, text=f"#{len(self.markers)+1}", fill='white')
        self.markers.append((marker, label))
        
    def set_callback(self, callback):
        """Set callback function to be called after calibration"""
        self.callback = callback
        
    def calibrate(self):
        # Reset state setiap kali kalibrasi dimulai
        self.doors = []
        self.go_back_pos = None
        self.claim_pos = None
        self.markers = []
        
        # Find and activate Telegram window
        window_info = self.window_detector.find_window()
        if not window_info:
            print("Telegram window not found!")
            return None
            
        # Activate window
        if not self.window_detector.activate_window(window_info):
            print("Failed to activate Telegram window!")
            return None
            
        # Get window region
        x, y, width, height = self.window_detector.get_window_region(window_info)
        
        root = tk.Tk()
        root.title("Door Calibration")
        root.attributes('-topmost', True)
        
        # Set window size and position to match Telegram
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        def on_click(event):
            # Dapatkan posisi window saat ini (bisa berubah jika window dipindah)
            current_x = root.winfo_x()
            current_y = root.winfo_y()
            
            # Hitung offset dari border window
            border_offset_x = root.winfo_rootx() - current_x
            border_offset_y = root.winfo_rooty() - current_y
            
            # Hitung koordinat klik yang sebenarnya
            click_x = current_x + event.x + border_offset_x
            click_y = current_y + event.y + border_offset_y
            
            # Debug info
            self.log(f"Click at: ({click_x}, {click_y})")
            self.log(f"Window pos: ({current_x}, {current_y})")
            self.log(f"Border offset: ({border_offset_x}, {border_offset_y})")
            
            if len(self.doors) < 3:
                self.doors.append((click_x, click_y))
                self.create_marker(canvas, event.x, event.y, 'red')
                self.log(f"Door #{len(self.doors)} position saved: ({click_x}, {click_y})")
                
                if len(self.doors) == 3:
                    self.log("\nNow click the Go Back button position (for stage 2-4)")
            
            elif not self.go_back_pos:
                self.go_back_pos = (click_x, click_y)
                self.create_marker(canvas, event.x, event.y, 'blue')
                self.log(f"Go Back button position saved: ({click_x}, {click_y})")
                self.log("\nNow click the Claim/First Go Back button position")
            
            elif not self.claim_pos:
                self.claim_pos = (click_x, click_y)
                self.create_marker(canvas, event.x, event.y, 'green')
                self.log(f"Claim/First Go Back position saved: ({click_x}, {click_y})")
                self.log("\nAll positions marked! Starting bot in 3 seconds...")
                
                # Verifikasi koordinat
                self.log("\nVerifying coordinates:")
                self.log(f"Doors: {self.doors}")
                self.log(f"Go Back: {self.go_back_pos}")
                self.log(f"Claim: {self.claim_pos}")
                
                def finish_calibration():
                    data = {
                        'doors': self.doors,
                        'go_back_pos': self.go_back_pos,
                        'claim_pos': self.claim_pos
                    }
                    root.destroy()
                    if self.callback:
                        self.callback(data)
                
                root.after(3000, finish_calibration)

        # Create transparent canvas
        canvas = tk.Canvas(root, width=width, height=height)
        canvas.pack(fill='both', expand=True)
        canvas.configure(highlightthickness=0)
        
        # Make window transparent
        root.attributes('-alpha', 0.3)
        
        # Bind click event
        canvas.bind("<Button-1>", on_click)
        
        # Add keyboard shortcut to exit
        root.bind('<Escape>', lambda e: root.destroy())
        
        print("Click on the center of each door (3 total)")
        root.mainloop()
        
        if len(self.doors) == 3 and self.go_back_pos and self.claim_pos:
            return {
                'doors': self.doors,
                'go_back_pos': self.go_back_pos,
                'claim_pos': self.claim_pos
            }
        return None

    def log(self, message):
        """Log message untuk debugging"""
        print(message)

if __name__ == "__main__":
    calibrator = Calibrator()
    print("Starting calibration...")
    print("Please make sure Telegram window is visible")
    time.sleep(2)
    result = calibrator.calibrate()
    if result:
        print("Calibration successful!")
        print(result)
    else:
        print("Calibration failed or cancelled") 