import logging
import os
import cv2
import numpy as np
from datetime import datetime

def setup_logging():
    """Setup logging configuration"""
    log_dir = "data"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logging.basicConfig(
        filename=os.path.join(log_dir, 'logs.txt'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def save_screenshot(image, prefix="screenshot"):
    """Save a screenshot for debugging"""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/{prefix}_{timestamp}.png"
    cv2.imwrite(filename, image)
    return filename

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def normalize_coordinates(x, y, width, height):
    """Normalize coordinates to [0,1] range"""
    return x/width, y/height

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = ["data"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory) 