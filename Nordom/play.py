import time
import random
import pyautogui
from pynput.mouse import Button, Controller

class GamePlayer:
    def __init__(self, calibration_data):
        self.mouse = Controller()
        self.doors = calibration_data['doors']
        self.go_back_pos = calibration_data['go_back_pos']
        self.claim_pos = calibration_data['claim_pos']
        self.reset_stats()  # Pindahkan inisialisasi stats ke fungsi terpisah
        self.force_stop = False
    
    def reset_stats(self):
        """Reset semua statistik ke kondisi awal"""
        self.attempts = 0
        self.successful_runs = 0
        self.current_stage = 1
        self.target_stage = 4
        self.is_paused = False
        # Inisialisasi door_stats langsung
        self.door_stats = self.initialize_door_stats(self.target_stage)
        self.current_run_doors = []
    
    def click(self, x, y):
        """Click at exact coordinates"""
        try:
            self.log(f"Clicking at: ({x}, {y})")
            self.mouse.position = (x, y)
            time.sleep(0.1)
            # Verifikasi posisi mouse
            current_x, current_y = self.mouse.position
            if abs(current_x - x) > 2 or abs(current_y - y) > 2:
                self.log(f"Warning: Mouse position mismatch. Expected: ({x}, {y}), Got: ({current_x}, {current_y})")
            
            self.mouse.press(Button.left)
            time.sleep(0.1)
            self.mouse.release(Button.left)
            time.sleep(0.5)
        except Exception as e:
            self.log(f"Error clicking: {e}")
    
    def find_and_click_button(self, image_name, confidence=0.8, should_click=True):
        try:
            button = pyautogui.locateOnScreen(f'{image_name}.png', confidence=confidence)
            if button:
                x, y = pyautogui.center(button)
                if should_click:
                    self.click(x, y)
                return (True, (x, y))
            return (False, None)
        except Exception as e:
            return (False, None)
    
    def set_target_stage(self, stage):
        """Set target stage for claiming"""
        if 1 <= stage <= 10:
            self.target_stage = stage
    
    def initialize_door_stats(self, target):
        stats = {}
        for door in [1, 2, 3]:
            stats[door] = {
                'clicks': 0,
                'successes': 0
            }
            for stage in range(1, target + 1):
                stats[door][f'stage_{stage}_attempts'] = 0
                stats[door][f'stage_{stage}_success'] = 0
        return stats
    
    def algorithm_3(self, current_stage):
        """Enhanced aggressive learning algorithm with success pattern recognition"""
        door_weights = {}
        
        # Initialize base weights from success rates
        for door_num in [1, 2, 3]:
            stats = self.door_stats[door_num]
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
        if len(self.current_run_doors) >= 2:
            # If we have two successful doors in a row, favor that pattern
            if self.current_run_doors[-1] == self.current_run_doors[-2]:
                door_weights[self.current_run_doors[-1]] *= 1.5
        
        # Ensure minimum weights
        door_weights = {k: max(0.2, v) for k, v in door_weights.items()}
        
        return door_weights
    
    def click_random_door(self):
        """Click random door based on weights"""
        if len(self.doors) != 3:
            self.log("Error: Invalid number of doors")
            return 0

        try:
            door_weights = self.algorithm_3(self.current_stage)
            
            # Convert weights to probabilities
            total_weight = sum(door_weights.values())
            door_probabilities = [door_weights[i] / total_weight for i in [1, 2, 3]]
            
            # Select door based on weighted probabilities
            door_num = random.choices([1, 2, 3], weights=door_probabilities)[0]
            door_pos = self.doors[door_num - 1]
            
            self.log(f"Door weights: {', '.join([f'Door #{i}: {door_weights[i]:.2f}' for i in [1, 2, 3]])}")
            self.click(door_pos[0], door_pos[1])
            return door_num
        except Exception as e:
            self.log(f"Error in click_random_door: {e}")
            return 0
    
    def handle_stage_success(self, door_clicked, current_stage, target):
        print(f"✅ Stage {current_stage} passed! (Using Door #{door_clicked})")
        self.door_stats[door_clicked]['successes'] += 1
        self.door_stats[door_clicked][f'stage_{current_stage}_success'] += 1
        
        if current_stage == target - 1:
            multiply_found, _ = self.find_and_click_button('multiply_button', confidence=0.7)
            if multiply_found:
                return current_stage + 1
        
        elif current_stage == target:
            print("🎉 Clicking claim button!")
            self.click(self.claim_pos[0], self.claim_pos[1])
            self.successful_runs += 1
            self.print_statistics(target)
            time.sleep(2)
            return 1  # Reset to stage 1
        
        else:
            multiply_found, _ = self.find_and_click_button('multiply_button', confidence=0.7)
            if multiply_found:
                return current_stage + 1
        
        return current_stage
    
    def handle_stage_failure(self, door_clicked, current_stage, target):
        print(f"❌ Failed at stage {current_stage} (Using Door #{door_clicked})")
        
        if current_stage == target:
            max_resume_attempts = 2
            resume_attempts = 0
            
            while resume_attempts < max_resume_attempts:
                resume_attempts += 1
                print(f"Resume attempt {resume_attempts}/{max_resume_attempts} at stage {target}")
                
                self.click(self.claim_pos[0], self.claim_pos[1])
                print("Clicked Resume to try again")
                time.sleep(1)
                
                door_clicked = self.click_random_door()
                time.sleep(2)
                
                upcoming_found, _ = self.find_and_click_button('upcoming_stage', confidence=0.7, should_click=False)
                if upcoming_found:
                    print(f"✅ Stage {current_stage} passed after resume! (Using Door #{door_clicked})")
                    self.door_stats[door_clicked]['successes'] += 1
                    self.door_stats[door_clicked][f'stage_{current_stage}_success'] += 1
                    return current_stage
                
                failed_again, _ = self.find_and_click_button('failed_stage', confidence=0.7, should_click=False)
                if failed_again and resume_attempts == max_resume_attempts:
                    print(f"Failed {max_resume_attempts} times after resume, clicking Go Back")
                    self.click(self.go_back_pos[0], self.go_back_pos[1])
                    return 1  # Reset to stage 1
                
                time.sleep(1)
        else:
            if current_stage == 1:
                self.click(self.claim_pos[0], self.claim_pos[1])
                print("Clicked First Stage Go Back")
            else:
                self.click(self.go_back_pos[0], self.go_back_pos[1])
                print("Clicked Go Back")
            return 1  # Reset to stage 1
    
    def print_statistics(self, target):
        print(f"\n=== Current Statistics ===")
        print(f"Total attempts: {self.attempts}")
        print(f"Successful runs: {self.successful_runs}")
        print(f"Target stage: {target}")
        print(f"Success rate: {(self.successful_runs/self.attempts)*100:.2f}%")
        print("\nDoor Statistics:")
        for door, stats in self.door_stats.items():
            success_rate = (stats['successes'] / stats['clicks'] * 100) if stats['clicks'] > 0 else 0
            print(f"Door #{door}: {stats['clicks']} clicks, {stats['successes']} successes ({success_rate:.2f}% success rate)")
        print(f"\nWinning combination: {self.current_run_doors}")
        print(f"=======================")
    
    def set_pause(self, paused):
        """Set pause status"""
        self.is_paused = paused
    
    def set_force_stop(self, force_stop):
        self.force_stop = force_stop
    
    def play_game(self):
        """Main game loop"""
        self.door_stats = self.initialize_door_stats(self.target_stage)
        self.current_stage = 1
        self.current_run_doors = []
        
        self.log(f"\nBot will claim at stage {self.target_stage}")
        self.log(f"Bot will use resume button when failing at stage {self.target_stage}")
        
        time.sleep(2)
        
        while True:
            if self.force_stop:  # Check force stop
                return
                
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            self.attempts += 1
            self.log(f"\nAttempt #{self.attempts} - Stage {self.current_stage}/{self.target_stage}")
            
            # Click door and update stats
            door_clicked = self.click_random_door()
            if door_clicked == 0:  # Handle error case
                self.log("Error: Invalid door configuration")
                return
                
            if self.is_paused:
                continue
                
            self.door_stats[door_clicked]['clicks'] += 1
            self.door_stats[door_clicked][f'stage_{self.current_stage}_attempts'] += 1
            self.current_run_doors.append(door_clicked)
            
            time.sleep(2)
            if self.is_paused:
                continue
            
            # Check result
            upcoming_found, _ = self.find_and_click_button('upcoming_stage', confidence=0.7, should_click=False)
            if self.is_paused:
                continue
                
            if upcoming_found:
                self.current_stage = self.handle_stage_success(door_clicked, self.current_stage, self.target_stage)
            else:
                failed_found, _ = self.find_and_click_button('failed_stage', confidence=0.7, should_click=False)
                if failed_found:
                    self.current_stage = self.handle_stage_failure(door_clicked, self.current_stage, self.target_stage)
                    self.current_run_doors = []
            
            if self.is_paused:
                continue
                
            time.sleep(1)
            
            if self.force_stop:
                return
    
    def set_logger(self, logger_func):
        self.logger = logger_func

    def log(self, message):
        if hasattr(self, 'logger'):
            self.logger(message)
        else:
            print(message) 