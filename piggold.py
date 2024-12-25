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
from basket_prediction import BasketPredictor

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
        
        # Get the first screenshot to set the game window dimensions
        screenshot = pyautogui.screenshot()
        self.predictor.screen_width = screenshot.width

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
        """Simple direct swipe from ball to hoop"""
        try:
            # Move to start position
            self.mouse.position = (int(start_x), int(start_y))
            time.sleep(0.03)
            
            # Press mouse button
            self.mouse.press(Button.left)
            
            # Calculate arc movement
            steps = 8
            duration = 0.08
            curve_height = 1.4
            
            # Execute arc movement
            for i in range(steps + 1):
                progress = i / steps
                # Calculate arc position
                curve = math.sin(progress * math.pi) * curve_height
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress - curve * 50)  # Adjusted curve
                
                # Move mouse
                self.mouse.position = (current_x, current_y)
                time.sleep(duration / steps)
            
            # Release at target
            self.mouse.release(Button.left)
            time.sleep(0.02)
            
        except Exception as e:
            print(f"Swipe error: {e}")
            self.mouse.release(Button.left)  # Ensure mouse is released even if error occurs

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
            if basket_pos and isinstance(basket_pos, tuple) and len(basket_pos) == 2:
                # Debug print to see what positions we're getting
                print(f"Ball pos: {self.ball_pos}, Basket pos: {basket_pos}")
                
                # Add delay between shots
                time.sleep(self.shot_delay)
                
                # Get coordinates
                aim_x, aim_y = basket_pos
                ball_x, ball_y = self.ball_pos
                
                # Ensure we have valid coordinates before swiping
                if all(isinstance(x, (int, float)) for x in [aim_x, aim_y, ball_x, ball_y]):
                    self.shot_count += 1
                    print(f"Shot {self.shot_count}: Swiping from ({ball_x}, {ball_y}) to ({aim_x}, {aim_y})")
                    self.swipe(ball_x, ball_y, aim_x, aim_y)
                else:
                    print("Invalid coordinates detected")
            else:
                print("No valid basket position detected")
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
