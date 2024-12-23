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

class BasketballBot:
    def __init__(self):
        self.ball_pos = None
        self.running = True
        self.paused = False
        self.mouse = Controller()
        self.shot_delay = 1.0  # Default delay between shots (1 second)

    def get_shot_delay(self):
        while True:
            try:
                delay = float(input("\nEnter delay between shots (0.1-2.0 seconds, default=1.0): "))
                if 0.1 <= delay <= 2.0:
                    return delay
                else:
                    print("Please enter a number between 0.1 and 2.0")
            except ValueError:
                print("Please enter a valid number")

    def swipe(self, start_x, start_y, end_x, end_y):
        """Perform swipe action with consistent speed but adjustable delay"""
        try:
            # Fixed swipe duration for consistency
            duration = 0.2
            
            self.mouse.position = (start_x, start_y)
            time.sleep(0.05)
            self.mouse.press(Button.left)
            
            steps = 15
            for i in range(steps):
                progress = i / steps
                curve = math.sin(progress * math.pi) * 2
                
                current_x = start_x + (end_x - start_x) * progress
                current_y = start_y + (end_y - start_y) * progress + curve
                
                self.mouse.position = (int(current_x), int(current_y))
                time.sleep(duration / steps)
            
            self.mouse.position = (end_x, end_y)
            time.sleep(0.05)
            self.mouse.release(Button.left)
            
            # Use configured delay between shots
            time.sleep(self.shot_delay)
            
        except Exception as e:
            print(f"Swipe error: {e}")

    def get_basket_position(self):
        """Find basket position using color detection"""
        try:
            screenshot = np.array(pyautogui.screenshot())
            
            # Define color ranges for basket detection
            # White rim
            white_lower = np.array([200, 200, 200])
            white_upper = np.array([255, 255, 255])
            
            # Blue background
            blue_lower = np.array([80, 120, 170])
            blue_upper = np.array([130, 170, 220])
            
            # Create masks
            white_mask = cv2.inRange(screenshot, white_lower, white_upper)
            blue_mask = cv2.inRange(screenshot, blue_lower, blue_upper)
            
            # Combine masks
            combined_mask = cv2.bitwise_or(white_mask, blue_mask)
            
            # Find contours
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find the largest contour in the upper half of the screen
                valid_contours = []
                height = screenshot.shape[0]
                for cnt in contours:
                    M = cv2.moments(cnt)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])
                        if cy < height/2:  # Only consider upper half of screen
                            valid_contours.append(cnt)
                
                if valid_contours:
                    largest_contour = max(valid_contours, key=cv2.contourArea)
                    M = cv2.moments(largest_contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        print(f"Found basket at: ({cx}, {cy})")
                        return (cx, cy)
            
            print("Basket not found")
            return None
            
        except Exception as e:
            print(f"Error finding basket: {e}")
            return None

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
                print("\nCalibration complete! Starting bot in 3 seconds...")
                root.after(3000, lambda: root.destroy())

        # Take screenshot
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
        """Main game loop"""
        try:
            # Find current basket position
            basket_pos = self.get_basket_position()
            if basket_pos:
                # Add offset to aim slightly higher (adjust these values)
                aim_x = basket_pos[0]
                aim_y = basket_pos[1] + 10  # Aim a bit lower than the detected position
                
                self.swipe(self.ball_pos[0], self.ball_pos[1], 
                          aim_x, aim_y)
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
    print("- Press 'S' to stop the bot")
    print("- Press 'K' to pause/resume")
    print("- Press 'ESC' to exit during calibration")
    
    # Get shot delay before starting
    bot.shot_delay = bot.get_shot_delay()
    print(f"\nShot delay set to: {bot.shot_delay} seconds")
    time.sleep(2)
    
    if not bot.calibrate():
        print("\nCalibration cancelled")
        return
    
    print("\nBot Started!")
    print("------------")
    
    while bot.running:
        try:
            if keyboard.is_pressed('s'):
                print("\nBot stopped by user")
                break
            
            if keyboard.is_pressed('k'):
                bot.paused = not bot.paused
                print(f"\nBot {'paused' if bot.paused else 'resumed'}")
                time.sleep(0.2)
            
            if not bot.paused:
                bot.play_game()
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"\nError occurred: {e}")
            time.sleep(1)
            continue
        
        except KeyboardInterrupt:
            print("\nBot stopped by user")
            break

if __name__ == "__main__":
    main()
