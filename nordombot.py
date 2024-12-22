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

def click_door(door_number):
    if 1 <= door_number <= 3 and len(doors) == 3:
        door_pos = doors[door_number - 1]  # Convert to 0-based index
        click(door_pos[0], door_pos[1])
        return True
    return False

def analyze_patterns(door_stats, winning_combinations):
    try:
        # Analyze door success rates
        door_success_rates = {}
        for door, stats in door_stats.items():
            success_rate = (stats['successes'] / stats['clicks'] * 100) if stats['clicks'] > 0 else 0
            door_success_rates[door] = success_rate
        
        # Analyze winning combinations
        stage_success = {1: {}, 2: {}, 3: {}}
        for combo in winning_combinations:
            for stage, door in enumerate(combo, 1):
                if door not in stage_success[stage]:
                    stage_success[stage][door] = 0
                stage_success[stage][door] += 1
        
        return door_success_rates, stage_success
    except Exception as e:
        print(f"Analysis error: {e}")
        return {1: 0, 2: 0, 3: 0}, {1: {}, 2: {}, 3: {}}

def get_smart_door(stage, door_stats, winning_combinations, learning_phase):
    if learning_phase:
        # During learning phase, use pure random
        return random.randint(1, 3)
    
    # After learning, use success rates to make smarter choices
    door_success_rates, stage_success = analyze_patterns(door_stats, winning_combinations)
    
    # Get best door for current stage
    stage_doors = stage_success.get(stage, {})
    if stage_doors:
        best_doors = [door for door, count in stage_doors.items() 
                     if count == max(stage_doors.values())]
        return random.choice(best_doors)
    
    # Fallback to overall best performing door
    best_doors = [door for door, rate in door_success_rates.items() 
                 if rate == max(door_success_rates.values())]
    return random.choice(best_doors)

def play_game():
    global running
    attempts = 0
    total_attempts = 0
    current_stage = 1
    successful_runs = 0
    door_stats = {1: {'clicks': 0, 'successes': 0}, 
                 2: {'clicks': 0, 'successes': 0}, 
                 3: {'clicks': 0, 'successes': 0}}
    winning_combinations = []
    current_run_doors = []
    learning_phase = True
    learning_attempts = 30
    best_pattern = None
    
    target = get_target_stage()
    print(f"\nBot will claim at stage {target}")
    print("Starting Learning Phase")
    time.sleep(2)
    
    while running:
        attempts += 1
        total_attempts += 1
        
        # Check if we need to switch phases
        if attempts >= learning_attempts:
            success_rate = (successful_runs / attempts) * 100
            print(f"\n=== Phase Complete ===")
            print(f"Success Rate: {success_rate:.2f}%")
            
            if success_rate >= 50:
                print("Found successful pattern! Continuing with best doors.")
                print(f"Best pattern found: {winning_combinations[-1]}")
                learning_phase = False
                best_pattern = winning_combinations[-1] if winning_combinations else None
            else:
                print("Success rate too low. Starting new learning phase.")
                learning_phase = True
                door_stats = {1: {'clicks': 0, 'successes': 0}, 
                            2: {'clicks': 0, 'successes': 0}, 
                            3: {'clicks': 0, 'successes': 0}}
                winning_combinations = []
            
            attempts = 0
            successful_runs = 0
        
        print(f"\nAttempt #{total_attempts} - Stage {current_stage}/{target}")
        print(f"Phase: {'Learning' if learning_phase else 'Using Best Pattern'}")
        
        # Choose door
        if not learning_phase and best_pattern and current_stage <= len(best_pattern):
            door_clicked = best_pattern[current_stage - 1]
        else:
            door_clicked = random.randint(1, 3)
        
        print(f"Selecting Door #{door_clicked}")
        time.sleep(2)  # Delay before clicking
            
        if click_door(door_clicked):
            door_stats[door_clicked]['clicks'] += 1
            current_run_doors.append(door_clicked)
            print(f"Clicked Door #{door_clicked}")
        else:
            print("Error clicking door! Retrying...")
            time.sleep(2)
            if click_door(door_clicked):
                door_stats[door_clicked]['clicks'] += 1
                current_run_doors.append(door_clicked)
                print(f"Successfully clicked Door #{door_clicked} on retry")
            else:
                print("Failed to click door twice, continuing...")
                continue
        
        print("Waiting for result...")
        time.sleep(2)  # Wait for door animation
        time.sleep(1)  # Wait for status
        
        upcoming_found, _ = find_and_click_button('upcoming_stage', confidence=0.7, should_click=False)
        
        if upcoming_found:
            print(f"✅ Stage {current_stage} passed! (Using Door #{door_clicked})")
            door_stats[door_clicked]['successes'] += 1
            
            if current_stage == target - 1:
                multiply_found, multiply_pos = find_and_click_button('multiply_button', confidence=0.7)
                if multiply_found:
                    current_stage += 1
                    print("🎯 Moving to final stage")
                    time.sleep(2)  # Extra delay before final stage
            
            elif current_stage == target:
                print("🎉 Clicking claim button!")
                time.sleep(1)  # Delay before claiming
                click(claim_pos[0], claim_pos[1])
                successful_runs += 1
                winning_combinations.append(current_run_doors.copy())
                
                print(f"\n=== Current Statistics ===")
                print(f"Total attempts in this phase: {attempts}")
                print(f"Successful runs: {successful_runs}")
                print(f"Current success rate: {(successful_runs/attempts)*100:.2f}%")
                print("\nDoor Statistics:")
                for door, stats in door_stats.items():
                    success_rate = (stats['successes'] / stats['clicks'] * 100) if stats['clicks'] > 0 else 0
                    print(f"Door #{door}: {stats['clicks']} clicks, {stats['successes']} successes ({success_rate:.2f}%)")
                print(f"\nWinning combination: {current_run_doors}")
                print("=======================")
                
                time.sleep(2)
                current_stage = 1
                current_run_doors = []
                continue
            
            else:
                multiply_found, _ = find_and_click_button('multiply_button', confidence=0.7)
                if multiply_found:
                    current_stage += 1
                    time.sleep(2)  # Extra delay between stages
        
        else:
            failed_found, _ = find_and_click_button('failed_stage', confidence=0.7, should_click=False)
            if failed_found:
                print(f"❌ Failed at stage {current_stage} (Using Door #{door_clicked})")
                time.sleep(1)  # Delay before clicking back
                if current_stage == 1:
                    click(claim_pos[0], claim_pos[1])
                    print("Clicked First Stage Go Back")
                else:
                    click(go_back_pos[0], go_back_pos[1])
                    print("Clicked Go Back")
                current_stage = 1
                current_run_doors = []
                time.sleep(2)  # Extra delay after going back
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