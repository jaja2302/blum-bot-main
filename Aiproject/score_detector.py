import cv2
import pytesseract
import numpy as np

class ScoreDetector:
    def __init__(self):
        self.current_score = 0
        self.last_score = 0
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def detect_score(self, screenshot):
        """Deteksi skor saja dengan visualisasi"""
        height = screenshot.shape[0]
        width = screenshot.shape[1]
        
        # Define score region only
        score_region = (int(width*0.15), int(height*0.08), int(width*0.15), int(height*0.1))
        
        # Extract region
        score_img = screenshot[score_region[1]:score_region[1]+score_region[3], 
                             score_region[0]:score_region[0]+score_region[2]]
        
        # Draw score box (red)
        cv2.rectangle(screenshot, 
                     (score_region[0], score_region[1]), 
                     (score_region[0]+score_region[2], score_region[1]+score_region[3]), 
                     (0, 0, 255), 2)
        
        # OCR process
        try:
            score_gray = cv2.cvtColor(score_img, cv2.COLOR_BGR2GRAY)
            _, score_thresh = cv2.threshold(score_gray, 200, 255, cv2.THRESH_BINARY)
            
            score_text = pytesseract.image_to_string(score_thresh, 
                config='--psm 7 -c tessedit_char_whitelist=0123456789')
            if score_text.strip().isdigit():
                self.current_score = int(score_text.strip())
            
            # Draw detected score
            cv2.putText(screenshot, f"Score: {self.current_score}", 
                       (10, height-30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 0, 255), 2)
            
        except Exception as e:
            print(f"OCR Error: {e}")
        
        return self.current_score

    def detect_game_end(self, screenshot):
        """Detect if game ended (Nice/Winner/Lose/Defeat)"""
        height = screenshot.shape[0]
        width = screenshot.shape[1]
        
        # 1. Check using OCR
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        try:
            text = pytesseract.image_to_string(thresh).lower().strip()
            if any(word in text.lower() for word in ['nice', 'winner', 'lose', 'ok', 'defeat', 'game over']):
                return True
        except:
            pass
        
        # 2. Check for red "Defeat" text
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
        
        # Red color range in HSV
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        
        # Create mask for red color
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        
        # Focus on center area where "Defeat" typically appears
        center_region = red_mask[int(height*0.3):int(height*0.7), int(width*0.3):int(width*0.7)]
        
        # If significant red pixels are found in center region
        if np.sum(center_region > 0) > 100:  # Adjust threshold as needed
            try:
                # Try OCR on this region specifically
                text = pytesseract.image_to_string(center_region).lower().strip()
                if 'defeat' in text:
                    print("Detected Defeat message!")
                    return True
            except:
                pass
        
        return False 