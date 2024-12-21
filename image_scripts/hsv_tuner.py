#!/usr/bin/env python3

import cv2
import numpy as np
import argparse
from pathlib import Path
import sys
import json
import os
import time
import signal
import atexit

# Configuration Constants
WINDOW_NAMES = ['Original', 'Mask', 'Result']

# Camera Configuration
CAMERA_WIDTH = 640  # Optimized resolution for Raspberry Pi
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# HSV and Area Defaults
HSV_PARAMS = [
    ('H min', 0, 179),
    ('H max', 179, 179),
    ('S min', 0, 255),
    ('S max', 255, 255),
    ('V min', 0, 255),
    ('V max', 255, 255),
    ('Area min', 100, 10000),
    ('Area max', 500, 100000)
]

# File Configuration
CONFIG_FILE = 'hsv_tuner_config.json'

class HSVTuner:
    def __init__(self, photo_dir=None, output_dir=None):
        self.photo_dir = Path(photo_dir) if photo_dir else None
        self.output_dir = Path(output_dir) if output_dir else None
        self.current_index = 0
        self.use_camera = photo_dir is None

        # Initialize camera or load photos
        if self.use_camera:
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # Use V4L2 backend for better performance
            if not self.cap.isOpened():
                print("Error: Could not open camera")
                sys.exit(1)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        else:
            self.photo_files = sorted([f for f in self.photo_dir.iterdir() if f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp'}])
            if not self.photo_files:
                print("No photos found in directory!")
                sys.exit(1)

        # Create OpenCV window first
        cv2.namedWindow('Controls', cv2.WINDOW_NORMAL)

        # Load saved HSV configuration
        self.hsv_values = self.load_config()

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)

        # Create trackbars with loaded or default values
        for name, default, max_val in HSV_PARAMS:
            value = self.hsv_values.get(name, default)
            cv2.createTrackbar(name, 'Controls', value, max_val, lambda x: None)

        # Pre-load current frame (if using photos) to reduce lag
        self.current_frame = None
        if not self.use_camera:
            self.current_frame = self.load_current_photo()

    def signal_handler(self, sig, frame):
        print("\nSaving values and exiting...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        self.save_config()
        if self.use_camera:
            self.cap.release()
        cv2.destroyAllWindows()

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Initialize with defaults
                    result = {name: default for name, default, _ in HSV_PARAMS}
                    # Update with loaded values if they're valid
                    for name, default, max_val in HSV_PARAMS:
                        if name in config and isinstance(config[name], (int, float)):
                            value = int(config[name])  # Convert to int
                            if 0 <= value <= max_val:  # Validate range
                                result[name] = value
                    return result
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Return defaults if loading fails
        return {name: default for name, default, _ in HSV_PARAMS}

    def save_config(self):
        try:
            hsv_values = {}
            for name, _, max_val in HSV_PARAMS:
                value = cv2.getTrackbarPos(name, 'Controls')
                if 0 <= value <= max_val:  # Validate before saving
                    hsv_values[name] = value
                else:
                    print(f"Warning: Invalid value for {name}: {value}")
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(hsv_values, f, indent=4)
            print(f"Saved HSV values to {CONFIG_FILE}")
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_current_photo(self):
        if 0 <= self.current_index < len(self.photo_files):
            img = cv2.imread(str(self.photo_files[self.current_index]))
            if img is None:
                print(f"Error: Could not load image {self.photo_files[self.current_index]}")
                return None
            return cv2.GaussianBlur(img, (5, 5), 0)  # Apply Gaussian blur for smoother mask
        return None

    def get_frame(self):
        if self.use_camera:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read from camera")
                return None
            return cv2.GaussianBlur(frame, (5, 5), 0)  # Apply Gaussian blur for smoother mask
        else:
            return self.current_frame

    def process_frame(self, frame, hsv_params):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (hsv_params['H min'], hsv_params['S min'], hsv_params['V min']),
                           (hsv_params['H max'], hsv_params['S max'], hsv_params['V max']))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        result = frame.copy()
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if hsv_params['Area min'] <= area <= hsv_params['Area max']:
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(result, (x, y), (x + w, y + h), (255, 0, 0), 2)

        return mask, result

    def show_images(self):
        while True:
            frame = self.get_frame()
            if frame is None:
                break

            # Get HSV parameters from trackbars
            hsv_params = {name: cv2.getTrackbarPos(name, 'Controls') for name, _, _ in HSV_PARAMS}

            # Process frame
            mask, result = self.process_frame(frame, hsv_params)

            # Display images
            cv2.imshow('Original', frame)
            cv2.imshow('Mask', mask)
            cv2.imshow('Result', result)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif not self.use_camera:
                if key == ord('n'):
                    self.current_index = (self.current_index + 1) % len(self.photo_files)
                    self.current_frame = self.load_current_photo()
                elif key == ord('b'):
                    self.current_index = (self.current_index - 1) % len(self.photo_files)
                    self.current_frame = self.load_current_photo()

        self.cleanup()

def main():
    parser = argparse.ArgumentParser(description='HSV Tuner for Raspberry Pi')
    parser.add_argument('photo_dir', nargs='?', help='Directory containing photos to view')
    parser.add_argument('-o', '--output', help='Output directory for results')
    args = parser.parse_args()

    if args.photo_dir and not Path(args.photo_dir).is_dir():
        print(f"Error: {args.photo_dir} is not a valid directory")
        sys.exit(1)

    tuner = HSVTuner(args.photo_dir, args.output)
    tuner.show_images()

if __name__ == "__main__":
    main()
