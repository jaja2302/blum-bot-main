import tkinter as tk
from PIL import ImageTk, Image, ImageDraw
import pyautogui
import time
import keyboard
import random
from pynput.mouse import Button, Controller

mouse = Controller()
doors = []  # Global variable to store door coordinates
go_back_pos = None   # Go Back button position (for stage 2-4)
claim_pos = None     # Claim/First Go Back button position
target_stage = 4     # Default target stage
running = True
paused = False

def get_target_stage():
    while True:
        try:
            stage = int(input("\nEnter target stage for claiming (1-10): "))
            if 1 <= stage <= 10:
                return stage
            else:
                print("Please enter a number between 1 and 10")
        except ValueError:
            print("Please enter a valid number")

def click(x, y):
    mouse.position = (x, y)
    time.sleep(0.1)
    mouse.press(Button.left)
    mouse.release(Button.left)
    time.sleep(0.5)

def find_and_click_button(image_name, confidence=0.8, should_click=True):
    try:
        button = pyautogui.locateOnScreen(f'{image_name}.png', confidence=confidence)
        if button:
            x, y = pyautogui.center(button)
            if should_click:
                click(x, y)
            return (True, (x, y))
        return (False, None)
    except Exception as e:
        return (False, None)

def click_random_door():
    if len(doors) == 3:
        door_num = random.randint(0, 2)
        door_pos = doors[door_num]
        click(door_pos[0], door_pos[1])
        return door_num + 1  # Return which door was clicked (1, 2, or 3)
    return 0

def play_game():
    global running
    attempts = 0
    current_stage = 1
    successful_runs = 0
    door_stats = {1: {'clicks': 0, 'successes': 0}, 
                 2: {'clicks': 0, 'successes': 0}, 
                 3: {'clicks': 0, 'successes': 0}}
    current_run_doors = []  # Track doors used in current run
    
    target = get_target_stage()
    print(f"\nBot will claim at stage {target}")
    time.sleep(2)
    
    while running:
        attempts += 1
        print(f"\nAttempt #{attempts} - Stage {current_stage}/{target} (Successful runs: {successful_runs})")
        
        # Click random door and track it
        door_clicked = click_random_door()
        door_stats[door_clicked]['clicks'] += 1
        current_run_doors.append(door_clicked)
        print(f"Clicked Door #{door_clicked}")
        
        print("Waiting for result...")
        time.sleep(2)
        time.sleep(1)
        
        upcoming_found, _ = find_and_click_button('upcoming_stage', confidence=0.7, should_click=False)
        
        if upcoming_found:
            print(f"✅ Stage {current_stage} passed! (Using Door #{door_clicked})")
            door_stats[door_clicked]['successes'] += 1
            
            if current_stage == target - 1:
                multiply_found, multiply_pos = find_and_click_button('multiply_button', confidence=0.7)
                if multiply_found:
                    current_stage += 1
                    print("🎯 Moving to final stage")
                    time.sleep(1)
            
            elif current_stage == target:
                print("🎉 Clicking claim button!")
                click(claim_pos[0], claim_pos[1])
                successful_runs += 1
                print(f"Claimed at stage {target}!")
                print(f"\n=== Current Statistics ===")
                print(f"Total attempts: {attempts}")
                print(f"Successful runs: {successful_runs}")
                print(f"Target stage: {target}")
                print(f"Success rate: {(successful_runs/attempts)*100:.2f}%")
                print("\nDoor Statistics:")
                for door, stats in door_stats.items():
                    success_rate = (stats['successes'] / stats['clicks'] * 100) if stats['clicks'] > 0 else 0
                    print(f"Door #{door}: {stats['clicks']} clicks, {stats['successes']} successes ({success_rate:.2f}% success rate)")
                print(f"\nWinning combination: {current_run_doors}")
                print(f"=======================")
                time.sleep(2)
                current_stage = 1
                current_run_doors = []  # Reset doors for new run
                continue
            
            else:
                multiply_found, _ = find_and_click_button('multiply_button', confidence=0.7)
                if multiply_found:
                    current_stage += 1
                    time.sleep(1)
        
        else:
            failed_found, _ = find_and_click_button('failed_stage', confidence=0.7, should_click=False)
            if failed_found:
                print(f"❌ Failed at stage {current_stage} (Using Door #{door_clicked})")
                if current_stage == 1:
                    click(claim_pos[0], claim_pos[1])
                    print("Clicked First Stage Go Back")
                else:
                    click(go_back_pos[0], go_back_pos[1])
                    print("Clicked Go Back")
                current_stage = 1
                current_run_doors = []  # Reset doors on failure
                time.sleep(1)
            time.sleep(1)
            continue

def calibrate():
    root = tk.Tk()
    root.title("Game Calibration")
    root.attributes('-topmost', True)
    
    def on_click(event):
        global doors, go_back_pos, claim_pos
        x = root.winfo_x() + event.x
        y = root.winfo_y() + event.y
        
        if len(doors) < 3:
            doors.append((x, y))
            # Draw a red dot for doors
            canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, fill='red')
            print(f"Door #{len(doors)} position saved: ({x}, {y})")
            
            if len(doors) == 3:
                print("\nNow click the Go Back button position (for stage 2-4)")
        
        elif not go_back_pos:
            go_back_pos = (x, y)
            # Draw a blue dot for Go Back
            canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, fill='blue')
            print(f"Go Back button position saved: ({x}, {y})")
            print("\nNow click the Claim/First Go Back button position")
        
        elif not claim_pos:
            claim_pos = (x, y)
            # Draw a green dot for Claim/First Go Back
            canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, fill='green')
            print(f"Claim/First Go Back position saved: ({x}, {y})")
            print("\nAll positions marked! Starting bot in 3 seconds...")
            root.after(3000, lambda: root.destroy())

    def reset_coordinates():
        global doors, go_back_pos, claim_pos
        doors = []
        go_back_pos = None
        claim_pos = None
        canvas.delete("all")
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        print("Coordinates reset. Click to mark positions again.")

    # Take screenshot
    screenshot = pyautogui.screenshot()
    photo = ImageTk.PhotoImage(screenshot)
    
    canvas = tk.Canvas(root, width=screenshot.width, height=screenshot.height)
    canvas.pack()
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.bind("<Button-1>", on_click)
    
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    reset_button = tk.Button(button_frame, text="Reset", command=reset_coordinates)
    reset_button.pack(side=tk.LEFT, padx=5)
    
    quit_button = tk.Button(button_frame, text="Quit", command=root.destroy)
    quit_button.pack(side=tk.LEFT, padx=5)
    
    root.bind('<Escape>', lambda e: root.destroy())
    
    print("Click on the center of each door (3 total)")
    root.mainloop()
    
    return len(doors) == 3 and go_back_pos and claim_pos

def main():
    global running, paused
    
    print("Nordom Gates Bot")
    print("---------------")
    print("Please make sure the game window is visible")
    print("Controls:")
    print("- Press 'S' to stop the bot")
    print("- Press 'K' to pause/resume")
    print("- Press 'ESC' to exit during calibration")
    time.sleep(2)
    
    if not calibrate():
        print("\nCalibration cancelled")
        return
    
    print("\nBot Started!")
    print("------------")
    
    while running:
        try:
            if keyboard.is_pressed('s'):
                print("\nBot stopped by user")
                break
            
            if keyboard.is_pressed('k'):
                paused = not paused
                print(f"\nBot {'paused' if paused else 'resumed'}")
                time.sleep(0.2)
            
            if not paused:
                play_game()
            
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