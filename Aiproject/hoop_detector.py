import cv2
import numpy as np
import time

class HoopDetector:
    BOX_SIZE = 72
    MARKER_LENGTH = 10
    KERNEL = np.ones((3, 3), np.uint8)
    
    # Detection area boundaries
    DETECTION_START_Y = 150  # Adjust this to be below score area
    DETECTION_END_Y = 400    # Adjust this to cover hoop area
    
    def __init__(self):
        self.missed_detections = 0
        self.last_ball_pos = None
        self.score_time = 0
        self.score_display_duration = 1.0  # Display "SCORE!" for 1 second
        self.last_valid_hoop_pos = None
        self.lost_tracking_frames = 0
        self.max_lost_frames = 3  # Reduce max prediction frames
        self.hoop_velocity = None
        self.last_detection_time = None
        self.debug_mode = False  # Add debug mode flag
        
    def is_ball_in_hoop(self, ball_pos, hoop_pos) -> bool:
        """Check if ball is inside hoop area"""
        if not ball_pos or not hoop_pos:
            return False
            
        # Define hoop box boundaries
        hoop_x, hoop_y = hoop_pos
        box_half = self.BOX_SIZE // 2
        
        # Check if ball is inside hoop box
        return (hoop_x - box_half < ball_pos[0] < hoop_x + box_half and
                hoop_y - box_half < ball_pos[1] < hoop_y + box_half)

    def detect_hoop(self, screenshot: np.ndarray, ball_pos=None) -> tuple[int, int] | None:
        frame_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        current_time = time.time()
        height, width = frame_bgr.shape[:2]
        
        # Try normal detection first
        detection_area = frame_bgr[self.DETECTION_START_Y:self.DETECTION_END_Y, :]
        result = self.detect_hoop_color(detection_area)
        
        if result:
            x, y = result
            adjusted_result = (x, y + self.DETECTION_START_Y)
            
            # Update velocity if we have previous position
            if self.last_valid_hoop_pos and self.last_detection_time:
                dt = current_time - self.last_detection_time
                if dt > 0:
                    dx = adjusted_result[0] - self.last_valid_hoop_pos[0]
                    dy = adjusted_result[1] - self.last_valid_hoop_pos[1]
                    
                    # Smooth velocity updates
                    if self.hoop_velocity is None:
                        self.hoop_velocity = (dx/dt, dy/dt)
                    else:
                        # Weighted average with previous velocity (smoothing)
                        alpha = 0.7  # Weight for new velocity
                        self.hoop_velocity = (
                            alpha * (dx/dt) + (1-alpha) * self.hoop_velocity[0],
                            alpha * (dy/dt) + (1-alpha) * self.hoop_velocity[1]
                        )
            
            self.last_valid_hoop_pos = adjusted_result
            self.last_detection_time = current_time
            self.lost_tracking_frames = 0
            
            if self.debug_mode:
                # Draw hoop box
                box_half = self.BOX_SIZE // 2
                cv2.rectangle(frame_bgr, 
                             (adjusted_result[0] - box_half, adjusted_result[1] - box_half),
                             (adjusted_result[0] + box_half, adjusted_result[1] + box_half),
                             (0, 255, 0), 2)
                
                # Draw vertical line through hoop center
                cv2.line(frame_bgr,
                        (adjusted_result[0], 0),
                        (adjusted_result[0], height),
                        (0, 255, 0), 1)  # Green line
                
                # Draw velocity vector if available
                if self.hoop_velocity:
                    # Draw predicted path
                    predicted_x = adjusted_result[0] + int(self.hoop_velocity[0] * 0.5)  # 0.5 second prediction
                    cv2.line(frame_bgr,
                            (adjusted_result[0], adjusted_result[1]),
                            (predicted_x, adjusted_result[1]),
                            (255, 255, 0), 2)  # Yellow line for prediction
                
                cv2.imshow('Hoop Detection Debug', frame_bgr)
                cv2.waitKey(1)
                
            return adjusted_result
        
        else:
            # If detection failed, try to predict position
            if self.last_valid_hoop_pos and self.hoop_velocity and self.lost_tracking_frames < self.max_lost_frames:
                self.lost_tracking_frames += 1
                dt = current_time - self.last_detection_time
                
                # Predict new position based on velocity
                predicted_x = int(self.last_valid_hoop_pos[0] + self.hoop_velocity[0] * dt)
                predicted_y = int(self.last_valid_hoop_pos[1] + self.hoop_velocity[1] * dt)
                
                # Bound predictions to reasonable area
                predicted_x = max(self.BOX_SIZE, min(predicted_x, width - self.BOX_SIZE))
                predicted_y = max(self.DETECTION_START_Y + self.BOX_SIZE, 
                                min(predicted_y, self.DETECTION_END_Y - self.BOX_SIZE))
                
                predicted_pos = (predicted_x, predicted_y)
                
                if self.debug_mode:
                    box_half = self.BOX_SIZE // 2
                    # Draw predicted box
                    cv2.rectangle(frame_bgr,
                                (predicted_x - box_half, predicted_y - box_half),
                                (predicted_x + box_half, predicted_y + box_half),
                                (0, 255, 255), 2)  # Yellow box
                    
                    # Draw vertical line through predicted center
                    cv2.line(frame_bgr,
                            (predicted_x, 0),
                            (predicted_x, height),
                            (0, 255, 255), 1)  # Yellow line
                    
                    cv2.imshow('Hoop Detection Debug', frame_bgr)
                    cv2.waitKey(1)
                    
                return predicted_pos
        
        if self.debug_mode:
            cv2.imshow('Hoop Detection Debug', frame_bgr)
            cv2.waitKey(1)
        
        return None

    def draw_detection_area(self, frame: np.ndarray) -> None:
        """Draw blue detection area markers."""
        height, width = frame.shape[:2]
        
        # Define blue color as tuple (B,G,R)
        blue_color = (255, 0, 0)  # BGR format
        
        # Draw horizontal lines
        cv2.line(frame, 
                 (0, self.DETECTION_START_Y), 
                 (width, self.DETECTION_START_Y), 
                 blue_color, 
                 2)
        cv2.line(frame, 
                 (0, self.DETECTION_END_Y), 
                 (width, self.DETECTION_END_Y), 
                 blue_color, 
                 2)
        
        # Draw vertical lines
        cv2.line(frame, 
                 (0, self.DETECTION_START_Y), 
                 (0, self.DETECTION_END_Y), 
                 blue_color, 
                 2)
        cv2.line(frame, 
                 (width-1, self.DETECTION_START_Y), 
                 (width-1, self.DETECTION_END_Y), 
                 blue_color, 
                 2)

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

    def draw_target_box(self, frame: np.ndarray, position: tuple[int, int], color=(0, 255, 0)) -> None:
        """Draw target box around detected hoop with specified color."""
        cx, cy = position
        box_start = (cx - self.BOX_SIZE // 2, cy - self.BOX_SIZE // 2)
        box_end = (cx + self.BOX_SIZE // 2, cy + self.BOX_SIZE // 2)

        # Draw main box
        cv2.rectangle(frame, box_start, box_end, color, 2)

        # Draw corner markers
        self.draw_corner_markers(frame, box_start, box_end, color)

    def draw_corner_markers(self, frame: np.ndarray, box_start: tuple[int, int], box_end: tuple[int, int], color=(0, 255, 0)) -> None:
        """Draw corner markers for target box."""
        x1, y1 = map(int, box_start)
        x2, y2 = map(int, box_end)

        # Top-left
        self.draw_marker(frame, (x1, y1), (x1 + self.MARKER_LENGTH, y1), (x1, y1 + self.MARKER_LENGTH), color)
        # Top-right
        self.draw_marker(frame, (x2, y1), (x2 - self.MARKER_LENGTH, y1), (x2, y1 + self.MARKER_LENGTH), color)
        # Bottom-left
        self.draw_marker(frame, (x1, y2), (x1 + self.MARKER_LENGTH, y2), (x1, y2 - self.MARKER_LENGTH), color)
        # Bottom-right
        self.draw_marker(frame, (x2, y2), (x2 - self.MARKER_LENGTH, y2), (x2, y2 - self.MARKER_LENGTH), color)

    def draw_marker(self, frame: np.ndarray, start: tuple[int, int], *ends: tuple[int, int], color=(0, 255, 0)) -> None:
        """Draw marker lines."""
        # Convert coordinates to integers and ensure they are tuples of 2 values
        start = (int(start[0]), int(start[1]))
        for end in ends:
            end = (int(end[0]), int(end[1]))
            cv2.line(frame, start, end, color, 2)

    def toggle_debug(self):
        """Toggle debug window on/off"""
        self.debug_mode = not self.debug_mode
        if not self.debug_mode:
            cv2.destroyAllWindows()
    
    def debug_window(self, frame: np.ndarray) -> None:
        """Show debug window only if debug mode is on."""
        if self.debug_mode:
            # Optionally resize frame to make it smaller
            debug_frame = cv2.resize(frame, (0,0), fx=0.7, fy=0.7)
            cv2.imshow('Hoop Detection Debug', debug_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.toggle_debug()

    def reset_state(self):
        """Reset detector state between games"""
        self.missed_detections = 0

    def close_debug_window(self):
        """Close the debug window"""
        cv2.destroyAllWindows()

    def handle_ball_tracking(self, frame: np.ndarray, ball_pos: tuple[int, int], hoop_pos: tuple[int, int]) -> None:
        """Handle ball tracking and scoring visualization"""
        # Draw ball position
        cv2.circle(frame, ball_pos, 5, (0, 0, 255), -1)
        
        # Check if ball is in hoop
        if self.is_ball_in_hoop(ball_pos, hoop_pos):
            self.score_time = time.time()
        
        # Show "SCORE!" text for duration
        if time.time() - self.score_time < self.score_display_duration:
            cv2.putText(frame, "SCORE!", (50, 50), 
                      cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)