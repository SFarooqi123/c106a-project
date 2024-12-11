#!/usr/bin/env python3

import cv2
import numpy as np
import time
import datetime
import os
from pathlib import Path

# Camera Configuration
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_EXPOSURE = -6  # Negative values decrease exposure (make image darker)

# Timing Configuration
CAPTURE_INTERVAL = 5  # Time between captures in seconds
TOTAL_DURATION_MINUTES = 60
TOTAL_DURATION = TOTAL_DURATION_MINUTES * 60  # Total runtime in seconds

# Output Configuration
OUTPUT_DIR = "captured_photos"
SAVE_DETECTED_ONLY = True  # Only save photos where target color is detected

# HSV Color Detection Configuration
HSV_MIN = np.array([107, 24, 6], dtype=np.uint8)    # Lower bound of target color
HSV_MAX = np.array([154, 255, 255], dtype=np.uint8)  # Upper bound of target color
MIN_AREA = 500    # Minimum area to consider a valid detection
MAX_AREA = 4000  # Maximum area to consider a valid detection

def init_camera():
    """Initialize the camera with specified resolution."""
    # Try different backends
    backends = [cv2.CAP_ANY, cv2.CAP_V4L2, cv2.CAP_GSTREAMER]
    
    for backend in backends:
        print(f"Trying camera backend: {backend}")
        for index in range(2):  # Try first two camera indices
            try:
                cap = cv2.VideoCapture(index, backend)
                if cap.isOpened():
                    # Set resolution
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                    
                    # Set exposure
                    cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_EXPOSURE)
                    print(f"Set exposure to: {CAMERA_EXPOSURE}")
                    
                    # Try to read a test frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"Successfully initialized camera with backend {backend} at index {index}")
                        print(f"Frame size: {frame.shape}")
                        return cap
                    else:
                        print(f"Camera opened but couldn't read frame with backend {backend} at index {index}")
                        cap.release()
                else:
                    print(f"Failed to open camera with backend {backend} at index {index}")
            except Exception as e:
                print(f"Error with backend {backend} at index {index}: {str(e)}")
                continue
    
    # If we get here, we couldn't initialize the camera
    raise RuntimeError("No working camera found! Tried all available backends.")

def save_image(frame, output_path):
    """Save image with proper encoding to avoid libpng warnings."""
    # Convert color space if needed
    if len(frame.shape) == 3:  # Color image
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Encode to JPEG
    is_success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if is_success:
        with open(output_path, "wb") as f:
            f.write(buffer)
        return True
    return False

def detect_color(frame):
    """Detect if target color is present in frame and return detection info."""
    # Convert to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    
    # Create mask for target color
    mask = cv2.inRange(hsv, HSV_MIN, HSV_MAX)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find the largest contour
    max_area = 0
    best_cnt = None
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if MIN_AREA <= area <= MAX_AREA and area > max_area:
            max_area = area
            best_cnt = cnt
    
    # If a valid contour was found
    if best_cnt is not None:
        # Calculate centroid
        M = cv2.moments(best_cnt)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            
            # Draw detection on frame
            cv2.drawContours(frame, [best_cnt], -1, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, f'Area: {int(max_area)}', (cx, cy - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            return True, frame, mask, (cx, cy, max_area)
    
    return False, frame, mask, None

def main():
    # Initialize the camera
    try:
        camera = init_camera()
    except RuntimeError as e:
        print(f"Error: {str(e)}")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create log file
    log_path = os.path.join(OUTPUT_DIR, "capture_log.csv")
    with open(log_path, "w") as f:
        f.write("timestamp,filepath,detection_found,center_x,center_y,area\n")
    
    start_time = time.time()
    last_capture_time = start_time
    
    try:
        while (time.time() - start_time) < TOTAL_DURATION:
            # Check if it's time for next capture
            current_time = time.time()
            if (current_time - last_capture_time) >= CAPTURE_INTERVAL:
                # Capture frame
                ret, frame = camera.read()
                if not ret:
                    print("Failed to grab frame")
                    continue
                
                # Swap red and blue channels for correct color
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect target color
                detected, processed_frame, mask, detection_info = detect_color(frame)
                
                # Generate timestamp and filename
                timestamp = datetime.datetime.now()
                filename = f"frame_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                # Save frame if detection criteria met
                if not SAVE_DETECTED_ONLY or detected:
                    if save_image(processed_frame, filepath):
                        print(f"Saved frame to {filepath}")
                        
                        # Log the capture
                        with open(log_path, "a") as f:
                            if detected:
                                cx, cy, area = detection_info
                                f.write(f"{timestamp.isoformat()},{filepath},True,{cx},{cy},{area}\n")
                            else:
                                f.write(f"{timestamp.isoformat()},{filepath},False,,,\n")
                    else:
                        print(f"Failed to save frame to {filepath}")
                
                last_capture_time = current_time
            
            # Small sleep to prevent CPU overload
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping capture")
    
    # Clean up
    camera.release()
    print(f"\nCapture complete. Log file saved to {log_path}")

if __name__ == "__main__":
    main()
