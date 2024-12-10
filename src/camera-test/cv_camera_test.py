#!/usr/bin/python3

# ------------------------------------------------------------------------------
# rpi-object-detection
# ------------------------------------------------------------------------------
# Save the image captured from the camera to disk. Used as a test program to 
# verify if OpenCV has been properly installed.
# ------------------------------------------------------------------------------
# automaticdai
# YF Robotics Labrotary
# Instagram: yfrobotics
# Twitter: @yfrobotics
# Website: https://yfrobotics.github.io/
# ------------------------------------------------------------------------------

import os
import sys
import cv2
import time
import numpy as np

# Set OpenCV to use a headless backend
os.environ['OPENCV_VIDEOIO_PRIORITY_BACKEND'] = '0'
os.environ['DISPLAY'] = ':0'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.picamera_utils import is_raspberry_camera, get_picamera

# Configuration
USE_BGR_MODE = False  # Set to False if camera feed shows red as blue

def init_camera():
    # Try different camera indices
    for index in range(4):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Get camera info
            print(f"Camera found at index {index}")
            print(f"Resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
            return cap
    raise RuntimeError("No camera found!")

def main():
    try:
        # Initialize camera
        if is_raspberry_camera():
            cap = get_picamera(320, 240)
            cap.start()
        else:
            cap = init_camera()
        
        # Create output directory if it doesn't exist
        output_dir = "camera_test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            if is_raspberry_camera():
                frame = cap.capture_array()
            else:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                
            # Convert BGR to RGB if needed
            if not USE_BGR_MODE:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Display frame size for debugging
            print(f"Frame shape: {frame.shape}")
            
            # Save frame every second
            current_time = time.time()
            if current_time - start_time >= 1.0:
                frame_path = os.path.join(output_dir, f"frame_{frame_count}.jpg")
                if USE_BGR_MODE:
                    cv2.imwrite(frame_path, frame)
                else:
                    cv2.imwrite(frame_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                print(f"Saved frame to {frame_path}")
                frame_count += 1
                start_time = current_time
            
            # Break after 5 frames
            if frame_count >= 5:
                print("Captured 5 frames successfully")
                break
                
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Cleanup
        if 'cap' in locals():
            cap.close() if is_raspberry_camera() else cap.release()

if __name__ == "__main__":
    main()
