#!/usr/bin/env python3

import cv2
import numpy as np
import time
import datetime
import argparse
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Capture photos at timed intervals with color detection.')
    parser.add_argument('-d', '--duration', type=int, default=60,
                      help='Total duration in minutes (default: 60)')
    parser.add_argument('-i', '--interval', type=float, default=5.0,
                      help='Capture interval in seconds (default: 5.0)')
    parser.add_argument('-e', '--exposure', type=int, default=-6,
                      help='Camera exposure value (default: -6, negative values decrease exposure)')
    parser.add_argument('-o', '--output', type=str, default="captured_photos",
                      help='Output directory for photos (default: captured_photos)')
    parser.add_argument('--detections-only', action='store_true',
                      help='Only save frames with color detections (default: save all frames)')
    return parser.parse_args()

# Camera Configuration
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# HSV Color Detection Configuration
HSV_MIN = np.array([107, 24, 6], dtype=np.uint8)    # Lower bound of target color
HSV_MAX = np.array([154, 255, 255], dtype=np.uint8)  # Upper bound of target color
MIN_AREA = 500    # Minimum area to consider a valid detection
MAX_AREA = 50000   # Maximum area to consider a valid detection

def init_camera(exposure):
    """Initialize the camera with specified resolution and exposure."""
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
                    cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
                    print(f"Set exposure to: {exposure}")
                    
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
    
    raise RuntimeError("No working camera found! Tried all available backends.")

def save_image(frame, output_path):
    """Save image with proper encoding to avoid libpng warnings."""
    if len(frame.shape) == 3:  # Color image
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
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
    
    # Find the largest contour within area bounds
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
    args = parse_args()
    
    # Convert duration to seconds
    total_duration = args.duration * 60
    
    # Initialize the camera
    try:
        camera = init_camera(args.exposure)
    except RuntimeError as e:
        print(f"Error: {str(e)}")
        return
    
    # Create base output directory if it doesn't exist
    base_dir = Path(args.output)
    base_dir.mkdir(exist_ok=True)
    
    # Create timestamped directory for this session
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    session_dir = base_dir / timestamp
    session_dir.mkdir(exist_ok=True)
    
    # Create log file in session directory
    log_path = session_dir / "capture_log.csv"
    with open(log_path, "w") as f:
        f.write("timestamp,filepath,detection_found,center_x,center_y,area\n")
    
    print(f"\nStarting capture session:")
    print(f"Duration: {args.duration} minutes")
    print(f"Interval: {args.interval} seconds")
    print(f"Exposure: {args.exposure}")
    print(f"Output directory: {session_dir}")
    print(f"Saving {'only frames with detections' if args.detections_only else 'all frames'}\n")
    
    start_time = time.time()
    last_capture_time = start_time
    
    try:
        while (time.time() - start_time) < total_duration:
            # Check if it's time for next capture
            current_time = time.time()
            if (current_time - last_capture_time) >= args.interval:
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
                filepath = session_dir / filename
                
                # Save frame if detection criteria met
                if not args.detections_only or detected:
                    if save_image(processed_frame, str(filepath)):
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
    print(f"All photos saved in: {session_dir}")

if __name__ == "__main__":
    main()
