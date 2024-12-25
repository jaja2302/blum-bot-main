import cv2
import numpy as np
import pyautogui
import time

class HoopTracker:
    def __init__(self):
        self.basket_history = []
        self.history_max = 6
        self.last_detection_time = None
        self.velocity = [0, 0]

    def update_history(self, position, current_time):
        """Update position history dan hitung velocity"""
        if self.last_detection_time and self.basket_history:
            dt = current_time - self.last_detection_time
            if dt > 0:
                # Hitung velocity
                self.velocity[0] = (position[0] - self.basket_history[-1][0]) / dt
                self.velocity[1] = (position[1] - self.basket_history[-1][1]) / dt
        
        self.basket_history.append((position[0], position[1], current_time))
        self.last_detection_time = current_time
        
        if len(self.basket_history) > self.history_max:
            self.basket_history.pop(0)

    def predict_position(self, current_time):
        """Prediksi posisi berdasarkan velocity"""
        if not self.basket_history:
            return None
            
        last_pos = (self.basket_history[-1][0], self.basket_history[-1][1])
        dt = current_time - self.last_detection_time
        
        # Prediksi posisi berikutnya
        predicted_x = last_pos[0] + self.velocity[0] * dt
        predicted_y = last_pos[1] + self.velocity[1] * dt
        
        return (int(predicted_x), int(predicted_y))

def get_hoop_position(window_rect):
    """Main function to get hoop position"""
    try:
        current_time = time.time()
        
        # Jika tidak ada deteksi, gunakan prediksi dari tracker
        if not hasattr(get_hoop_position, 'tracker'):
            get_hoop_position.tracker = HoopTracker()
        
        screenshot = np.array(pyautogui.screenshot(region=window_rect))
        if screenshot is None:
            predicted_pos = get_hoop_position.tracker.predict_position(current_time)
            return predicted_pos

        # Tetap menggunakan range warna yang sama
        red_lower = np.array([0, 0, 170])
        red_upper = np.array([15, 25, 255])
        
        # Tingkatkan blur untuk mengurangi noise lebih baik
        blurred = cv2.GaussianBlur(screenshot, (7, 7), 0)
        red_mask = cv2.inRange(cv2.cvtColor(blurred, cv2.COLOR_RGB2BGR), red_lower, red_upper)
        
        # Tambah iterasi morphological operations
        kernel = np.ones((5,5), np.uint8)  # Kernel lebih besar
        red_mask = cv2.dilate(red_mask, kernel, iterations=2)
        red_mask = cv2.erode(red_mask, kernel, iterations=1)
        
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            valid_contours = []
            height = screenshot.shape[0]
            for cnt in contours:
                # Tambah minimum area threshold
                if cv2.contourArea(cnt) > 50:  # Minimal area 50 pixel
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
                    
                    screen_x = window_rect[0] + cx
                    screen_y = window_rect[1] + cy
                    
                    # Update tracker dengan posisi baru
                    get_hoop_position.tracker.update_history((screen_x, screen_y), current_time)
                    return (screen_x, screen_y)
        
        # Jika tidak ada deteksi, gunakan prediksi
        predicted_pos = get_hoop_position.tracker.predict_position(current_time)
        return predicted_pos
        
    except Exception as e:
        print(f"Error tracking hoop: {e}")
        return None

# Initialize last_pos as static variable
get_hoop_position.last_pos = None

def collect_training_data():
    """Collect training data by capturing hoop positions"""
    training_data = []
    return training_data 

    