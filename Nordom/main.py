import tkinter as tk
from PIL import ImageTk
import pyautogui
import keyboard
import time
import threading
from play import GamePlayer
from calibration import Calibrator

class BotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Nordom Gates Bot")
        self.root.geometry("400x500")
        
        self.reset_state()  # Reset state awal
        self.create_new_calibrator()  # Buat calibrator pertama
        self.setup_gui()
        
    def reset_state(self):
        """Reset semua state ke kondisi awal"""
        self.running = False
        self.paused = False
        self.force_stop = False  # Tambah flag untuk force stop
        self.player = None
        self.calibration_data = None
        self.calibrator = None
        self.bot_thread = None
        
    def create_new_calibrator(self):
        """Buat instance calibrator baru"""
        self.calibrator = Calibrator()
        self.calibrator.set_callback(self.on_calibration_complete)

    def setup_gui(self):
        # Status Frame
        status_frame = tk.LabelFrame(self.root, text="Status", padx=10, pady=5)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = tk.Label(status_frame, text="Not Running", font=("Arial", 12))
        self.status_label.pack()
        
        # Target Stage Frame
        target_frame = tk.LabelFrame(self.root, text="Target Stage", padx=10, pady=5)
        target_frame.pack(fill="x", padx=10, pady=5)
        
        # Spinbox untuk target stage
        self.target_stage = tk.StringVar(value="4")  # Default value 4
        target_spinbox = tk.Spinbox(
            target_frame, 
            from_=1, 
            to=10, 
            textvariable=self.target_stage,
            width=10,
            font=("Arial", 10)
        )
        target_spinbox.pack(pady=5)
        
        # Control Buttons Frame
        control_frame = tk.LabelFrame(self.root, text="Controls", padx=10, pady=5)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_button = tk.Button(control_frame, text="Start Bot", command=self.start_bot, width=15, state='disabled')
        self.start_button.pack(pady=5)
        
        self.pause_button = tk.Button(control_frame, text="Pause", command=self.toggle_pause, width=15, state='disabled')
        self.pause_button.pack(pady=5)
        
        self.stop_button = tk.Button(control_frame, text="Stop", command=self.stop_bot, width=15, state='disabled')
        self.stop_button.pack(pady=5)
        
        self.calibrate_button = tk.Button(control_frame, text="Calibrate", command=self.calibrate, width=15)
        self.calibrate_button.pack(pady=5)
        
        # Log Frame
        log_frame = tk.LabelFrame(self.root, text="Log", padx=10, pady=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, width=40)
        self.log_text.pack(fill="both", expand=True)
        
        # Scrollbar for log
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
    
    def log(self, message):
        if hasattr(self, 'log_text') and self.log_text.winfo_exists():
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.root.update()
    
    def on_calibration_complete(self, calibration_data):
        """Callback yang dipanggil setelah kalibrasi selesai"""
        self.calibration_data = calibration_data
        self.root.after(0, self.post_calibration)  # Schedule GUI update
    
    def post_calibration(self):
        """Update GUI setelah kalibrasi selesai"""
        if self.calibration_data:
            self.player = GamePlayer(self.calibration_data)
            self.player.set_logger(self.log)
            self.log("Calibration successful!")
            self.start_button.config(state='normal')
            self.calibrate_button.config(state='disabled')
            self.status_label.config(text="Calibrated")
    
    def calibrate(self):
        """Start calibration process"""
        # Pastikan bot benar-benar berhenti
        if self.running or self.bot_thread and self.bot_thread.is_alive():
            self.stop_bot()
        
        # Reset state sebelum kalibrasi baru
        self.reset_state()
        
        self.log("Starting calibration...")
        # Buat calibrator baru
        self.create_new_calibrator()
        # Mulai kalibrasi
        self.calibrator.calibrate()
    
    def start_bot(self):
        if not self.calibration_data:
            self.log("Please calibrate first!")
            return
        
        # Pastikan bot sebelumnya sudah berhenti
        if self.bot_thread and self.bot_thread.is_alive():
            self.stop_bot()
        
        # Reset attempts dan statistik di player
        if self.player:
            self.player.reset_stats()
        
        self.running = True
        self.paused = False
        self.start_button.config(state='disabled')
        self.pause_button.config(state='normal')
        self.stop_button.config(state='normal')
        self.calibrate_button.config(state='disabled')
        
        # Start bot in separate thread
        self.bot_thread = threading.Thread(target=self.run_bot)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        
        self.status_label.config(text="Running")
        self.log("\n" + "="*40)
        self.log("Starting new bot session...")
        self.log(f"Target stage: {self.target_stage.get()}")
    
    def stop_bot(self):
        """Stop bot dan reset semua state"""
        self.force_stop = True
        self.running = False
        self.paused = False
        
        if self.player:
            self.player.set_force_stop(True)  # Set force stop di player
        
        # Tunggu thread bot berhenti
        if self.bot_thread and self.bot_thread.is_alive():
            try:
                self.bot_thread.join(timeout=2.0)  # Tunggu lebih lama
                if self.bot_thread.is_alive():  # Jika masih hidup setelah timeout
                    self.log("Force stopping bot...")
            except:
                pass
        
        # Reset semua state
        self.force_stop = False  # Reset force stop flag
        self.player = None
        self.calibration_data = None
        self.calibrator = None
        self.bot_thread = None
        
        # Reset GUI state
        self.start_button.config(state='disabled')
        self.pause_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        self.calibrate_button.config(state='normal')
        self.status_label.config(text="Not Running")
        self.pause_button.config(text="Pause")
        
        self.log("\n" + "="*40)
        self.log("Bot stopped - Please calibrate to start new session")
    
    def toggle_pause(self):
        self.paused = not self.paused
        if self.player:  # Pastikan player sudah diinisialisasi
            self.player.set_pause(self.paused)
        
        if self.paused:
            self.pause_button.config(text="Resume")
            self.status_label.config(text="Paused")
            self.log("Bot paused")
        else:
            self.pause_button.config(text="Pause")
            self.status_label.config(text="Running")
            self.log("Bot resumed")
        
        # Force update GUI
        self.root.update()
    
    def run_bot(self):
        try:
            while self.running and not self.force_stop:  # Check force stop flag
                if not self.paused:
                    try:
                        if self.force_stop:  # Check di awal loop
                            break
                        
                        target = int(self.target_stage.get())
                        self.player.set_target_stage(target)
                        
                        if self.force_stop:  # Check sebelum play_game
                            break
                            
                        self.player.play_game()
                        
                        if self.force_stop:  # Check setelah play_game
                            break
                            
                    except Exception as e:
                        self.log(f"Error in game loop: {str(e)}")
                        self.stop_bot()
                        break
                time.sleep(0.1)
        except Exception as e:
            self.log(f"Critical error: {str(e)}")
        finally:
            if self.force_stop:
                self.log("Bot force stopped")
            self.running = False
            self.force_stop = False
    
    def run(self):
        def update():
            try:
                self.root.update()
                self.root.after(100, update)
            except:
                pass
        
        update()
        self.root.mainloop()

if __name__ == "__main__":
    gui = BotGUI()
    gui.run() 