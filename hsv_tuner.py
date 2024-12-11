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

def nothing(x):
    pass

class HSVTuner:
    def __init__(self, photo_dir=None, output_dir=None):
        self.photo_dir = Path(photo_dir) if photo_dir else None
        self.output_dir = Path(output_dir) if output_dir else None
        self.current_index = 0
        self.selected_photos = set()
        self.hsv_values = {}
        self.use_camera = photo_dir is None
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        if self.use_camera:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Could not open camera")
                sys.exit(1)
            # Set camera resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        else:
            # Load all image files
            self.photo_files = [f for f in self.photo_dir.iterdir() 
                              if f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp'}]
            self.photo_files.sort()
            
            if not self.photo_files:
                print("No photos found in directory!")
                sys.exit(1)
        
        # Load saved configuration
        self.load_config()
        
        # Get screen resolution
        try:
            from screeninfo import get_monitors
            screen = get_monitors()[0]
            self.screen_width = screen.width
            self.screen_height = screen.height
        except:
            self.screen_width = 1920
            self.screen_height = 1080
        
        # Create windows with specific sizes and positions
        window_width = self.screen_width // 3
        window_height = (self.screen_height - 100)  # Leave space for controls
        
        cv2.namedWindow('Original', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Mask', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Result', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Controls', cv2.WINDOW_NORMAL)
        
        # Set window sizes and positions
        cv2.resizeWindow('Original', window_width, window_height)
        cv2.resizeWindow('Mask', window_width, window_height)
        cv2.resizeWindow('Result', window_width, window_height)
        cv2.resizeWindow('Controls', self.screen_width, 100)
        
        cv2.moveWindow('Original', 0, 0)
        cv2.moveWindow('Mask', window_width, 0)
        cv2.moveWindow('Result', 2 * window_width, 0)
        cv2.moveWindow('Controls', 0, window_height)
        
        # Create trackbars
        params = [
            ('H min', 0, 179), ('H max', 179, 179),
            ('S min', 0, 255), ('S max', 255, 255),
            ('V min', 0, 255), ('V max', 255, 255),
            ('Area min', 100, 50000), ('Area max', 5000, 50000)
        ]
        
        for name, default, max_val in params:
            value = self.hsv_values.get(name.lower().replace(' ', '_'), default)
            cv2.createTrackbar(name, 'Controls', value, max_val, nothing)
    
    def __del__(self):
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C"""
        print("\nSaving values and exiting...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Save values and clean up resources"""
        # Save to JSON config
        self.save_config()
        
        # Save as Python arrays with timestamp
        h_min = cv2.getTrackbarPos('H min', 'Controls')
        h_max = cv2.getTrackbarPos('H max', 'Controls')
        s_min = cv2.getTrackbarPos('S min', 'Controls')
        s_max = cv2.getTrackbarPos('S max', 'Controls')
        v_min = cv2.getTrackbarPos('V min', 'Controls')
        v_max = cv2.getTrackbarPos('V max', 'Controls')
        area_min = cv2.getTrackbarPos('Area min', 'Controls')
        area_max = cv2.getTrackbarPos('Area max', 'Controls')
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_file = 'hsv_values_log.txt'
        
        # Create file with header if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write("# HSV Tuner Log\n")
                f.write("# Format: timestamp, HSV_MIN, HSV_MAX, MIN_AREA, MAX_AREA\n\n")
        
        with open(log_file, 'a') as f:
            f.write(f"\n# {timestamp}\n")
            f.write(f"HSV_MIN = np.array([{h_min}, {s_min}, {v_min}], dtype=np.uint8)    # Lower bound of target color\n")
            f.write(f"HSV_MAX = np.array([{h_max}, {s_max}, {v_max}], dtype=np.uint8)  # Upper bound of target color\n")
            f.write(f"MIN_AREA = {area_min}    # Minimum area to consider a valid detection\n")
            f.write(f"MAX_AREA = {area_max}  # Maximum area to consider a valid detection\n")
            f.write("#" + "-" * 80 + "\n")  # Separator line
        
        print(f"Appended HSV values to {log_file}")
        
        # Release camera if using it
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
        
        # Close all windows
        cv2.destroyAllWindows()
    
    def load_config(self):
        """Load HSV values from config file"""
        if os.path.exists('hsv_tuner_config.json'):
            with open('hsv_tuner_config.json', 'r') as f:
                config = json.load(f)
                self.hsv_values = config.get('hsv_values', {})
    
    def save_config(self):
        """Save HSV values to config file"""
        hsv_values = {
            'h_min': cv2.getTrackbarPos('H min', 'Controls'),
            'h_max': cv2.getTrackbarPos('H max', 'Controls'),
            's_min': cv2.getTrackbarPos('S min', 'Controls'),
            's_max': cv2.getTrackbarPos('S max', 'Controls'),
            'v_min': cv2.getTrackbarPos('V min', 'Controls'),
            'v_max': cv2.getTrackbarPos('V max', 'Controls'),
            'area_min': cv2.getTrackbarPos('Area min', 'Controls'),
            'area_max': cv2.getTrackbarPos('Area max', 'Controls')
        }
        
        with open('hsv_tuner_config.json', 'w') as f:
            json.dump({'hsv_values': hsv_values}, f, indent=4)
    
    def load_image(self, filepath):
        """Load image and convert to RGB"""
        img = cv2.imread(str(filepath))
        if img is None:
            return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    def save_current_mask(self, img, mask, result, filename):
        """Save original image, mask, and result to output directory"""
        if not self.output_dir:
            return
            
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original image
        output_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(self.output_dir / f"original_{filename}"), output_img)
        
        # Save mask and result
        cv2.imwrite(str(self.output_dir / f"mask_{filename}"), mask)
        cv2.imwrite(str(self.output_dir / f"result_{filename}"), 
                   cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
        
        print(f"\nSaved to {self.output_dir}")
    
    def get_next_frame(self):
        """Get next frame from either camera or image files"""
        if self.use_camera:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read from camera")
                return None
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            if not (0 <= self.current_index < len(self.photo_files)):
                print("Error: Invalid photo index")
                return None
            
            current_file = self.photo_files[self.current_index]
            img = self.load_image(current_file)
            if img is None:
                print(f"Error: Could not load image {current_file}")
                self.current_index += 1
                return None
            
            return img, current_file
    
    def show_images(self):
        """Display images and handle keyboard input"""
        print("\nControls:")
        if not self.use_camera:
            print("'n' or Space - Next photo")
            print("'b' - Previous photo")
            print("Type a number to jump to that image")
        print("'y' - Save current frame/image")
        print("'q' - Quit (saves HSV values)")
        if self.photo_dir:
            print(f"\nViewing photos from: {self.photo_dir}")
        if self.output_dir:
            print(f"Output directory: {self.output_dir}")
        print()
        
        number_buffer = ""
        while True:
            # Get frame from camera or image file
            if self.use_camera:
                frame_data = self.get_next_frame()
                if frame_data is None:
                    break
                img = frame_data
                current_file = None
            else:
                frame_data = self.get_next_frame()
                if frame_data is None:
                    break
                img, current_file = frame_data
            
            # Show current image info
            if not self.use_camera:
                print(f"\rImage {self.current_index + 1}/{len(self.photo_files)}: {current_file.name}", end="")
                sys.stdout.flush()
                
                # Update window titles
                title = f'Photo {self.current_index + 1}/{len(self.photo_files)}: {current_file.name}'
                cv2.setWindowTitle('Original', f'Original - {title}')
                cv2.setWindowTitle('Mask', f'Mask - {title}')
                cv2.setWindowTitle('Result', f'Result - {title}')
            
            # Get trackbar positions
            h_min = cv2.getTrackbarPos('H min', 'Controls')
            h_max = cv2.getTrackbarPos('H max', 'Controls')
            s_min = cv2.getTrackbarPos('S min', 'Controls')
            s_max = cv2.getTrackbarPos('S max', 'Controls')
            v_min = cv2.getTrackbarPos('V min', 'Controls')
            v_max = cv2.getTrackbarPos('V max', 'Controls')
            area_min = cv2.getTrackbarPos('Area min', 'Controls')
            area_max = cv2.getTrackbarPos('Area max', 'Controls')
            
            # Convert to HSV and create mask
            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(hsv, lower, upper)
            
            # Find and draw contours
            result = img.copy()
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area_min <= area <= area_max:
                    # Draw contour
                    cv2.drawContours(result, [cnt], -1, (0, 255, 0), 2)
                    
                    # Get and draw bounding rectangle
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(result, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    
                    # Display area
                    cv2.putText(result, f'Area: {int(area)}', (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # Show images
            cv2.imshow('Original', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            cv2.imshow('Mask', mask)
            cv2.imshow('Result', cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.save_config()
                break
            elif key == ord('y'):
                if self.use_camera:
                    filename = f"frame_{int(time.time())}.jpg"
                else:
                    filename = current_file.name
                self.save_current_mask(img, mask, result, filename)
                if not self.use_camera:
                    self.selected_photos.add(filename)
            elif not self.use_camera:  # Photo navigation commands
                if key == ord('n') or key == ord(' '):
                    self.current_index = (self.current_index + 1) % len(self.photo_files)
                elif key == ord('b'):
                    self.current_index = (self.current_index - 1) % len(self.photo_files)
                elif 48 <= key <= 57:  # Number keys 0-9
                    number_buffer += chr(key)
                elif key == 13:  # Enter key
                    if number_buffer:
                        try:
                            new_index = int(number_buffer) - 1
                            if 0 <= new_index < len(self.photo_files):
                                self.current_index = new_index
                        except ValueError:
                            pass
                        number_buffer = ""
        
        cv2.destroyAllWindows()
        if self.use_camera:
            self.cap.release()

def main():
    parser = argparse.ArgumentParser(description='HSV color tuner with photo navigation')
    parser.add_argument('photo_dir', nargs='?', help='Directory containing photos to view (optional)')
    parser.add_argument('-o', '--output', help='Output directory for saved masks')
    
    args = parser.parse_args()
    
    if args.photo_dir and not Path(args.photo_dir).is_dir():
        print(f"Error: {args.photo_dir} is not a valid directory")
        sys.exit(1)
    
    tuner = HSVTuner(args.photo_dir, args.output)
    tuner.show_images()

if __name__ == "__main__":
    main()
