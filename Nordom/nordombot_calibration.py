import tkinter as tk
from PIL import ImageTk, Image, ImageDraw
import pyautogui
import time
import keyboard
from pynput.mouse import Button, Controller

def calibrate():
    root = tk.Tk()
    root.title("Door Calibration")
    
    # Make window appear on top
    root.attributes('-topmost', True)
    
    print("Starting calibration...")
    print("Press 'ESC' to exit calibration")
    
    def on_click(event):
        nonlocal doors
        if len(doors) < 3:
            doors.append((event.x, event.y))
            # Draw a marker where clicked
            canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, fill='red')
            print(f"Door {len(doors)} position saved: ({event.x}, {event.y})")
            
            if len(doors) == 3:
                save_button.config(state='normal')
                print("All 3 doors marked! You can now save or reset.")

    def save_coordinates():
        with open('door_coordinates.txt', 'w') as f:
            for x, y in doors:
                f.write(f"{x},{y}\n")
        print("Door coordinates saved!")
        root.destroy()

    def reset_coordinates():
        nonlocal doors
        doors = []
        canvas.delete("all")
        # Redraw the screenshot
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        save_button.config(state='disabled')
        print("Coordinates reset. Click to mark doors again.")

    # Take screenshot
    screenshot = pyautogui.screenshot()
    photo = ImageTk.PhotoImage(screenshot)
    
    # Initialize doors list
    doors = []
    
    # Create canvas and display image
    canvas = tk.Canvas(root, width=screenshot.width, height=screenshot.height)
    canvas.pack()
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    
    # Bind click event
    canvas.bind("<Button-1>", on_click)
    
    # Create button frame
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    # Add buttons
    save_button = tk.Button(button_frame, text="Save Coordinates", command=save_coordinates, state='disabled')
    save_button.pack(side=tk.LEFT, padx=5)
    
    reset_button = tk.Button(button_frame, text="Reset", command=reset_coordinates)
    reset_button.pack(side=tk.LEFT, padx=5)
    
    quit_button = tk.Button(button_frame, text="Quit", command=root.destroy)
    quit_button.pack(side=tk.LEFT, padx=5)
    
    # Add keyboard shortcut to exit
    root.bind('<Escape>', lambda e: root.destroy())
    
    print("Click on the center of each door (3 total)")
    root.mainloop()

if __name__ == "__main__":
    print("Starting door calibration...")
    print("Please make sure the game window is visible")
    time.sleep(2)
    calibrate()