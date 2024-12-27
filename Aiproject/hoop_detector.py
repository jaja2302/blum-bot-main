import cv2
import numpy as np

class HoopDetector:
    BOX_SIZE = 72
    MARKER_LENGTH = 10
    KERNEL = np.ones((3, 3), np.uint8)

    def __init__(self):
        self.missed_detections = 0

    def detect_hoop(self, screenshot: np.ndarray) -> tuple[int, int] | None:
        """Mendeteksi hoop menggunakan metode warna atau bentuk."""
        frame_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

        # Coba deteksi warna terlebih dahulu
        result = self.detect_hoop_color(frame_bgr)
        if result:
            self.draw_target_box(frame_bgr, result)
            return result

        # Jika deteksi warna gagal, coba deteksi bentuk
        result = self.detect_hoop_shape(frame_bgr)
        if result:
            self.draw_target_box(frame_bgr, result)
            return result

        return None

    def detect_hoop_color(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        """Mendeteksi hoop berdasarkan warna."""
        height = frame_bgr.shape[0]
        roi = frame_bgr[int(height * 0.2):int(height * 0.5), :]

        red_lower, red_upper = self.get_adaptive_color_range()
        red_mask = cv2.inRange(roi, red_lower, red_upper)
        red_mask = cv2.dilate(red_mask, self.KERNEL, iterations=1)

        contours = self.find_contours(red_mask)
        return self.get_largest_contour_center(contours, offset_y=int(height * 0.2))

    def detect_hoop_shape(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        """Mendeteksi hoop berdasarkan bentuk."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(cv2.GaussianBlur(gray, (9, 9), 2), 50, 150)

        contours = self.find_contours(edges)
        valid_contours = self.filter_valid_contours(contours, frame_bgr.shape[0])
        return self.get_largest_contour_center(valid_contours)

    def get_adaptive_color_range(self) -> tuple[np.ndarray, np.ndarray]:
        """Menyesuaikan rentang warna merah berdasarkan missed_detections."""
        red_lower = np.array([0, 0, 170])
        red_upper = np.array([15, 25, 255])

        if self.missed_detections > 10:
            red_lower[2] = max(150, red_lower[2] - 10)
            red_upper[1] = min(35, red_upper[1] + 5)

        return red_lower, red_upper

    def find_contours(self, binary_mask: np.ndarray) -> list:
        """Menemukan kontur dari citra biner."""
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def filter_valid_contours(self, contours: list, frame_height: int) -> list:
        """Memfilter kontur yang memenuhi kriteria valid."""
        return [
            cnt for cnt in contours if cv2.contourArea(cnt) > 100
            and cv2.boundingRect(cnt)[1] < frame_height / 2  # Kontur di atas layar tengah
            and cv2.boundingRect(cnt)[2] > cv2.boundingRect(cnt)[3]  # Lebar > tinggi
        ]

    def get_largest_contour_center(self, contours: list, offset_y: int = 0) -> tuple[int, int] | None:
        """Mengembalikan koordinat pusat kontur terbesar."""
        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"]) + offset_y
                return (cx, cy)
        return None

    def draw_target_box(self, frame: np.ndarray, position: tuple[int, int]) -> None:
        """Menggambar kotak target di sekitar hoop."""
        cx, cy = position
        box_start = (cx - self.BOX_SIZE // 2, cy - self.BOX_SIZE // 2)
        box_end = (cx + self.BOX_SIZE // 2, cy + self.BOX_SIZE // 2)

        # Gambar kotak utama
        cv2.rectangle(frame, box_start, box_end, (0, 255, 0), 2)

        # Gambar penanda sudut
        self.draw_corner_markers(frame, box_start, box_end)

    def draw_corner_markers(self, frame: np.ndarray, box_start: tuple[int, int], box_end: tuple[int, int]) -> None:
        """Menggambar penanda sudut untuk kotak target."""
        x1, y1 = box_start
        x2, y2 = box_end

        # Top-left
        self.draw_marker(frame, (x1, y1), (x1 + self.MARKER_LENGTH, y1), (x1, y1 + self.MARKER_LENGTH))
        # Top-right
        self.draw_marker(frame, (x2, y1), (x2 - self.MARKER_LENGTH, y1), (x2, y1 + self.MARKER_LENGTH))
        # Bottom-left
        self.draw_marker(frame, (x1, y2), (x1 + self.MARKER_LENGTH, y2), (x1, y2 - self.MARKER_LENGTH))
        # Bottom-right
        self.draw_marker(frame, (x2, y2), (x2 - self.MARKER_LENGTH, y2), (x2, y2 - self.MARKER_LENGTH))

    def draw_marker(self, frame: np.ndarray, start: tuple[int, int], *ends: tuple[int, int]) -> None:
        """Menggambar garis marker."""
        for end in ends:
            cv2.line(frame, start, end, (0, 255, 0), 2)
