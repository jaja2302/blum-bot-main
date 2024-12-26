import win32gui
import win32con
import time
from screen_capture import ScreenCapture
from ai_hoop_detector import HoopDetector
from ai_ball_controller import BallController
from ai_rl_agent import RLAgent

class PiggyBallAI:
    def __init__(self):
        self.window_detector = WindowDetector()
        self.screen_capture = ScreenCapture()
        self.hoop_detector = HoopDetector()
        self.ball_controller = BallController()
        self.rl_agent = RLAgent()
        
    def find_telegram_window(self):
        # Find Telegram window
        telegram_hwnd = self.window_detector.find_window("Telegram")
        if telegram_hwnd:
            # Bring window to front
            win32gui.ShowWindow(telegram_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(telegram_hwnd)
            return telegram_hwnd
        return None

    def run(self):
        print("Starting Piggy Ball AI...")
        
        # Find and focus Telegram window
        telegram_hwnd = self.find_telegram_window()
        if not telegram_hwnd:
            print("Could not find Telegram window!")
            return

        # Set the game region
        self.screen_capture.set_game_region((100, 100, 500, 700))

        try:
            while True:
                # Capture game screen
                game_screen = self.screen_capture.get_game_screen(telegram_hwnd)
                
                # Detect hoop position
                hoop_pos = self.hoop_detector.detect_hoop(game_screen)
                
                if hoop_pos:
                    # Get action from RL agent
                    action = self.rl_agent.get_action(game_screen, hoop_pos)
                    
                    # Execute action using ball controller
                    self.ball_controller.execute_action(action)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Stopping Piggy Ball AI...")

if __name__ == "__main__":
    ai = PiggyBallAI()
    ai.run()
