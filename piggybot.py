import tkinter as tk
from PIL import ImageTk, Image
import pyautogui
import time
import keyboard
from pynput.mouse import Button, Controller
import cv2
import numpy as np
import random
import math
from basket_predictor import BasketPredictor

class BasketballBot:
    def __init__(self):
        self.ball_pos = None
        self.running = True
        self.paused = False
        self.mouse = Controller()
        self.shot_delay = 1.0
        self.mode = None
        self.shot_count = 0    
        self.log_file = 'basket_analysis.txt'  
        self.predictor = BasketPredictor()

    def get_mode(self):
        while True:
            print("\nSelect mode:")
            print("1. Daily (0.5s delay)")
            print("2. Matching (Ultra-fast)")
            try:
                choice = input("Enter choice (1 or 2): ")
                if choice == '1':
                    self.shot_delay = 0.5
                    self.mode = 'daily'
                    print("\nDaily mode selected (0.5s delay)")
                    return
                elif choice == '2':
                    self.shot_delay = 0.005
                    self.mode = 'matching'
                    print("\nMatching mode selected (Ultra-fast)")
                    return
                else:
                    print("Please enter 1 or 2")
            except ValueError:
                print("Invalid input")

    def swipe(self, start_x, start_y, end_x, end_y):
        """Perform fast swipe action with balanced speed and accuracy"""
        try:
            # Get current basket movement speed from history
            basket_speed = self.predictor.get_basket_speed()

            # Adaptive settings based on basket movement
            if self.mode == 'matching':
                if basket_speed > 5:  # Moving basket
                    duration = 0.06    
                    steps = 6 
                    wait_start = 0.015
                    wait_end = 0.015
                    curve_height = 1.2
                else:  # Stationary or slow-moving basket
                    duration = 0.08    
                    steps = 8
                    wait_start = 0.02
                    wait_end = 0.02
                    curve_height = 1.5
            else:  # daily mode
                duration = 0.2
                steps = 15
                wait_start = 0.05
                wait_end = 0.05
                curve_height = 2
            
            # Pre-position mouse
            self.mouse.position = (start_x, start_y)
            time.sleep(wait_start)
            
            # Press and initial hold
            self.mouse.press(Button.left)
            
            # Smooth movement
            for i in range(steps):
                progress = i / steps
                curve = math.sin(progress * math.pi) * curve_height
                
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress + curve)
                
                self.mouse.position = (current_x, current_y)
                time.sleep(duration / steps)
            
            # Ensure final position and release
            self.mouse.position = (end_x, end_y)
            time.sleep(wait_end)
            self.mouse.release(Button.left)
            
            # Adaptive delay between shots
            if self.mode == 'matching':
                if basket_speed > 5:
                    time.sleep(0.01)   
                else:
                    time.sleep(0.015)  
            else:
                time.sleep(max(0.05, self.shot_delay))
            
        except Exception as e:
            print(f"Swipe error: {e}")

    def calibrate(self):
        root = tk.Tk()
        root.title("Basketball Game Calibration")
        root.attributes('-topmost', True)
        
        def on_click(event):
            x = root.winfo_x() + event.x
            y = root.winfo_y() + event.y
            
            if not self.ball_pos:
                self.ball_pos = (x, y)
                canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, fill='red')
                print(f"Ball position saved: ({x}, {y})")
                root.destroy()

        screenshot = pyautogui.screenshot()
        photo = ImageTk.PhotoImage(screenshot)
        
        canvas = tk.Canvas(root, width=screenshot.width, height=screenshot.height)
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.bind("<Button-1>", on_click)
        
        root.bind('<Escape>', lambda e: root.destroy())
        
        print("Click on the ball position")
        root.mainloop()
        
        return self.ball_pos is not None

    def play_game(self):
        try:
            basket_pos = self.predictor.get_basket_position()
            if basket_pos and len(basket_pos) == 2:
                self.shot_count += 1
                aim_x, aim_y = basket_pos
                self.swipe(self.ball_pos[0], self.ball_pos[1], aim_x, aim_y)
            else:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Game error: {e}")
            time.sleep(0.1)

def main():
    bot = BasketballBot()
    
    print("Piggy Basketball Bot")
    print("------------------")
    print("Please make sure the game window is visible")
    print("Controls:")
    print("- Press 'Q' to stop the bot")
    print("- Press 'W' to pause/resume")
    print("- Press 'R' to return to mode selection")
    print("- Press 'ESC' to exit during calibration")
    print("- Press 'SPACE' to start after calibration")
    
    while True:
        bot.get_mode()
        time.sleep(1)
        
        if not bot.calibrate():
            print("\nCalibration cancelled")
            continue
        
        print(f"\nBot calibrated in {bot.mode.upper()} mode!")
        print("Press SPACE to start...")
        
        # Wait for space key
        while True:
            if keyboard.is_pressed('space'):
                print("Bot Started!")
                print("------------")
                break
            if keyboard.is_pressed('r'):
                break
            if keyboard.is_pressed('q'):
                bot.running = False
                return
            time.sleep(0.1)
        
        while bot.running:
            try:
                if keyboard.is_pressed('q'):
                    print("\nBot stopped by user")
                    bot.running = False
                    break
                
                if keyboard.is_pressed('w'):
                    bot.paused = not bot.paused
                    print(f"\nBot {'paused' if bot.paused else 'resumed'}")
                    time.sleep(0.2)
                
                if keyboard.is_pressed('r'):
                    print("\nReturning to mode selection...")
                    bot.running = True
                    bot.ball_pos = None
                    time.sleep(0.2)
                    break
                
                if not bot.paused:
                    bot.play_game()
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"\nError occurred: {e}")
                time.sleep(1)
                continue
            
            except KeyboardInterrupt:
                print("\nBot stopped by user")
                bot.running = False
                break
        
        if not bot.running:
            break

if __name__ == "__main__":
    main()

