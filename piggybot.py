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
        self.shot_delay = 1.0
        self.basket_history = []
        self.history_max = 3
        self.last_detection_time = None
        self.mode = None  # For storing current mode

    def get_mode(self):
        while True:
            print("\nSelect mode:")
            print("1. Daily (0.5s delay)")
            print("2. Matching (0.01s delay)")
            try:
                choice = input("Enter choice (1 or 2): ")
                if choice == '1':
                    self.shot_delay = 0.5
                    self.mode = 'daily'
                    print("\nDaily mode selected (0.5s delay)")
                    return
                elif choice == '2':
                    self.shot_delay = 0.01
                    self.mode = 'matching'
                    print("\nMatching mode selected (0.01s delay)")
                    return
                else:
                    print("Please enter 1 or 2")
            except ValueError:
                print("Invalid input")

    def swipe(self, start_x, start_y, end_x, end_y):
        """Perform ultra-fast swipe action with minimal delays"""
        try:
            # Ultra-fast swipe duration
            duration = 0.05  # Reduced to 0.05s
            
            self.mouse.position = (start_x, start_y)
            time.sleep(0.01)  # Minimum practical delay
            self.mouse.press(Button.left)
            
            # Minimal steps for maximum speed
            steps = 5  # Reduced to 5 steps
            for i in range(steps):
                progress = i / steps
                curve = math.sin(progress * math.pi)  # Reduced curve
                
                current_x = start_x + (end_x - start_x) * progress
                current_y = start_y + (end_y - start_y) * progress + curve
                
                self.mouse.position = (int(current_x), int(current_y))
                time.sleep(duration / steps)
            
            self.mouse.position = (end_x, end_y)
            time.sleep(0.01)
            self.mouse.release(Button.left)
            
            # Absolute minimum delay between shots
            time.sleep(max(0.01, self.shot_delay))  # Won't go lower than 0.01s
            
        except Exception as e:
            print(f"Swipe error: {e}")

    def get_basket_position(self):
        """Find basket position using color detection with movement prediction"""
        try:
            screenshot = np.array(pyautogui.screenshot())
            current_time = time.time()
            
            # Define color ranges for basket detection
            white_lower = np.array([200, 200, 200])
            white_upper = np.array([255, 255, 255])
            blue_lower = np.array([80, 120, 170])
            blue_upper = np.array([130, 170, 220])
            
            white_mask = cv2.inRange(screenshot, white_lower, white_upper)
            blue_mask = cv2.inRange(screenshot, blue_lower, blue_upper)
            combined_mask = cv2.bitwise_or(white_mask, blue_mask)
            
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                valid_contours = []
                height = screenshot.shape[0]
                for cnt in contours:
                    M = cv2.moments(cnt)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])
                        if cy < height/2:
                            valid_contours.append(cnt)
                
                if valid_contours:
                    largest_contour = max(valid_contours, key=cv2.contourArea)
                    M = cv2.moments(largest_contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        # Store position with timestamp
                        self.basket_history.append((cx, cy, current_time))
                        if len(self.basket_history) > self.history_max:
                            self.basket_history.pop(0)
                        
                        # Predict movement if we have enough history
                        if len(self.basket_history) >= 2:
                            # Calculate velocity from last two positions
                            prev_x, prev_y, prev_time = self.basket_history[-2]
                            dt = current_time - prev_time
                            if dt > 0:
                                dx = (cx - prev_x) / dt
                                dy = (cy - prev_y) / dt
                                
                                # Predict position after 0.2s (typical shot time)
                                predict_time = 0.2
                                predicted_x = int(cx + dx * predict_time)
                                predicted_y = int(cy + dy * predict_time)
                                
                                print(f"Current: ({cx}, {cy}), Predicted: ({predicted_x}, {predicted_y})")
                                return (predicted_x, predicted_y)
                        
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
        """Main game loop with improved aiming"""
        try:
            basket_pos = self.get_basket_position()
            if basket_pos:
                # Add small random variation to make shots more natural
                aim_x = basket_pos[0] + random.randint(-2, 2)
                aim_y = basket_pos[1] + random.randint(-2, 2)
                
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
    print("- Press 'S' to stop the bot")
    print("- Press 'K' to pause/resume")
    print("- Press 'R' to return to mode selection")
    print("- Press 'ESC' to exit during calibration")
    
    while True:
        bot.get_mode()
        time.sleep(1)
        
        if not bot.calibrate():
            print("\nCalibration cancelled")
            continue
        
        print(f"\nBot Started in {bot.mode.upper()} mode!")
        print("------------")
        
        while bot.running:
            try:
                if keyboard.is_pressed('s'):
                    print("\nBot stopped by user")
                    bot.running = False
                    break
                
                if keyboard.is_pressed('k'):
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
