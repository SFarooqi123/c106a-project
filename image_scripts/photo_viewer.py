#!/usr/bin/env python3
import cv2
import os
import sys
import argparse
from pathlib import Path
from collections import deque
import numpy as np
from datetime import datetime
import shutil
import signal
import atexit

# Configuration Settings
CACHE_SIZE = 100        # Number of images to keep in memory (current + before/after)
TARGET_WIDTH = 800      # Maximum width to resize images to
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}  # Supported image formats
COMPRESS_IMAGES = False  # Set to False to load images at full resolution

class PhotoViewer:
    def __init__(self, photo_dir, output_file=None):
        self.photo_dir = Path(photo_dir)
        # Generate output filename with timestamp if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"selected_photos_{timestamp}.txt"
        self.output_file = Path(output_file)
        self.photo_files = []
        self.current_index = 0
        self.cache_size = CACHE_SIZE
        self.image_cache = {}  # filename -> image cache
        self.target_width = TARGET_WIDTH
        
        # Load all image files
        self.photo_files = [f for f in self.photo_dir.iterdir() 
                          if f.suffix.lower() in VALID_EXTENSIONS]
        self.photo_files.sort()
        
        # Create or load existing selections
        self.selected_photos = set()
        if self.output_file.exists():
            with open(self.output_file, 'r') as f:
                self.selected_photos = set(line.strip() for line in f)
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl-C"""
        print("\nReceived Ctrl-C, saving and exiting...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Save selected photos to directory on exit"""
        if not self.selected_photos:
            return
            
        # Create directory name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"selected_photos_{timestamp}"
        dir_path = Path(dir_name)
        
        # Create directory
        dir_path.mkdir(exist_ok=True)
        
        # Copy selected files
        copied = 0
        for photo in self.selected_photos:
            src = Path(photo)
            if src.exists():
                shutil.copy2(src, dir_path / src.name)
                copied += 1
        
        if copied > 0:
            print(f"\nCopied {copied} photos to directory: {dir_path}")
    
    def load_image(self, filepath):
        """Load and resize image efficiently."""
        if COMPRESS_IMAGES:
            # Load at reduced resolution and resize
            img = cv2.imread(str(filepath), cv2.IMREAD_REDUCED_COLOR_2)
            if img is None:
                return None
            
            height, width = img.shape[:2]
            if width > self.target_width:
                scale = self.target_width / width
                new_height = int(height * scale)
                img = cv2.resize(img, (self.target_width, new_height), 
                               interpolation=cv2.INTER_AREA)
        else:
            # Load at full resolution
            img = cv2.imread(str(filepath))
            
        return img
    
    def update_cache(self, center_index):
        """Update image cache around the current index."""
        start_idx = max(0, center_index - self.cache_size)
        end_idx = min(len(self.photo_files), center_index + self.cache_size + 1)
        
        self.image_cache = {
            idx: img for idx, img in self.image_cache.items()
            if start_idx <= idx < end_idx
        }
        
        for idx in range(start_idx, end_idx):
            if idx not in self.image_cache:
                img = self.load_image(self.photo_files[idx])
                if img is not None:
                    self.image_cache[idx] = img
    
    def save_selection(self, filename):
        """Save selected photo filename to output file."""
        with open(self.output_file, 'a') as f:
            f.write(f"{filename}\n")
        self.selected_photos.add(filename)
        print(f"Saved {filename} to {self.output_file}")
    
    def show_photos(self):
        """Display photos and handle keyboard input."""
        if not self.photo_files:
            print("No photos found in directory!")
            return
        
        print("\nControls:")
        print("'y' - Save current photo name to file")
        print("'n' or Space - Next photo")
        print("'b' - Previous photo")
        print("Type a number to jump to that image")
        print("'q' - Quit (will save selected photos to new directory)")
        print(f"\nViewing photos from: {self.photo_dir}")
        print(f"Selected photos will be saved to: {self.output_file}\n")
        
        # Initial cache load
        self.update_cache(self.current_index)
        
        # Create window with full-size display
        cv2.namedWindow('Photo Viewer', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Photo Viewer', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        
        number_buffer = ""
        while True:
            if not (0 <= self.current_index < len(self.photo_files)):
                print("Error: Invalid photo index")
                break
                
            current_file = self.photo_files[self.current_index]
            current_image = self.image_cache.get(self.current_index)
            if current_image is None:
                print(f"Error: Could not load image {current_file}")
                self.current_index += 1
                continue
            
            # Show current image index and filename
            print(f"\rImage {self.current_index + 1}/{len(self.photo_files)}: {current_file.name}", end="")
            sys.stdout.flush()
            
            # Update window title with image count
            cv2.setWindowTitle('Photo Viewer', f'Photo {self.current_index + 1}/{len(self.photo_files)}: {current_file.name}')
            
            # Display image
            cv2.imshow('Photo Viewer', current_image)
            
            # Wait for keypress
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.cleanup()
                break
            elif key == ord('y'):
                self.save_selection(self.photo_files[self.current_index].name)
                self.current_index += 1
            elif key == ord('n') or key == ord(' '):
                self.current_index = (self.current_index + 1) % len(self.photo_files)
                self.update_cache(self.current_index)
            elif key == ord('b'):
                self.current_index = (self.current_index - 1) % len(self.photo_files)
                self.update_cache(self.current_index)
            elif 48 <= key <= 57:  # Number keys 0-9
                number_buffer += chr(key)
            elif key == 13:  # Enter key
                if number_buffer:
                    try:
                        new_index = int(number_buffer) - 1
                        if 0 <= new_index < len(self.photo_files):
                            self.current_index = new_index
                            self.update_cache(self.current_index)
                    except ValueError:
                        pass
                    number_buffer = ""
        
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description='View and sort photos with keyboard input.')
    parser.add_argument('photo_dir', help='Directory containing photos to view')
    parser.add_argument('-o', '--output', 
                      help='Output file for selected photo names (default: selected_photos_TIMESTAMP.txt)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.photo_dir):
        print(f"Error: {args.photo_dir} is not a valid directory")
        sys.exit(1)
    
    viewer = PhotoViewer(args.photo_dir, args.output)
    viewer.show_photos()

if __name__ == "__main__":
    main()
