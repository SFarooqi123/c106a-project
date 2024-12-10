#!/usr/bin/env python3

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
import argparse

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
    # Initialize camera
    if is_raspberry_camera():
        camera = get_picamera(320, 240)
        camera.start()
    else:
        camera = init_camera()
    if camera is None:
        print("Error: Could not initialize camera")
        return

    try:
        # Create output directory if it doesn't exist
        output_dir = "camera_test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            # Capture frame
            if is_raspberry_camera():
                frame = camera.capture_array()
            else:
                ret, frame = camera.read()
                if not ret:
                    print("Failed to grab frame")
                    break

            # Swap red and blue channels for correct color display
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Display frame size for debugging
            print(f"Frame shape: {frame.shape}")
            
            # Save frame every second
            current_time = time.time()
            if current_time - start_time >= 1.0:
                frame_path = os.path.join(output_dir, f"frame_{frame_count}.jpg")
                # Convert back to BGR for saving
                save_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(frame_path, save_frame)
                print(f"Saved frame to {frame_path}")
                frame_count += 1
                start_time = current_time
            
            # Convert back to BGR for display
            display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imshow('Camera Feed', display_frame)
            
            # Break on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Cleanup
        if is_raspberry_camera():
            camera.close()
        else:
            camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
