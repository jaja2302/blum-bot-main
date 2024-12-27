import cv2
import numpy as np

class HoopDetector:
    BOX_SIZE = 72
    MARKER_LENGTH = 10
    KERNEL = np.ones((3, 3), np.uint8)
    
    # Detection area boundaries
    DETECTION_START_Y = 150  # Adjust this to be below score area
    DETECTION_END_Y = 400    # Adjust this to cover hoop area
    
    def __init__(self):
        self.missed_detections = 0
        

    def detect_hoop(self, screenshot: np.ndarray) -> tuple[int, int] | None:
        frame_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        
        # Draw blue detection area
        self.draw_detection_area(frame_bgr)
        
        # Crop to detection area
        detection_area = frame_bgr[self.DETECTION_START_Y:self.DETECTION_END_Y, :]

        # Try color detection first
        result = self.detect_hoop_color(detection_area)
        if result:
            x, y = result
            adjusted_result = (x, y + self.DETECTION_START_Y)
            self.draw_target_box(frame_bgr, adjusted_result)
            # self.debug_window(frame_bgr)
            return adjusted_result

        # Try shape detection if color fails
        result = self.detect_hoop_shape(detection_area)
        if result:
            x, y = result
            adjusted_result = (x, y + self.DETECTION_START_Y)
            self.draw_target_box(frame_bgr, adjusted_result)
            # self.debug_window(frame_bgr)
            return adjusted_result

        # self.debug_window(frame_bgr)
        return None

    def draw_detection_area(self, frame: np.ndarray) -> None:
        """Draw blue detection area markers."""
        height, width = frame.shape[:2]
        
        # Draw horizontal lines
        cv2.line(frame, (0, self.DETECTION_START_Y), (width, self.DETECTION_START_Y), (255, 0, 0), 2)
        cv2.line(frame, (0, self.DETECTION_END_Y), (width, self.DETECTION_END_Y), (255, 0, 0), 2)
        
        # Draw vertical lines
        cv2.line(frame, (0, self.DETECTION_START_Y), (0, self.DETECTION_END_Y), (255, 0, 0), 2)
        cv2.line(frame, (width-1, self.DETECTION_START_Y), (width-1, self.DETECTION_END_Y), (255, 0, 0), 2)

    def detect_hoop_color(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        """Detect hoop based on color."""
        red_lower, red_upper = self.get_adaptive_color_range()
        red_mask = cv2.inRange(frame_bgr, red_lower, red_upper)
        red_mask = cv2.dilate(red_mask, self.KERNEL, iterations=1)

        contours = self.find_contours(red_mask)
        return self.get_largest_contour_center(contours)

    def detect_hoop_shape(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        """Detect hoop based on shape."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(cv2.GaussianBlur(gray, (9, 9), 2), 50, 150)

        contours = self.find_contours(edges)
        valid_contours = self.filter_valid_contours(contours, frame_bgr.shape[0])
        return self.get_largest_contour_center(valid_contours)

    def get_adaptive_color_range(self) -> tuple[np.ndarray, np.ndarray]:
        """Adjust red color range based on missed detections."""
        red_lower = np.array([0, 0, 170])
        red_upper = np.array([15, 25, 255])

        if self.missed_detections > 10:
            red_lower[2] = max(150, red_lower[2] - 10)
            red_upper[1] = min(35, red_upper[1] + 5)

        return red_lower, red_upper

    def find_contours(self, binary_mask: np.ndarray) -> list:
        """Find contours in binary image."""
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def filter_valid_contours(self, contours: list, frame_height: int) -> list:
        """Filter contours based on area and position."""
        return [
            cnt for cnt in contours if cv2.contourArea(cnt) > 100
            and cv2.boundingRect(cnt)[2] > cv2.boundingRect(cnt)[3]  # width > height
        ]

    def get_largest_contour_center(self, contours: list) -> tuple[int, int] | None:
        """Get center coordinates of largest contour."""
        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                return (cx, cy)
        return None

    def draw_target_box(self, frame: np.ndarray, position: tuple[int, int]) -> None:
        """Draw target box around detected hoop."""
        cx, cy = position
        box_start = (cx - self.BOX_SIZE // 2, cy - self.BOX_SIZE // 2)
        box_end = (cx + self.BOX_SIZE // 2, cy + self.BOX_SIZE // 2)

        # Draw main box
        cv2.rectangle(frame, box_start, box_end, (0, 255, 0), 2)

        # Draw corner markers
        self.draw_corner_markers(frame, box_start, box_end)

    def draw_corner_markers(self, frame: np.ndarray, box_start: tuple[int, int], box_end: tuple[int, int]) -> None:
        """Draw corner markers for target box."""
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
        """Draw marker lines."""
        for end in ends:
            cv2.line(frame, start, end, (0, 255, 0), 2)

    # def debug_window(self, frame: np.ndarray) -> None:
    #     """Show debug window."""
    #     cv2.imshow('Hoop Detection Debug', frame)
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         cv2.destroyAllWindows()
    #         exit()