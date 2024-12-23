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
        self.history_max = 5
        self.last_detection_time = None
        self.mode = None  # For storing current mode
        self.movement_log = []  # Added back to fix error

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
        """Perform swipe action with mode-specific speed"""
        try:
            # Different timing for each mode
            if self.mode == 'matching':
                duration = 0.08  # Ultra fast for matching
                steps = 8       # Fewer steps for speed
                wait_start = 0.02
                wait_end = 0.02
                curve_height = 1.5
            else:  # daily mode
                duration = 0.2   # Normal speed for daily
                steps = 15      # More steps for smoothness
                wait_start = 0.05
                wait_end = 0.05
                curve_height = 2
            
            self.mouse.position = (start_x, start_y)
            time.sleep(wait_start)
            self.mouse.press(Button.left)
            
            for i in range(steps):
                progress = i / steps
                curve = math.sin(progress * math.pi) * curve_height
                
                current_x = start_x + (end_x - start_x) * progress
                current_y = start_y + (end_y - start_y) * progress + curve
                
                self.mouse.position = (int(current_x), int(current_y))
                time.sleep(duration / steps)
            
            self.mouse.position = (end_x, end_y)
            time.sleep(wait_end)
            self.mouse.release(Button.left)
            
            # Ultra minimal delay for matching mode
            if self.mode == 'matching':
                time.sleep(max(0.01, self.shot_delay))  # As fast as possible
            else:
                time.sleep(max(0.05, self.shot_delay))  # Normal daily delay
            
        except Exception as e:
            print(f"Swipe error: {e}")

    def get_basket_position(self):
        """Find basket position using red rim color detection"""
        try:
            screenshot = np.array(pyautogui.screenshot())
            current_time = time.time()
            
            # BGR format for OpenCV
            # For #cc0c04 (RGB: 204, 12, 4)
            # In BGR: 4, 12, 204
            red_lower = np.array([0, 0, 180])    # BGR format
            red_upper = np.array([10, 20, 255])  # BGR format
            
            # Create mask for red rim
            red_mask = cv2.inRange(cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR), red_lower, red_upper)
            
            # Add some morphological operations to clean up the mask
            kernel = np.ones((3,3), np.uint8)
            red_mask = cv2.dilate(red_mask, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            print(f"Found {len(contours)} contours")  # Debug print
            
            if contours:
                valid_contours = []
                height = screenshot.shape[0]
                for cnt in contours:
                    M = cv2.moments(cnt)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])
                        if cy < height/2:  # Only consider upper half of screen
                            valid_contours.append(cnt)
                
                print(f"Found {len(valid_contours)} valid contours")  # Debug print
                
                if valid_contours:
                    largest_contour = max(valid_contours, key=cv2.contourArea)
                    M = cv2.moments(largest_contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        print(f"Found basket at: ({cx}, {cy})")  # Debug print
                        
                        # Store position for prediction
                        self.basket_history.append((cx, cy, current_time))
                        if len(self.basket_history) > self.history_max:
                            self.basket_history.pop(0)
                        
                        if len(self.basket_history) >= 3:
                            velocities = []
                            weights = [0.5, 0.7, 1.0]
                            
                            for i in range(1, len(self.basket_history)):
                                prev_x, prev_y, prev_time = self.basket_history[i-1]
                                curr_x, curr_y, curr_time = self.basket_history[i]
                                dt = curr_time - prev_time
                                if dt > 0:
                                    dx = (curr_x - prev_x) / dt
                                    dy = (curr_y - prev_y) / dt
                                    weight = weights[min(i-1, len(weights)-1)]
                                    velocities.append((dx * weight, dy * weight))
                            
                            if velocities:
                                total_weight = sum(weights[:len(velocities)])
                                avg_dx = sum(v[0] for v in velocities) / total_weight
                                avg_dy = sum(v[1] for v in velocities) / total_weight
                                
                                predict_time = 0.12
                                predicted_x = int(cx + avg_dx * predict_time)
                                predicted_y = int(cy + avg_dy * predict_time)
                                
                                if abs(avg_dx) > 1:
                                    direction_correction = int(3 * math.copysign(1, avg_dx))
                                    predicted_x += direction_correction
                                
                                predicted_y -= 2
                                
                                print(f"Predicted position: ({predicted_x}, {predicted_y})")  # Debug print
                                return (predicted_x, predicted_y)
                        
                        return (cx, cy)
            
            print("No basket found")  # Debug print
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
        """Main game loop with enhanced aiming"""
        try:
            basket_pos = self.get_basket_position()
            if basket_pos:
                # Dynamic aim variation based on movement
                if len(self.basket_history) >= 2:
                    _, _, prev_time = self.basket_history[-2]
                    _, _, curr_time = self.basket_history[-1]
                    if curr_time - prev_time > 0:
                        movement_speed = abs(basket_pos[0] - self.basket_history[-2][0]) / (curr_time - prev_time)
                        # Reduce variation when basket is moving faster
                        variation = max(1, 3 - int(movement_speed * 0.1))
                    else:
                        variation = 2
                else:
                    variation = 2
                    
                aim_x = basket_pos[0] + random.randint(-variation, variation)
                aim_y = basket_pos[1] + random.randint(-1, 1)  # Keep vertical variation minimal
                
                self.swipe(self.ball_pos[0], self.ball_pos[1], aim_x, aim_y)
            else:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Game error: {e}")
            time.sleep(0.1)

    def save_movement_log(self):
        """Save movement log to file"""
        if self.movement_log:
            with open('basket_movement.txt', 'w') as f:
                for x, y, t in self.movement_log:
                    f.write(f"{x},{y},{t}\n")
            print("\nMovement log saved to basket_movement.txt")

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
                    bot.save_movement_log()  # Save log when stopping
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
