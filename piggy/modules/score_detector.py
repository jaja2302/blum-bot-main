import cv2
import pytesseract

class ScoreDetector:
    def __init__(self):
        self.current_score = 0
        self.last_score = 0
        self.current_time = "00:00"
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def detect_score_and_time(self, screenshot):
        """Deteksi skor dan waktu dari posisi yang tetap"""
        height = screenshot.shape[0]
        width = screenshot.shape[1]
        
        # Area spesifik untuk skor (kiri) dan waktu (tengah)
        score_region = screenshot[0:int(height*0.1), int(width*0.1):int(width*0.2)]
        time_region = screenshot[0:int(height*0.1), int(width*0.4):int(width*0.6)]
        
        # Convert ke grayscale
        score_gray = cv2.cvtColor(score_region, cv2.COLOR_BGR2GRAY)
        time_gray = cv2.cvtColor(time_region, cv2.COLOR_BGR2GRAY)
        
        # Threshold untuk teks putih
        _, score_thresh = cv2.threshold(score_gray, 200, 255, cv2.THRESH_BINARY)
        _, time_thresh = cv2.threshold(time_gray, 200, 255, cv2.THRESH_BINARY)
        
        # OCR untuk skor
        try:
            score_text = pytesseract.image_to_string(score_thresh, 
                config='--psm 7 -c tessedit_char_whitelist=0123456789')
            if score_text.strip().isdigit():
                self.current_score = int(score_text.strip())
        except:
            pass
        
        # OCR untuk waktu
        try:
            time_text = pytesseract.image_to_string(time_thresh,
                config='--psm 7 -c tessedit_char_whitelist=0123456789:')
            if ':' in time_text:
                self.current_time = time_text.strip()
        except:
            pass
        
        return self.current_score, self.current_time 