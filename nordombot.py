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

def algorithm_3(door_stats, current_stage, current_run_doors):
    """Enhanced aggressive learning algorithm with success pattern recognition"""
    door_weights = {}
    
    # Initialize base weights from success rates
    for door_num in [1, 2, 3]:
        stats = door_stats[door_num]
        if stats['clicks'] == 0:
            door_weights[door_num] = 1
        else:
            # Calculate stage-specific success rate
            stage_success_rate = stats[f'stage_{current_stage}_success'] / stats[f'stage_{current_stage}_attempts'] if stats[f'stage_{current_stage}_attempts'] > 0 else 0
            overall_success_rate = stats['successes'] / stats['clicks']
            
            # Combine rates with higher emphasis on stage-specific performance
            door_weights[door_num] = (stage_success_rate * 0.8) + (overall_success_rate * 0.2)
            
            # Boost weight for doors that have led to higher stages
            for stage in range(current_stage + 1, 5):
                if stats[f'stage_{stage}_success'] > 0:
                    door_weights[door_num] *= 1.3
    
    # Pattern recognition boost
    if len(current_run_doors) >= 2:
        # If we have two successful doors in a row, favor that pattern
        if current_run_doors[-1] == current_run_doors[-2]:
            door_weights[current_run_doors[-1]] *= 1.5
    
    # Success streak handling
    if len(current_run_doors) > 0 and door_stats[current_run_doors[-1]]['successes'] > 0:
        last_door = current_run_doors[-1]
        success_rate = door_stats[last_door]['successes'] / door_stats[last_door]['clicks']
        if success_rate > 0.7:  # If door has >70% success rate
            door_weights[last_door] *= 1.4  # Increase chance to use it again
    
    # Ensure minimum weights
    door_weights = {k: max(0.2, v) for k, v in door_weights.items()}
    
    return door_weights

def click_random_door(door_stats, current_stage, current_run_doors, algorithm_num=3):
    if len(doors) != 3:
        return 0

    door_weights = algorithm_3(door_stats, current_stage, current_run_doors)
    
    # Convert weights to probabilities
    total_weight = sum(door_weights.values())
    door_probabilities = [door_weights[i] / total_weight for i in [1, 2, 3]]
    
    # Select door based on weighted probabilities
    door_num = random.choices([1, 2, 3], weights=door_probabilities)[0]
    door_pos = doors[door_num - 1]
    
    print(f"Door weights: {', '.join([f'Door #{i}: {door_weights[i]:.2f}' for i in [1, 2, 3]])}")
    click(door_pos[0], door_pos[1])
    return door_num

def play_game():
    global running
    attempts = 0
    current_stage = 1
    successful_runs = 0
    door_stats = {
        1: {'clicks': 0, 'successes': 0, 'stage_1_attempts': 0, 'stage_1_success': 0, 
            'stage_2_attempts': 0, 'stage_2_success': 0, 'stage_3_attempts': 0, 
            'stage_3_success': 0, 'stage_4_attempts': 0, 'stage_4_success': 0},
        2: {'clicks': 0, 'successes': 0, 'stage_1_attempts': 0, 'stage_1_success': 0, 
            'stage_2_attempts': 0, 'stage_2_success': 0, 'stage_3_attempts': 0, 
            'stage_3_success': 0, 'stage_4_attempts': 0, 'stage_4_success': 0},
        3: {'clicks': 0, 'successes': 0, 'stage_1_attempts': 0, 'stage_1_success': 0, 
            'stage_2_attempts': 0, 'stage_2_success': 0, 'stage_3_attempts': 0, 
            'stage_3_success': 0, 'stage_4_attempts': 0, 'stage_4_success': 0}
    }
    current_run_doors = []
    
    target = get_target_stage()
    print(f"\nBot will claim at stage {target}")
    print(f"Bot will use resume button when failing at stage {target}")
    time.sleep(2)
    
    while running:
        attempts += 1
        print(f"\nAttempt #{attempts} - Stage {current_stage}/{target} (Successful runs: {successful_runs})")
        
        # Update the door click to include current algorithm
        door_clicked = click_random_door(door_stats, current_stage, current_run_doors)
        door_stats[door_clicked]['clicks'] += 1
        door_stats[door_clicked][f'stage_{current_stage}_attempts'] += 1
        current_run_doors.append(door_clicked)
        print(f"Clicked Door #{door_clicked}")
        
        print("Waiting for result...")
        time.sleep(2)
        time.sleep(1)
        
        upcoming_found, _ = find_and_click_button('upcoming_stage', confidence=0.7, should_click=False)
        
        if upcoming_found:
            print(f"✅ Stage {current_stage} passed! (Using Door #{door_clicked})")
            door_stats[door_clicked]['successes'] += 1
            door_stats[door_clicked][f'stage_{current_stage}_success'] += 1
            
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
                
                # Handle failures at target stage differently
                if current_stage == target:
                    # Try resume up to 2 times
                    max_resume_attempts = 2
                    resume_attempts = 0
                    
                    while resume_attempts < max_resume_attempts:
                        resume_attempts += 1
                        print(f"Resume attempt {resume_attempts}/{max_resume_attempts} at stage {target}")
                        
                        # Click resume (same position as claim button)
                        click(claim_pos[0], claim_pos[1])
                        print("Clicked Resume to try again")
                        time.sleep(1)
                        
                        # Try another door
                        door_clicked = click_random_door(door_stats, current_stage, current_run_doors)
                        time.sleep(2)
                        
                        # Check if succeeded
                        upcoming_found, _ = find_and_click_button('upcoming_stage', confidence=0.7, should_click=False)
                        if upcoming_found:
                            print(f"✅ Stage {current_stage} passed after resume! (Using Door #{door_clicked})")
                            door_stats[door_clicked]['successes'] += 1
                            door_stats[door_clicked][f'stage_{current_stage}_success'] += 1
                            break
                        
                        # Check if failed again
                        failed_again, _ = find_and_click_button('failed_stage', confidence=0.7, should_click=False)
                        if failed_again and resume_attempts == max_resume_attempts:
                            print(f"Failed {max_resume_attempts} times after resume, clicking Go Back")
                            click(go_back_pos[0], go_back_pos[1])
                            current_stage = 1
                            current_run_doors = []
                            break
                        
                        time.sleep(1)
                    
                else:
                    # Handle failures for non-target stages as before
                    if current_stage == 1:
                        click(claim_pos[0], claim_pos[1])
                        print("Clicked First Stage Go Back")
                    else:
                        click(go_back_pos[0], go_back_pos[1])
                        print("Clicked Go Back")
                    current_stage = 1
                    current_run_doors = []
                
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