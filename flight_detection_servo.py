#!/usr/bin/env python3

import cv2
import numpy as np
import time
import datetime
import argparse
from pathlib import Path
import lgpio

# Camera Configuration
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
#a
# HSV Color Detection Configuration
HSV_MIN = np.array([117, 141, 109], dtype=np.uint8)    # Lower bound of target color
HSV_MAX = np.array([179, 255, 255], dtype=np.uint8)  # Upper bound of target color
MIN_AREA = 10000    # Minimum area to consider a valid detection
MAX_AREA = 22000  # Maximum area to consider a valid detection

# Servo Configuration
GPIO_PIN = 17          # GPIO pin number for servo
SERVO_COOLDOWN = 1.0   # Time to wait between servo movements (seconds)
FREQ = 50             # PWM frequency (Hz)
MIN_DUTY = 2.5        # Duty cycle for 0 degrees
MAX_DUTY = 12.5       # Duty cycle for 180 degrees
OPEN_ANGLE = 90      # Angle for opening servo
CLOSE_ANGLE = 0       # Angle for closing servo
OPEN_TIME = 2         # Time to keep servo open in seconds

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Capture photos at timed intervals with color detection.')
    parser.add_argument('-d', '--duration', type=int, default=60,
                      help='Total duration in minutes (default: 60)')
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                      help='Capture interval in seconds (default: 1.0)')
    parser.add_argument('-e', '--exposure', type=int, default=-6,
                      help='Camera exposure value (default: -6, negative values decrease exposure)')
    parser.add_argument('-o', '--output', type=str, default="captured_photos",
                      help='Output directory for photos (default: captured_photos)')
    parser.add_argument('--detections-only', action='store_true',
                      help='Only save frames with color detections (default: save all frames)')
    return parser.parse_args()

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
                    
                    # Set buffer size to 1 to reduce latency
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    # Set FPS to maximum
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    print(f"Successfully initialized camera with backend {backend} at index {index}")
                    print(f"FPS: {cap.get(cv2.CAP_PROP_FPS)}")
                    print(f"Buffer size: {cap.get(cv2.CAP_PROP_BUFFERSIZE)}")
                    return cap
            except Exception as e:
                print(f"Error with backend {backend} at index {index}: {str(e)}")
                continue
    
    raise RuntimeError("No working camera found! Tried all available backends.")

def init_servo():
    """Initialize the servo motor using lgpio"""
    try:
        h = lgpio.gpiochip_open(0)
        # Configure GPIO pin for PWM
        lgpio.gpio_claim_output(h, GPIO_PIN)
        # Start PWM at minimum position
        lgpio.tx_pwm(h, GPIO_PIN, FREQ, MIN_DUTY)
        print(f"Initialized servo on GPIO {GPIO_PIN}")
        return h
    except Exception as e:
        print(f"Failed to initialize servo: {str(e)}")
        return None

def move_servo(h, angle):
    """Move servo to specified angle"""
    duty_cycle = MIN_DUTY + (MAX_DUTY - MIN_DUTY) * angle / 180
    lgpio.tx_pwm(h, GPIO_PIN, FREQ, duty_cycle)

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
            
            return (cx, cy, max_area)
    
    return None

def main():
    args = parse_args()
    
    # Convert duration to seconds
    total_duration = args.duration * 60
    
    # Initialize the camera and servo
    try:
        camera = init_camera(args.exposure)
        h = init_servo()
        if h is None:
            print("Warning: Servo initialization failed, continuing without servo control")
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
        f.write("timestamp,filepath,detection_found,center_x,center_y,area,servo_moved\n")
    
    print(f"\nStarting capture session:")
    print(f"Duration: {args.duration} minutes")
    print(f"Interval: {args.interval} seconds")
    print(f"Exposure: {args.exposure}")
    print(f"Output directory: {session_dir}")
    print(f"Saving {'only frames with detections' if args.detections_only else 'all frames'}\n")
    
    start_time = time.time()
    last_capture_time = start_time
    last_servo_move = start_time - SERVO_COOLDOWN  # Allow immediate first move
    servo_at_min = True  # Track if servo is at min position
    frame_count = 0
    fps_time = start_time
    
    try:
        while (time.time() - start_time) < total_duration:
            current_time = time.time()
            
            # Calculate and display FPS every second
            frame_count += 1
            if current_time - fps_time >= 1.0:
                fps = frame_count / (current_time - fps_time)
                print(f"FPS: {fps:.2f}")
                frame_count = 0
                fps_time = current_time
            
            # Capture frame immediately without waiting
            ret, frame = camera.read()
            if not ret:
                print("Failed to grab frame")
                continue
            
            # Swap red and blue channels for correct color
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame
            detection_info = detect_color(frame)
            detection_found = detection_info is not None
            
            # Handle servo control based on detection
            if h is not None:
                if detection_found:
                    # Open servo when blob detected
                    move_servo(h, OPEN_ANGLE)
                    last_servo_move = current_time
                elif current_time - last_servo_move >= OPEN_TIME:
                    # Close servo after OPEN_TIME seconds
                    move_servo(h, CLOSE_ANGLE)
            
            # Save frame if needed (based on interval)
            if (current_time - last_capture_time) >= args.interval:
                timestamp = datetime.datetime.now()
                filename = f"frame_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                filepath = session_dir / filename
                
                if not args.detections_only or detection_found:
                    if save_image(frame, str(filepath)):
                        print(f"Saved frame to {filepath}")
                        
                        # Log the capture with servo movement info
                        with open(log_path, "a") as f:
                            if detection_found:
                                cx, cy, area = detection_info
                                f.write(f"{timestamp.isoformat()},{filepath},True,{cx},{cy},{area},True\n")
                            else:
                                f.write(f"{timestamp.isoformat()},{filepath},False,,,,False\n")
                
                last_capture_time = current_time
            
            # Small sleep to prevent CPU overload, but much shorter than before
            time.sleep(0.01)  # 10ms delay instead of 100ms
            
    except KeyboardInterrupt:
        print("\nStopping capture")
    finally:
        # Cleanup
        camera.release()
        if h is not None:
            move_servo(h, CLOSE_ANGLE)  # Return to min position
            lgpio.gpio_free(h, GPIO_PIN)
            lgpio.gpiochip_close(h)
        print("Cleanup completed")

if __name__ == "__main__":
    main()
