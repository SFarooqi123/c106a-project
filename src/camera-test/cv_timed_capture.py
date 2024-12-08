#!/usr/bin/python3

import os
import sys
import cv2
import time
import datetime
from pathlib import Path

# Set OpenCV to use a headless backend
os.environ['OPENCV_VIDEOIO_PRIORITY_BACKEND'] = '0'
os.environ['DISPLAY'] = ':0'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.picamera_utils import is_raspberry_camera, get_picamera

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

def capture_periodic_photos(interval_seconds, duration_seconds, output_dir="captured_photos"):
    """
    Capture photos every interval_seconds until duration_seconds have elapsed.
    
    Args:
        interval_seconds (float): Time between photos in seconds
        duration_seconds (float): Total duration to run for in seconds
        output_dir (str): Directory to save photos
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create log file
    log_file = output_path / "capture_log.txt"
    
    try:
        # Initialize camera
        if is_raspberry_camera():
            cap = get_picamera(320, 240)
            cap.start()
        else:
            cap = init_camera()
            
        start_time = time.time()
        photo_count = 0
        
        print(f"Starting photo capture sequence:")
        print(f"- Taking photos every {interval_seconds} seconds")
        print(f"- Running for {duration_seconds} seconds")
        print(f"- Saving to {output_path.absolute()}")
        
        with open(log_file, 'w') as log:
            log.write("Timestamp,PhotoPath\n")
            
            while (time.time() - start_time) < duration_seconds:
                # Get current timestamp
                timestamp = datetime.datetime.now()
                
                # Capture frame
                if is_raspberry_camera():
                    frame = cap.capture_array()
                else:
                    ret, frame = cap.read()
                    if not ret:
                        print("Failed to capture frame")
                        continue
                
                # Generate filename with timestamp
                filename = f"photo_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                photo_path = output_path / filename
                
                # Save the image
                cv2.imwrite(str(photo_path), frame)
                photo_count += 1
                
                # Log the capture
                log_entry = f"{timestamp.isoformat()},{photo_path.absolute()}\n"
                log.write(log_entry)
                print(f"Captured photo {photo_count}: {filename}")
                
                # Wait for next interval
                time.sleep(interval_seconds)
        
        print(f"\nCapture complete! Took {photo_count} photos.")
        print(f"Log file saved to: {log_file}")
            
    finally:
        # Cleanup
        if is_raspberry_camera():
            cap.stop()
        else:
            cap.release()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Capture periodic photos with timestamps')
    parser.add_argument('-i', '--interval', type=float, default=5.0,
                        help='Interval between photos in seconds (default: 5.0)')
    parser.add_argument('-d', '--duration', type=float, default=60.0,
                        help='Total duration to run in seconds (default: 60.0)')
    parser.add_argument('-o', '--output', type=str, default='captured_photos',
                        help='Output directory for photos (default: captured_photos)')
    
    args = parser.parse_args()
    
    try:
        capture_periodic_photos(args.interval, args.duration, args.output)
    except KeyboardInterrupt:
        print("\nCapture interrupted by user")
    except Exception as e:
        print(f"Error during capture: {e}")

if __name__ == "__main__":
    main()
