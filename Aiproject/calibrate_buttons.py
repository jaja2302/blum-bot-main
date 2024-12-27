import json
import pyautogui
import keyboard
import time
from window_detector import WindowDetector
import tkinter as tk
from PIL import ImageTk, Image
import numpy as np
import cv2

class ButtonCalibrator:
    def __init__(self):
        self.window_detector = WindowDetector()
        self.calibration_data = self.load_existing_calibration()
        self.screenshot = None
        self.window_info = None
        
    def load_existing_calibration(self):
        """Load existing calibration if exists"""
        try:
            with open('button_claim_game_over.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "buttons": {},
                "window_info": None
            }

    def take_window_screenshot(self):
        """Ambil screenshot window Telegram"""
        window_info = self.window_detector.find_window()
        if window_info:
            self.window_info = window_info
            # Ambil screenshot area window saja
            screenshot = pyautogui.screenshot(region=(
                window_info['left'],
                window_info['top'],
                window_info['width'],
                window_info['height']
            ))
            return screenshot
        return None

    def start_calibration(self):
        """Mulai proses kalibrasi dengan GUI"""
        print("\nMencari window Telegram...")
        self.screenshot = self.take_window_screenshot()
        
        if not self.screenshot:
            print("Window Telegram tidak ditemukan!")
            return

        root = tk.Tk()
        root.title("Button Calibration")
        root.attributes('-topmost', True)

        def on_click(event):
            """Handle click event untuk kalibrasi button"""
            x, y = event.x, event.y
            print("\nMasukkan nama button (contoh: claim, ok, play):")
            button_name = input().strip().lower()
            
            if button_name:
                self.calibration_data["buttons"][button_name] = {
                    "x": x,
                    "y": y
                }
                # Draw a dot on canvas
                canvas.create_oval(x-5, y-5, x+5, y+5, fill='red')
                canvas.create_text(x, y-15, text=button_name, fill='yellow')
                print(f"Button '{button_name}' dikalibrasi di: ({x}, {y})")

        def save_and_exit():
            """Simpan kalibrasi dan tutup window"""
            self.save_calibration()
            print("Kalibrasi disimpan!")
            root.destroy()

        def reset_calibration():
            """Reset semua kalibrasi"""
            self.calibration_data["buttons"] = {}
            canvas.delete("all")
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            print("Kalibrasi direset!")

        # Setup GUI
        photo = ImageTk.PhotoImage(self.screenshot)
        
        canvas = tk.Canvas(root, width=self.window_info['width'], 
                         height=self.window_info['height'])
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.bind("<Button-1>", on_click)

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        save_button = tk.Button(button_frame, text="Save & Exit", command=save_and_exit)
        save_button.pack(side=tk.LEFT, padx=5)
        
        reset_button = tk.Button(button_frame, text="Reset", command=reset_calibration)
        reset_button.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        print("\nInstruksi Kalibrasi:")
        print("1. Klik posisi button pada gambar")
        print("2. Masukkan nama button di terminal")
        print("3. Ulangi untuk button lainnya")
        print("4. Klik 'Save & Exit' untuk menyimpan")
        print("5. Klik 'Reset' untuk mengulang\n")

        # Draw existing calibration points if any
        for name, pos in self.calibration_data["buttons"].items():
            canvas.create_oval(pos['x']-5, pos['y']-5, 
                             pos['x']+5, pos['y']+5, fill='red')
            canvas.create_text(pos['x'], pos['y']-15, 
                             text=name, fill='yellow')

        root.mainloop()

    def save_calibration(self):
        """Simpan data kalibrasi ke file JSON"""
        try:
            with open('button_claim_game_over.json', 'w') as f:
                json.dump(self.calibration_data, f, indent=4)
        except Exception as e:
            print(f"Error menyimpan kalibrasi: {e}")

if __name__ == "__main__":
    calibrator = ButtonCalibrator()
    calibrator.start_calibration() 