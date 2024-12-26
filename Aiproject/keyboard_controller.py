import keyboard
import time
import sys

class KeyboardController:
    def __init__(self):
        self.is_running = True
        self.is_paused = False
        
        # Set up keyboard event handlers
        keyboard.on_press_key('s', lambda _: self.stop_program())
        keyboard.on_press_key('esc', lambda _: self.stop_program())
        keyboard.on_press_key('p', lambda _: self.toggle_pause())
        keyboard.on_press_key('r', lambda _: self.toggle_pause())

    def stop_program(self):
        """Immediately stop the program"""
        print("\nMenghentikan program...")
        self.is_running = False
        sys.exit(0)  # Force exit

    def toggle_pause(self):
        """Toggle pause state"""
        self.is_paused = not self.is_paused
        print("\nProgram di-pause..." if self.is_paused else "\nMelanjutkan program...")

    def is_stopped(self):
        """Check if program should stop"""
        return not self.is_running

    def is_game_paused(self):
        return self.is_paused 