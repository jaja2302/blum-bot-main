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
            print("2. Matching (Ultra-fast)")
            try:
                choice = input("Enter choice (1 or 2): ")
                if choice == '1':
                    self.shot_delay = 0.5
                    self.mode = 'daily'
                    print("\nDaily mode selected (0.5s delay)")
                    return
                elif choice == '2':
                    self.shot_delay = 0.005  # Ultra minimal delay
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
            basket_speed = 0
            if len(self.basket_history) >= 2:
                prev_x = self.basket_history[-2][0]
                curr_x = self.basket_history[-1][0]
                basket_speed = abs(curr_x - prev_x)

            # Adaptive settings based on basket movement
            if self.mode == 'matching':
                if basket_speed > 5:  # Moving basket
                    duration = 0.06    # Slightly slower than before
                    steps = 6 
                    wait_start = 0.015
                    wait_end = 0.015
                    curve_height = 1.2
                else:  # Stationary or slow-moving basket
                    duration = 0.08    # More controlled for accuracy
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
                    time.sleep(0.01)   # Slightly longer delay
                else:
                    time.sleep(0.015)  # More controlled timing
            else:
                time.sleep(max(0.05, self.shot_delay))
            
        except Exception as e:
            print(f"Swipe error: {e}")

    def get_basket_position(self):
        """Find basket position using red rim color detection with 3D movement prediction"""
        try:
            screenshot = np.array(pyautogui.screenshot())
            current_time = time.time()
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            red_lower = np.array([0, 0, 180])
            red_upper = np.array([10, 20, 255])
            
            red_mask = cv2.inRange(cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR), red_lower, red_upper)
            kernel = np.ones((3,3), np.uint8)
            red_mask = cv2.dilate(red_mask, kernel, iterations=1)
            
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                valid_contours = []
                for cnt in contours:
                    M = cv2.moments(cnt)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])
                        if cy < screen_height/2:
                            valid_contours.append(cnt)
                
                if valid_contours:
                    largest_contour = max(valid_contours, key=cv2.contourArea)
                    M = cv2.moments(largest_contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        self.basket_history.append((cx, cy, current_time))
                        if len(self.basket_history) > self.history_max:
                            self.basket_history.pop(0)
                        
                        if len(self.basket_history) >= 3:
                            # Analyze movement patterns
                            horizontal_pattern = "none"  # left-to-right, right-to-left, none
                            vertical_pattern = "none"    # up-to-down, down-to-up, none
                            
                            # Calculate velocities with enhanced vertical movement detection
                            velocities = []
                            weights = [0.3, 0.5, 0.7, 1.0]
                            
                            for i in range(1, len(self.basket_history)):
                                prev_x, prev_y, prev_time = self.basket_history[i-1]
                                curr_x, curr_y, curr_time = self.basket_history[i]
                                dt = curr_time - prev_time
                                if dt > 0:
                                    dx = (curr_x - prev_x) / dt
                                    dy = (curr_y - prev_y) / dt
                                    weight = weights[min(i-1, len(weights)-1)]
                                    velocities.append((dx * weight, dy * weight))
                                    
                                    # Detect movement patterns
                                    if abs(dx) > abs(dy):  # Primarily horizontal movement
                                        if dx > 0:
                                            horizontal_pattern = "left-to-right"
                                        else:
                                            horizontal_pattern = "right-to-left"
                                    else:  # Primarily vertical movement
                                        if dy > 0:
                                            vertical_pattern = "up-to-down"
                                        else:
                                            vertical_pattern = "down-to-up"
                            
                            if velocities:
                                total_weight = sum(weights[:len(velocities)])
                                avg_dx = sum(v[0] for v in velocities) / total_weight
                                avg_dy = sum(v[1] for v in velocities) / total_weight
                                
                                # Calculate overall speed and directions
                                horizontal_speed = abs(avg_dx)
                                vertical_speed = abs(avg_dy)
                                horizontal_direction = math.copysign(1, avg_dx)
                                vertical_direction = math.copysign(1, avg_dy)
                                
                                # Base prediction time
                                predict_time = 0.15
                                
                                # Position-based prediction adjustments
                                if cx < screen_width * 0.2 or cx > screen_width * 0.8:  # Near edges
                                    predict_time = 0.18
                                
                                # Calculate predicted position
                                predicted_x = int(cx + avg_dx * predict_time)
                                predicted_y = int(cy + avg_dy * predict_time)
                                
                                # Enhanced diagonal movement prediction
                                if abs(avg_dx) > 50 and abs(avg_dy) > 30:  # Significant diagonal movement
                                    diagonal_speed = math.sqrt(horizontal_speed**2 + vertical_speed**2)
                                    if diagonal_speed > 150:  # Fast diagonal
                                        predicted_x += int(horizontal_direction * 15)
                                        predicted_y += int(vertical_direction * 8)
                                    elif diagonal_speed > 100:  # Medium diagonal
                                        predicted_x += int(horizontal_direction * 12)
                                        predicted_y += int(vertical_direction * 6)
                                    else:  # Slow diagonal
                                        predicted_x += int(horizontal_direction * 8)
                                        predicted_y += int(vertical_direction * 4)
                                else:  # Pure horizontal/vertical movement
                                    if horizontal_speed > 150:
                                        predicted_x += int(horizontal_direction * 15)
                                    elif horizontal_speed > 100:
                                        predicted_x += int(horizontal_direction * 12)
                                    elif horizontal_speed > 50:
                                        predicted_x += int(horizontal_direction * 8)
                                    
                                    if vertical_speed > 50:
                                        predicted_y += int(vertical_direction * 6)
                                    elif vertical_speed > 30:
                                        predicted_y += int(vertical_direction * 4)
                                
                                # Pattern-based corrections
                                if horizontal_pattern == "left-to-right":
                                    predicted_x += 5
                                elif horizontal_pattern == "right-to-left":
                                    predicted_x -= 5
                                    
                                if vertical_pattern == "up-to-down":
                                    predicted_y += 3
                                elif vertical_pattern == "down-to-up":
                                    predicted_y -= 3
                                
                                # Final height adjustment
                                height_correction = min(6, int(math.sqrt(horizontal_speed**2 + vertical_speed**2) * 0.04))
                                predicted_y -= height_correction
                                
                                return (predicted_x, predicted_y)
                        
                        return (cx, cy)
            
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
