import pygetwindow as gw
import pyautogui
import time
import random
from pynput.mouse import Button, Controller
import cv2
import numpy as np
from PIL import ImageGrab, ImageDraw
import json

class MatchMoneyBot:
    def __init__(self):
        self.mouse = Controller()
        self.window_name = "TelegramDesktop"
        self.window = None
        self.running = False
        self.paused = False
        self.games_played = 0
        self.last_scan_time = time.time()
        self.game_area = None
        self.board_start_y = None
        self.board_start_x = None
        self.cell_size = None
        
        # Color codes for messages
        self.PUTIH = '\033[1;97m'
        self.MERAH = '\033[1;91m'
        self.HIJAU = '\033[1;92m'
        self.KUNING = '\033[1m\033[93m'
        self.BIRU = '\033[1;94m'
        self.RESET = '\033[0m'
        self.debug = True
        
        # Update warna bidak dengan nilai hex yang tepat
        self.gem_colors = {
            'yellow': {'rgb': (254, 223, 16),  # #fedf10
                      'tolerance': 50},
            'green': {'rgb': (12, 216, 4),     # #0cd804
                     'tolerance': 50},
            'red': {'rgb': (252, 60, 28),      # #fc3c1c
                   'tolerance': 50},
            'blue': {'rgb': (12, 148, 228),    # #0c94e4
                    'tolerance': 50},
            'bomb': {'rgb': (119, 122, 226),   # #777ae2
                    'tolerance': 50}
        }

        self.templates = {
            'gem': None,
            'threshold': 0.8
        }
        self.load_templates()

        # Koordinat relatif untuk area game
        self.board_offset_x = 0.2
        self.board_offset_y = 0.3
        self.board_width = 0.6
        self.board_height = 0.6

        # Load calibration data first
        self.board_calibration = self.load_board_calibration()
        
        # Then calculate cell size
        self.calculate_cell_size()

    def load_templates(self):
        """Load template images for pattern matching"""
        try:
            # Load template for a single gem
            self.templates['gem'] = cv2.imread('gem_template.png', cv2.IMREAD_GRAYSCALE)
            if self.templates['gem'] is None:
                print(f"{self.MERAH}Failed to load gem template{self.RESET}")
        except Exception as e:
            print(f"{self.MERAH}Error loading templates: {str(e)}{self.RESET}")

    def find_window(self):
        """Find and activate the Telegram window"""
        windows = gw.getWindowsWithTitle(self.window_name)
        if not windows:
            return False
        
        self.window = windows[0]
        if self.debug:
            print(f"{self.HIJAU}Found window:")
            print(f"Position: ({self.window.left}, {self.window.top})")
            print(f"Size: {self.window.width}x{self.window.height}{self.RESET}")
        
        self.window.activate()
        time.sleep(1)
        
        # Calculate game area after window is found
        self.calculate_game_area()
        return True

    def calculate_cell_size(self):
        """Calculate cell size based on calibration data"""
        if self.board_calibration and "corners" in self.board_calibration:
            # Jika cell_size sudah ada di kalibrasi, gunakan itu
            if "cell_size" in self.board_calibration:
                self.cell_size = self.board_calibration["cell_size"]
            else:
                # Kalau tidak, hitung dari lebar board
                corners = self.board_calibration["corners"]
                board_width = corners["top_right"]["x"] - corners["top_left"]["x"]
                self.cell_size = int(board_width / 9)  # 9 columns
                
            print(f"{self.HIJAU}Cell size: {self.cell_size}px{self.RESET}")

    def calculate_game_area(self):
        """Calculate the game board area using calibration data"""
        try:
            if not self.board_calibration:
                print(f"{self.MERAH}No calibration data available!{self.RESET}")
                return False

            corners = self.board_calibration["corners"]
            
            # Gunakan koordinat dari kalibrasi
            self.board_start_x = corners["top_left"]["x"]
            self.board_start_y = corners["top_left"]["y"]
            
            # Calculate board dimensions
            board_width = corners["top_right"]["x"] - corners["top_left"]["x"]
            board_height = corners["bottom_left"]["y"] - corners["top_left"]["y"]
            
            # Area game adalah persegi panjang yang dibentuk oleh 4 sudut
            self.game_area = (
                self.board_start_x,
                self.board_start_y,
                board_width,
                board_height
            )
            
            if self.debug:
                print(f"{self.HIJAU}Game area calculated from calibration:")
                print(f"Start position: ({self.board_start_x}, {self.board_start_y})")
                print(f"Board dimensions: {board_width}x{board_height}")
                print(f"Cell size: {self.cell_size}px")
                print(f"Game area: {self.game_area}{self.RESET}")
                
            return True
            
        except Exception as e:
            print(f"{self.MERAH}Error calculating game area: {str(e)}{self.RESET}")
            return False

    def click(self, x, y):
        """Perform a mouse click with slight randomization"""
        self.mouse.position = (x, y + random.randint(1, 3))
        self.mouse.press(Button.left)
        self.mouse.release(Button.left)

    def check_play_button(self):
        """Look for and click the play button"""
        window_rect = (
            self.window.left, self.window.top,
            self.window.width, self.window.height
        )
        
        try:
            play_button = pyautogui.locateOnScreen('play_button.png', 
                                                  confidence=0.7, 
                                                  region=window_rect)
            if play_button:
                self.games_played += 1
                play_x, play_y = pyautogui.center(play_button)
                self.click(play_x, play_y)
                print(f"{self.HIJAU}Starting game #{self.games_played}...{self.RESET}")
                time.sleep(2)
                return True
        except:
            pass
        return False

    def scan_and_match(self):
        """Scan the game board and make matches"""
        if not self.game_area:
            if self.debug:
                print(f"{self.MERAH}Game area not initialized{self.RESET}")
            return
        
        try:
            current_time = time.time()
            if current_time - self.last_scan_time >= 0.2:
                if self.debug:
                    print(f"{self.BIRU}Scanning board...{self.RESET}")
                
                # Capture dan tampilkan debug window
                window_info = self.board_calibration["window_info"]
                screenshot = pyautogui.screenshot(
                    region=(
                        window_info["left"],
                        window_info["top"],
                        window_info["width"],
                        window_info["height"]
                    )
                )
                debug_image = np.array(screenshot)
                debug_image = cv2.cvtColor(debug_image, cv2.COLOR_RGB2BGR)
                
                # Draw grid dan scan points
                corners = self.board_calibration["corners"]
                start_x = corners["top_left"]["x"] - window_info["left"]
                start_y = corners["top_left"]["y"] - window_info["top"]
                
                # Draw board outline
                points = []
                for corner in ["top_left", "top_right", "bottom_right", "bottom_left"]:
                    x = corners[corner]["x"] - window_info["left"]
                    y = corners[corner]["y"] - window_info["top"]
                    points.append((int(x), int(y)))
                
                for i in range(4):
                    cv2.line(debug_image, points[i], points[(i+1)%4], (0, 255, 0), 2)
                
                board = [[None for _ in range(9)] for _ in range(11)]
                
                # Scan dan visualisasi
                for row in range(11):
                    for col in range(9):
                        x = self.board_start_x + (col * self.cell_size) + (self.cell_size // 2)
                        y = self.board_start_y + (row * self.cell_size) + (self.cell_size // 2)
                        
                        # Draw scan point
                        screen_x = x - window_info["left"]
                        screen_y = y - window_info["top"]
                        
                        try:
                            pixel = pyautogui.pixel(x, y)
                            color_name = self.get_gem_color(pixel)
                            
                            if color_name:
                                board[row][col] = (color_name, x, y)
                                # Draw colored circle for detected gems
                                color_map = {
                                    'red': (0, 0, 255),
                                    'blue': (255, 0, 0),
                                    'green': (0, 255, 0),
                                    'yellow': (0, 255, 255),
                                    'bomb': (255, 0, 255)
                                }
                                cv2.circle(debug_image, (screen_x, screen_y), 5, color_map.get(color_name, (255, 255, 255)), -1)
                                if self.debug:
                                    print(f"Found {color_name} at ({row},{col}) position ({x},{y})")
                            else:
                                # Draw red dot for no detection
                                cv2.circle(debug_image, (screen_x, screen_y), 3, (0, 0, 255), 1)
                                
                        except Exception as e:
                            if self.debug:
                                print(f"Skip position ({row},{col}): {str(e)}")
                            cv2.circle(debug_image, (screen_x, screen_y), 3, (0, 0, 255), 1)
                
                # Add debug info overlay
                info_text = [
                    f"Cell Size: {self.cell_size}px",
                    f"Scanning: {current_time - self.last_scan_time:.2f}s",
                    f"Found gems: {sum(1 for row in board for cell in row if cell is not None)}"
                ]
                
                for i, text in enumerate(info_text):
                    cv2.putText(
                        debug_image,
                        text,
                        (10, 20 + (i * 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1
                    )
                
                # Show debug window
                cv2.imshow('Game Area Debug', debug_image)
                cv2.waitKey(1)
                
                # Find and make matches
                if self.find_and_make_move(board):
                    time.sleep(0.5)  # Wait for animation
                
                self.last_scan_time = current_time
                
        except Exception as e:
            print(f"{self.MERAH}Error scanning board: {str(e)}{self.RESET}")

    def get_gem_color(self, pixel):
        """Determine the color of a gem from its pixel color"""
        r, g, b = pixel
        
        # Skip brown boxes and dark background
        if (r > 150 and g > 100 and b < 100) or (r < 50 and g < 50 and b < 50):
            return None
        
        # Check each color with specific thresholds
        if abs(r - 254) <= 30 and abs(g - 223) <= 30 and abs(b - 16) <= 30:
            return 'yellow'
        elif abs(r - 12) <= 30 and abs(g - 216) <= 30 and abs(b - 4) <= 30:
            return 'green'
        elif abs(r - 252) <= 30 and abs(g - 60) <= 30 and abs(b - 28) <= 30:
            return 'red'
        elif abs(r - 12) <= 30 and abs(g - 148) <= 30 and abs(b - 228) <= 30:
            return 'blue'
        elif abs(r - 119) <= 30 and abs(g - 122) <= 30 and abs(b - 226) <= 30:
            return 'bomb'
        
        return None

    def find_and_make_move(self, board):
        """Find a valid move and execute it"""
        # Debug: print board state
        if self.debug:
            print("\nCurrent board state:")
            for row in range(11):
                row_str = ""
                for col in range(9):
                    if board[row][col]:
                        row_str += f"{board[row][col][0][0]} "  # First letter of color
                    else:
                        row_str += "- "
                print(row_str)

        # Check for potential matches by swapping adjacent pieces
        for row in range(11):
            for col in range(8):  # Check horizontal swaps
                if not board[row][col] or not board[row][col+1]:
                    continue
                    
                # Try horizontal swap
                temp_board = [row[:] for row in board]
                temp_board[row][col], temp_board[row][col+1] = temp_board[row][col+1], temp_board[row][col]
                
                # Check if swap creates a match
                if self.would_create_match(temp_board, row, col):
                    if self.debug:
                        print(f"\nFound potential horizontal move at ({row},{col}) -> ({row},{col+1})")
                        print(f"Colors: {board[row][col][0]} <-> {board[row][col+1][0]}")
                    
                    # Make the move
                    self.drag_move(
                        board[row][col][1], board[row][col][2],
                        board[row][col+1][1], board[row][col+1][2]
                    )
                    return True

        # Check vertical swaps
        for row in range(10):  # Up to second-to-last row
            for col in range(9):
                if not board[row][col] or not board[row+1][col]:
                    continue
                    
                # Try vertical swap
                temp_board = [row[:] for row in board]
                temp_board[row][col], temp_board[row+1][col] = temp_board[row+1][col], temp_board[row][col]
                
                # Check if swap creates a match
                if self.would_create_match(temp_board, row, col):
                    if self.debug:
                        print(f"\nFound potential vertical move at ({row},{col}) -> ({row+1},{col})")
                        print(f"Colors: {board[row][col][0]} <-> {board[row+1][col][0]}")
                    
                    # Make the move
                    self.drag_move(
                        board[row][col][1], board[row][col][2],
                        board[row+1][col][1], board[row+1][col][2]
                    )
                    return True
        
        if self.debug:
            print("\nNo valid moves found")
        return False

    def would_create_match(self, board, row, col):
        """Check if position creates a match after swap"""
        def check_horizontal_match(r, c):
            # Check for horizontal match centered at (r,c)
            if c >= 1 and c <= 7:
                if (board[r][c-1] and board[r][c] and board[r][c+1] and
                    board[r][c-1][0] == board[r][c][0] == board[r][c+1][0]):
                    return True
            return False

        def check_vertical_match(r, c):
            # Check for vertical match centered at (r,c)
            if r >= 1 and r <= 9:
                if (board[r-1][c] and board[r][c] and board[r+1][c] and
                    board[r-1][c][0] == board[r][c][0] == board[r+1][c][0]):
                    return True
            return False

        # Check all possible matches around the swapped pieces
        positions_to_check = [
            (row, col),
            (row, col+1),
            (row+1, col)
        ]

        for r, c in positions_to_check:
            if r < 0 or r >= 11 or c < 0 or c >= 9:
                continue
            if check_horizontal_match(r, c) or check_vertical_match(r, c):
                return True

        return False

    def drag_move(self, x1, y1, x2, y2):
        """Make a move by dragging between two positions"""
        try:
            if self.debug:
                print(f"\nMaking move: ({x1},{y1}) -> ({x2},{y2})")
            
            # Add small random offset to make moves more human-like
            offset = random.randint(-5, 5)
            
            # Move to start position
            self.mouse.position = (x1 + offset, y1 + offset)
            time.sleep(0.3)
            
            # Press and hold
            self.mouse.press(Button.left)
            time.sleep(0.2)
            
            # Drag to end position (with slight curve)
            mid_x = (x1 + x2) // 2 + random.randint(-10, 10)
            mid_y = (y1 + y2) // 2 + random.randint(-10, 10)
            self.mouse.position = (mid_x, mid_y)
            time.sleep(0.1)
            self.mouse.position = (x2 + offset, y2 + offset)
            time.sleep(0.2)
            
            # Release
            self.mouse.release(Button.left)
            time.sleep(0.5)  # Wait for animations
            
            if self.debug:
                print("Move completed")
            
        except Exception as e:
            print(f"{self.MERAH}Error making move: {str(e)}{self.RESET}")

    def is_similar_color(self, pixel, target_color, tolerance=30):
        """Check if two colors are similar within a tolerance"""
        r1, g1, b1 = pixel
        r2, g2, b2 = target_color
        
        # Hitung perbedaan warna
        diff_r = abs(r1 - r2)
        diff_g = abs(g1 - g2)
        diff_b = abs(b1 - b2)
        
        if self.debug:
            print(f"Color diff: R={diff_r}, G={diff_g}, B={diff_b}")
        
        return (diff_r <= tolerance and 
                diff_g <= tolerance and 
                diff_b <= tolerance)

    def is_valid_gem(self, pixel):
        """Check if pixel color represents a valid gem (not empty/box)"""
        r, g, b = pixel
        
        # Warna coklat box
        if (r > 150 and g > 100 and b < 100):  # Box berwarna coklat
            return False
        
        # Warna background
        if (r < 50 and g < 50 and b < 50):  # Background gelap
            return False
        
        return True

    def play_game(self):
        """Start a new game if available"""
        if self.check_play_button():
            print(f"{self.HIJAU}Found play button, starting new game...{self.RESET}")
            time.sleep(1)  # Wait for game to load
            return True
        return False

    def start(self):
        """Start the bot"""
        self.running = True
        while self.running:
            if not self.paused:
                self.scan_and_match()
            time.sleep(0.01)

    def stop(self):
        """Stop the bot"""
        self.running = False
        print(f"{self.PUTIH}Total games played: {self.KUNING}{self.games_played}{self.RESET}")
        # Close debug window
        cv2.destroyAllWindows()

    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        if self.paused:
            print(f"{self.BIRU}Bot paused...{self.RESET}")
        else:
            print(f"{self.BIRU}Bot continuing...{self.RESET}") 

    def debug_show_game_area(self):
        """Show debug visualization of the game area"""
        try:
            if not self.board_calibration:
                return
            
            window_info = self.board_calibration["window_info"]
            screenshot = pyautogui.screenshot(
                region=(
                    window_info["left"],
                    window_info["top"],
                    window_info["width"],
                    window_info["height"]
                )
            )
            debug_image = np.array(screenshot)
            debug_image = cv2.cvtColor(debug_image, cv2.COLOR_RGB2BGR)
            
            corners = self.board_calibration["corners"]
            
            # Draw board outline
            points = []
            for corner in ["top_left", "top_right", "bottom_right", "bottom_left"]:
                x = corners[corner]["x"] - window_info["left"]
                y = corners[corner]["y"] - window_info["top"]
                points.append((int(x), int(y)))
            
            # Draw board outline
            for i in range(4):
                cv2.line(debug_image, points[i], points[(i+1)%4], (0, 255, 0), 2)
            
            # Draw grid
            start_x = points[0][0]
            start_y = points[0][1]
            
            # Draw vertical lines
            for i in range(10):  # 10 lines for 9 columns
                x = int(start_x + (i * self.cell_size))
                cv2.line(
                    debug_image,
                    (x, start_y),
                    (x, start_y + (11 * self.cell_size)),
                    (0, 255, 255),
                    1
                )
            
            # Draw horizontal lines
            for i in range(12):  # 12 lines for 11 rows
                y = int(start_y + (i * self.cell_size))
                cv2.line(
                    debug_image,
                    (start_x, y),
                    (start_x + (9 * self.cell_size), y),
                    (0, 255, 255),
                    1
                )
            
            # Draw scan points
            for row in range(11):
                for col in range(9):
                    x = int(start_x + (col * self.cell_size) + (self.cell_size // 2))
                    y = int(start_y + (row * self.cell_size) + (self.cell_size // 2))
                    cv2.circle(debug_image, (x, y), 3, (0, 0, 255), -1)
                    
                    # Add coordinate text
                    cv2.putText(
                        debug_image,
                        f"({col},{row})",
                        (x-15, y-5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.3,
                        (255, 255, 255),
                        1
                    )
            
            # Show debug window
            cv2.imshow('Game Area Debug', debug_image)
            cv2.waitKey(1)
            
        except Exception as e:
            print(f"{self.MERAH}Error showing debug visualization: {str(e)}{self.RESET}")

    def load_board_calibration(self):
        """Load board calibration data"""
        try:
            with open('board_calibration.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{self.MERAH}Board calibration file not found!{self.RESET}")
            return None 

    def show_debug_window(self):
        """Show debug window without scanning"""
        if not self.board_calibration:
            print(f"{self.MERAH}No calibration data available!{self.RESET}")
            return
        
        try:
            window_info = self.board_calibration["window_info"]
            screenshot = pyautogui.screenshot(
                region=(
                    window_info["left"],
                    window_info["top"],
                    window_info["width"],
                    window_info["height"]
                )
            )
            debug_image = np.array(screenshot)
            debug_image = cv2.cvtColor(debug_image, cv2.COLOR_RGB2BGR)
            
            corners = self.board_calibration["corners"]
            
            # Draw board outline
            points = []
            for corner in ["top_left", "top_right", "bottom_right", "bottom_left"]:
                x = corners[corner]["x"] - window_info["left"]
                y = corners[corner]["y"] - window_info["top"]
                points.append((int(x), int(y)))
            
            # Draw board outline in blue
            for i in range(4):
                cv2.line(debug_image, points[i], points[(i+1)%4], (255, 0, 0), 2)
            
            # Draw grid in yellow
            for i in range(9):
                # Vertical lines
                x = int(points[0][0] + (i * self.cell_size))
                if x <= points[1][0]:
                    cv2.line(debug_image, (x, points[0][1]), (x, points[2][1]), (0, 255, 255), 1)
                
                # Horizontal lines
                y = int(points[0][1] + (i * self.cell_size))
                if y <= points[2][1]:
                    cv2.line(debug_image, (points[0][0], y), (points[1][0], y), (0, 255, 255), 1)
            
            # Draw scan points in red
            for row in range(8):
                for col in range(8):
                    x = int(points[0][0] + (col * self.cell_size) + (self.cell_size // 2))
                    y = int(points[0][1] + (row * self.cell_size) + (self.cell_size // 2))
                    if (x <= points[1][0] and y <= points[2][1]):
                        cv2.circle(debug_image, (x, y), 3, (0, 0, 255), -1)
                        # Add coordinate text
                        cv2.putText(
                            debug_image,
                            f"({col},{row})",
                            (x-15, y-5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.3,
                            (255, 255, 255),
                            1
                        )
            
            # Add debug info
            info_text = [
                f"Cell Size: {self.cell_size}px",
                f"Board Start: ({self.board_start_x}, {self.board_start_y})",
                f"Board Width: {points[1][0] - points[0][0]}px",
                f"Board Height: {points[2][1] - points[0][1]}px",
                f"Window: {window_info['width']}x{window_info['height']}"
            ]
            
            for i, text in enumerate(info_text):
                cv2.putText(
                    debug_image,
                    text,
                    (10, 20 + (i * 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
            
            # Show debug window
            cv2.imshow('Game Area Debug', debug_image)
            cv2.waitKey(0)  # Wait for key press
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"{self.MERAH}Error showing debug window: {str(e)}{self.RESET}") 