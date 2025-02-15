import json
import pyautogui
import keyboard
import time
from window_detector import WindowDetector
import tkinter as tk
from PIL import ImageTk, Image
import numpy as np
import cv2

class BoardCalibrator:
    def __init__(self):
        self.window_detector = WindowDetector()
        self.calibration_data = self.load_existing_calibration()
        self.screenshot = None
        self.window_info = None
        self.corners = []  # Untuk menyimpan 4 sudut
        self.corner_names = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
        self.dragging = None
        self.cell_size = None
        
    def load_existing_calibration(self):
        """Load existing calibration if exists"""
        try:
            with open('board_calibration.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "corners": {},
                "window_info": None
            }

    def take_window_screenshot(self):
        """Ambil screenshot window Telegram"""
        window_info = self.window_detector.find_window()
        if window_info:
            self.window_info = window_info
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
        root.title("Game Board Calibration")
        root.attributes('-topmost', True)

        def on_mouse_press(event):
            """Handle mouse press untuk memulai drag"""
            x, y = event.x, event.y
            
            # Cek apakah klik dekat dengan corner yang sudah ada
            for i, (cx, cy) in enumerate(self.corners):
                if abs(x - cx) < 10 and abs(y - cy) < 10:
                    self.dragging = i
                    return
                    
            # Jika tidak dekat corner yang ada, tambah corner baru
            if len(self.corners) < 4:
                self.corners.append((x, y))
                redraw_calibration()

        def on_mouse_move(event):
            """Handle mouse movement untuk drag corner"""
            if self.dragging is not None:
                self.corners[self.dragging] = (event.x, event.y)
                redraw_calibration()

        def on_mouse_release(event):
            """Handle mouse release untuk end drag"""
            self.dragging = None
            update_calibration_data()

        def update_calibration_data():
            """Update data kalibrasi dari posisi corner"""
            if len(self.corners) == 4:
                for i, corner_name in enumerate(self.corner_names):
                    self.calibration_data["corners"][corner_name] = {
                        "x": self.corners[i][0] + self.window_info['left'],
                        "y": self.corners[i][1] + self.window_info['top']
                    }

        def redraw_calibration():
            """Redraw semua elemen kalibrasi"""
            canvas.delete("all")
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            
            # Draw corners and lines
            if self.corners:
                # Draw lines
                for i in range(len(self.corners)):
                    x1, y1 = self.corners[i]
                    x2, y2 = self.corners[(i+1)%len(self.corners)]
                    canvas.create_line(x1, y1, x2, y2, fill='green', width=2)
                
                # Draw corner points and labels
                for i, (x, y) in enumerate(self.corners):
                    canvas.create_oval(x-5, y-5, x+5, y+5, fill='red')
                    canvas.create_text(x, y-15, text=self.corner_names[i], fill='yellow')

        def preview_detection():
            """Preview deteksi papan dengan grid dan titik scanning"""
            if len(self.corners) != 4:
                print("Tentukan 4 sudut terlebih dahulu!")
                return
                
            preview_window = tk.Toplevel()
            preview_window.title("Detection Preview")
            preview_window.attributes('-topmost', True)
            
            # Frame untuk kontrol
            control_frame = tk.Frame(preview_window)
            control_frame.pack(side=tk.TOP, pady=5)
            
            # Inisialisasi cell size berdasarkan lebar board dibagi 9
            cell_width = self.corners[1][0] - self.corners[0][0]
            self.cell_size = int(cell_width / 9)
            initial_cell_size = self.cell_size
            
            # Grid info frame
            info_frame = tk.Frame(control_frame)
            info_frame.pack(side=tk.LEFT, padx=20)
            
            grid_label = tk.Label(info_frame, text="Grid Size: 9x11")
            grid_label.pack(side=tk.LEFT)
            
            size_label = tk.Label(info_frame, text="")
            size_label.pack(side=tk.LEFT, padx=10)
            
            def update_info():
                """Update info label dengan dimensi grid"""
                width = 9 * self.cell_size
                height = 11 * self.cell_size
                size_label.config(
                    text=f"Dimensions: {width}x{height}px"
                )
            
            def update_cell_size(val):
                """Update cell size dan refresh display"""
                self.cell_size = int(val)
                update_info()
                redraw_preview()
            
            # Cell size control
            cell_size_frame = tk.Frame(control_frame)
            cell_size_frame.pack(side=tk.LEFT, padx=5)
            
            tk.Label(cell_size_frame, text="Cell Size:").pack(side=tk.LEFT)
            cell_size_slider = tk.Scale(
                cell_size_frame,
                from_=20, to=60,
                orient=tk.HORIZONTAL,
                length=200,
                command=update_cell_size
            )
            cell_size_slider.set(initial_cell_size)
            cell_size_slider.pack(side=tk.LEFT, padx=5)
            
            # Offset controls
            offset_frame = tk.Frame(control_frame)
            offset_frame.pack(side=tk.LEFT, padx=20)
            
            offset_x = tk.IntVar(value=0)
            offset_y = tk.IntVar(value=0)
            
            def update_offset(*args):
                redraw_preview()
            
            tk.Label(offset_frame, text="X Offset:").pack(side=tk.LEFT)
            x_offset = tk.Scale(
                offset_frame,
                from_=-20, to=20,
                orient=tk.HORIZONTAL,
                length=100,
                variable=offset_x,
                command=update_offset
            )
            x_offset.pack(side=tk.LEFT, padx=5)
            
            tk.Label(offset_frame, text="Y Offset:").pack(side=tk.LEFT)
            y_offset = tk.Scale(
                offset_frame,
                from_=-20, to=20,
                orient=tk.HORIZONTAL,
                length=100,
                variable=offset_y,
                command=update_offset
            )
            y_offset.pack(side=tk.LEFT, padx=5)
            
            # Create preview canvas
            preview_canvas = tk.Canvas(preview_window, 
                                     width=self.window_info['width'],
                                     height=self.window_info['height'])
            preview_canvas.pack(pady=5)
            
            def redraw_preview():
                preview_canvas.delete("all")
                preview_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                
                # Get current values
                cell_size = self.cell_size
                x_off = offset_x.get()
                y_off = offset_y.get()
                
                # Calculate adjusted start position
                start_x = self.corners[0][0] + x_off
                start_y = self.corners[0][1] + y_off
                
                # Calculate end positions
                end_x = start_x + (9 * cell_size)  # 9 columns
                end_y = start_y + (11 * cell_size)  # 11 rows
                
                # Draw grid - vertical lines
                for i in range(10):  # 10 lines for 9 columns
                    x = int(start_x + (i * cell_size))
                    preview_canvas.create_line(
                        x, start_y,  # start point
                        x, end_y,    # end point
                        fill='yellow',
                        width=1
                    )
                
                # Draw horizontal lines
                for i in range(12):  # 12 lines for 11 rows
                    y = int(start_y + (i * cell_size))
                    preview_canvas.create_line(
                        start_x, y,  # start point
                        end_x, y,    # end point
                        fill='yellow',
                        width=1
                    )
                
                # Draw scan points
                for row in range(11):
                    for col in range(9):
                        x = int(start_x + (col * cell_size) + (cell_size // 2))
                        y = int(start_y + (row * cell_size) + (cell_size // 2))
                        
                        # Draw cell border
                        cell_x = start_x + (col * cell_size)
                        cell_y = start_y + (row * cell_size)
                        preview_canvas.create_rectangle(
                            cell_x, cell_y,
                            cell_x + cell_size, cell_y + cell_size,
                            outline='gray',
                            width=1
                        )
                        
                        # Draw scan point
                        preview_canvas.create_oval(
                            x-4, y-4,
                            x+4, y+4,
                            fill='red'
                        )
                        
                        # Add coordinate text
                        preview_canvas.create_text(
                            x, y-10,
                            text=f"({col},{row})",
                            fill='white',
                            font=('Arial', 8),
                            stipple='gray50'
                        )
                        
                        # Add pixel color preview
                        try:
                            screen_x = x + self.window_info['left']
                            screen_y = y + self.window_info['top']
                            pixel = pyautogui.pixel(screen_x, screen_y)
                            color_hex = '#{:02x}{:02x}{:02x}'.format(*pixel)
                            preview_canvas.create_text(
                                x, y+10,
                                text=color_hex,
                                fill='cyan',
                                font=('Arial', 7)
                            )
                        except:
                            pass
            
            def apply_and_save():
                """Terapkan pengaturan saat ini ke kalibrasi"""
                try:
                    x_off = offset_x.get()
                    y_off = offset_y.get()
                    
                    # Update corners dengan offset
                    for corner in self.calibration_data["corners"]:
                        self.calibration_data["corners"][corner]["x"] += x_off
                        self.calibration_data["corners"][corner]["y"] += y_off
                    
                    # Simpan cell size
                    self.calibration_data["cell_size"] = self.cell_size
                    
                    # Simpan ke file
                    self.save_calibration()
                    print(f"Kalibrasi grid disimpan! Cell size: {self.cell_size}px")
                    preview_window.destroy()
                    
                except Exception as e:
                    print(f"Error saat menyimpan kalibrasi: {str(e)}")
            
            # Add Apply button
            apply_button = tk.Button(
                control_frame,
                text="Apply & Save",
                command=apply_and_save
            )
            apply_button.pack(side=tk.LEFT, padx=20)
            
            # Initial updates
            update_info()
            redraw_preview()

        # Setup GUI
        photo = ImageTk.PhotoImage(self.screenshot)
        
        canvas = tk.Canvas(root, width=self.window_info['width'], 
                         height=self.window_info['height'])
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        
        # Bind mouse events
        canvas.bind("<Button-1>", on_mouse_press)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_release)

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        preview_button = tk.Button(button_frame, text="Preview Detection", 
                                 command=preview_detection)
        preview_button.pack(side=tk.LEFT, padx=5)
        
        save_button = tk.Button(button_frame, text="Save & Exit", 
                              command=lambda: self.save_and_exit(root))
        save_button.pack(side=tk.LEFT, padx=5)
        
        reset_button = tk.Button(button_frame, text="Reset", 
                               command=lambda: self.reset_calibration(canvas, photo))
        reset_button.pack(side=tk.LEFT, padx=5)
        
        # Load existing calibration if any
        if "corners" in self.calibration_data:
            for corner_name in self.corner_names:
                if corner_name in self.calibration_data["corners"]:
                    pos = self.calibration_data["corners"][corner_name]
                    x = pos['x'] - self.window_info['left']
                    y = pos['y'] - self.window_info['top']
                    self.corners.append((x, y))
            redraw_calibration()

        # Instructions
        print("\nInstruksi Kalibrasi Board Game:")
        print("1. Klik untuk menambah sudut (4 sudut)")
        print("2. Drag sudut untuk menyesuaikan posisi")
        print("3. Klik 'Preview Detection' untuk melihat hasil")
        print("4. Klik 'Save & Exit' jika sudah sesuai")
        print("5. Klik 'Reset' untuk mengulang\n")

        root.mainloop()

    def save_calibration(self):
        """Simpan data kalibrasi ke file JSON"""
        try:
            self.calibration_data["window_info"] = self.window_info
            with open('board_calibration.json', 'w') as f:
                json.dump(self.calibration_data, f, indent=4)
        except Exception as e:
            print(f"Error menyimpan kalibrasi: {e}")

    def reset_calibration(self, canvas, photo):
        """Reset kalibrasi"""
        self.calibration_data["corners"] = {}
        self.corners = []
        canvas.delete("all")
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        print(f"Kalibrasi direset!")

    def save_and_exit(self, root):
        """Simpan kalibrasi dan tutup window"""
        if len(self.corners) == 4:
            self.save_calibration()
            print("Kalibrasi board game disimpan!")
            root.destroy()
        else:
            print("Harap tentukan 4 sudut board game terlebih dahulu!")

if __name__ == "__main__":
    calibrator = BoardCalibrator()
    calibrator.start_calibration() 