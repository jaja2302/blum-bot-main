import cv2
import numpy as np
import csv
from datetime import datetime
import time
import os
import json
from pathlib import Path

class HoopMovementTrainer:
    def __init__(self):
        self.log_file = f'hoop_movement_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        self.pattern_file = 'hoop_patterns.json'
        self.movement_patterns = {
            'left_to_right': [],
            'right_to_left': [],
            'center_pause': [],
            'speed_changes': []
        }
        
        # Create log file with headers
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Frame#', 'Time', 'X', 'Y', 'Direction', 'Speed', 'Red_Pixels', 'Pattern'])
    
    def analyze_movement_patterns(self, positions, times):
        """Analyze sequence of positions to detect patterns"""
        if len(positions) < 3:
            return "unknown"
            
        # Calculate direction changes
        directions = []
        for i in range(1, len(positions)):
            if positions[i][0] > positions[i-1][0]:
                directions.append("right")
            elif positions[i][0] < positions[i-1][0]:
                directions.append("left")
            else:
                directions.append("center")
                
        # Detect patterns
        if all(d == "center" for d in directions[-3:]):
            return "center_pause"
        elif all(d == "right" for d in directions[-3:]):
            return "left_to_right"
        elif all(d == "left" for d in directions[-3:]):
            return "right_to_left"
        
        return "transitioning"

    def train_from_video(self, video_path):
        print(f"\nProcessing video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        last_positions = []
        
        # Initialize delay for video playback
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        delay = int(1000 / fps) if fps > 0 else 30  # Default to 30ms if fps detection fails
        
        movement_data = {
            'left_to_right': [],
            'right_to_left': [],
            'center_pause': [],
            'speed_changes': [],
            'positions': [],
            'timestamps': [],
            'movement_patterns': []
        }
        
        start_time = time.time()
        print(f"Starting video analysis... FPS: {fps}")
        print("Controls: 'Q' to quit, 'S' to slow down, 'F' to speed up")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            current_time = time.time() - start_time
            
            try:
                # Convert to HSV
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # Blue backboard detection
                lower_blue = np.array([100, 100, 100])
                upper_blue = np.array([130, 255, 255])
                blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
                
                # White net detection
                lower_white = np.array([0, 0, 200])
                upper_white = np.array([180, 30, 255])
                white_mask = cv2.inRange(hsv, lower_white, upper_white)
                
                # Combine masks
                combined_mask = cv2.bitwise_or(blue_mask, white_mask)
                
                # Clean up mask
                kernel = np.ones((3,3), np.uint8)
                combined_mask = cv2.dilate(combined_mask, kernel, iterations=1)
                combined_mask = cv2.erode(combined_mask, kernel, iterations=1)
                
                # Find contours
                contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    valid_contours = []
                    for cnt in contours:
                        area = cv2.contourArea(cnt)
                        if 200 < area < 5000:
                            x, y, w, h = cv2.boundingRect(cnt)
                            if y < frame.shape[0]/2:  # Upper half only
                                aspect_ratio = float(w)/h
                                if 1.2 < aspect_ratio < 2.5:
                                    valid_contours.append(cnt)
                    
                    if valid_contours:
                        hoop_contour = max(valid_contours, key=cv2.contourArea)
                        x, y, w, h = cv2.boundingRect(hoop_contour)
                        center_x = x + w//2
                        center_y = y + h//2
                        
                        # Store position
                        movement_data['positions'].append({
                            'frame': frame_count,
                            'x': int(center_x),
                            'y': int(center_y),
                            'time': float(current_time)
                        })
                        
                        # Track movement
                        last_positions.append(center_x)
                        if len(last_positions) > 2:
                            last_positions.pop(0)
                        
                        # Calculate movement
                        if len(last_positions) > 1:
                            speed = last_positions[-1] - last_positions[-2]
                            
                            # Determine movement type
                            if abs(speed) < 2:
                                movement_type = "center_pause"
                                movement_data['center_pause'].append({
                                    'frame': frame_count,
                                    'position': int(center_x),
                                    'duration': float(current_time),
                                    'y_position': int(center_y)
                                })
                            elif speed > 0:
                                movement_type = "left_to_right"
                                movement_data['left_to_right'].append({
                                    'frame': frame_count,
                                    'start_x': int(last_positions[0]),
                                    'end_x': int(center_x),
                                    'speed': float(speed),
                                    'time': float(current_time)
                                })
                            else:
                                movement_type = "right_to_left"
                                movement_data['right_to_left'].append({
                                    'frame': frame_count,
                                    'start_x': int(last_positions[0]),
                                    'end_x': int(center_x),
                                    'speed': float(abs(speed)),
                                    'time': float(current_time)
                                })
                        
                        # Draw visualization
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                        
                        # Show info
                        direction = "RIGHT ➜" if speed > 0 else "⬅ LEFT" if speed < 0 else "STATIONARY"
                        cv2.putText(frame, f"{direction} | Speed: {abs(speed):.0f}", 
                                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                                  0.7, (0, 255, 0), 2)
                
                # Show frames
                cv2.imshow('Hoop Movement Training', frame)
                cv2.imshow('Detection Mask', combined_mask)
                
                # Playback control
                key = cv2.waitKey(delay) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    delay = min(delay + 5, 100)
                    print(f"Delay: {delay}ms")
                elif key == ord('f'):
                    delay = max(1, delay - 5)
                    print(f"Delay: {delay}ms")
                    
            except Exception as e:
                print(f"Error processing frame {frame_count}: {e}")
                continue
                
        # Save data
        with open('hoop_patterns.json', 'w') as f:
            json.dump(movement_data, f, indent=2)
        
        print("\nTraining Analysis:")
        print(f"Total Frames: {frame_count}")
        print(f"Left to Right movements: {len(movement_data['left_to_right'])}")
        print(f"Right to Left movements: {len(movement_data['right_to_left'])}")
        print(f"Center pauses: {len(movement_data['center_pause'])}")
        print(f"Total positions tracked: {len(movement_data['positions'])}")
        print(f"Data saved to hoop_patterns.json")
        
        cap.release()
        cv2.destroyAllWindows()

    def train_from_folder(self, folder_path='source'):
        """Train on all video files in the specified folder"""
        # Get list of video files
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov')
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(list(Path(folder_path).glob(f'*{ext}')))
        
        if not video_files:
            print(f"No video files found in {folder_path}")
            return
            
        print(f"Found {len(video_files)} videos to process")
        
        # Process each video
        all_movement_data = {
            'left_to_right': [],
            'right_to_left': [],
            'center_pause': [],
            'speed_changes': [],
            'positions': [],
            'timestamps': [],
            'movement_patterns': []
        }
        
        for video_file in video_files:
            self.train_from_video(str(video_file))
            
            # Load and merge the data from the last processed video
            with open('hoop_patterns.json', 'r') as f:
                video_data = json.load(f)
                
            # Merge data
            for key in all_movement_data:
                all_movement_data[key].extend(video_data[key])
        
        # Save combined data
        with open('hoop_patterns.json', 'w') as f:
            json.dump(all_movement_data, f, indent=2)
            
        print("\nFinal Training Summary:")
        print(f"Total videos processed: {len(video_files)}")
        print(f"Total Left to Right movements: {len(all_movement_data['left_to_right'])}")
        print(f"Total Right to Left movements: {len(all_movement_data['right_to_left'])}")
        print(f"Total Center pauses: {len(all_movement_data['center_pause'])}")
        print(f"Total positions tracked: {len(all_movement_data['positions'])}")
        print(f"Combined data saved to hoop_patterns.json")

# Usage
trainer = HoopMovementTrainer()
trainer.train_from_folder('source')  # Will process all videos in the source folder 