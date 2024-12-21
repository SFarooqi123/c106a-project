#!/usr/bin/env python3
import cv2
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import shutil
import signal
import atexit

# Configuration Settings
CACHE_SIZE = 20  # Reduced cache size to conserve memory
TARGET_WIDTH = 800  # Maximum width to resize images
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}  # Supported image formats
COMPRESS_IMAGES = True  # Always compress images for faster performance

class PhotoViewer:
    def __init__(self, photo_dir, output_file=None):
        self.photo_dir = Path(photo_dir)
        self.output_file = Path(output_file or f"selected_photos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

        # Load all image files
        self.photo_files = sorted([f for f in self.photo_dir.iterdir() if f.suffix.lower() in VALID_EXTENSIONS])
        self.current_index = 0
        self.image_cache = {}  # Cache for loaded images
        self.selected_photos = set()

        # Load existing selections if the output file exists
        if self.output_file.exists():
            with open(self.output_file, 'r') as f:
                self.selected_photos = set(line.strip() for line in f)

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle Ctrl-C"""
        print("\nExiting...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Save selected photos to a directory on exit"""
        if not self.selected_photos:
            return

        dir_name = f"selected_photos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)

        for photo in self.selected_photos:
            src = Path(photo)
            if src.exists():
                shutil.copy2(src, dir_path / src.name)

        print(f"\nCopied {len(self.selected_photos)} photos to: {dir_path}")

    def load_image(self, filepath):
        """Load and resize image efficiently."""
        img = cv2.imread(str(filepath))
        if img is None:
            return None

        height, width = img.shape[:2]
        if width > TARGET_WIDTH:
            scale = TARGET_WIDTH / width
            img = cv2.resize(img, (TARGET_WIDTH, int(height * scale)), interpolation=cv2.INTER_AREA)
        return img

    def update_cache(self):
        """Update image cache around the current index."""
        self.image_cache.clear()
        start_idx = max(0, self.current_index - CACHE_SIZE)
        end_idx = min(len(self.photo_files), self.current_index + CACHE_SIZE + 1)

        for idx in range(start_idx, end_idx):
            if idx not in self.image_cache:
                img = self.load_image(self.photo_files[idx])
                if img is not None:
                    self.image_cache[idx] = img

    def save_selection(self):
        """Save selected photo filename to output file and move to next photo."""
        current_file = self.photo_files[self.current_index]
        if str(current_file) not in self.selected_photos:
            self.selected_photos.add(str(current_file))
            with open(self.output_file, 'a') as f:
                f.write(f"{current_file}\n")
            print(f"Saved: {current_file}")
        self.current_index = (self.current_index + 1) % len(self.photo_files)
        self.update_cache()

    def show_photos(self):
        """Display photos and handle keyboard input."""
        if not self.photo_files:
            print("No photos found in the directory!")
            return

        print("\nControls:")
        print("'y': Save current photo")
        print("'n': Next photo")
        print("'b': Previous photo")
        print("'q': Quit")

        self.update_cache()
        cv2.namedWindow('Photo Viewer', cv2.WINDOW_NORMAL)

        while True:
            current_file = self.photo_files[self.current_index]
            current_image = self.image_cache.get(self.current_index)

            if current_image is None:
                print(f"Could not load: {current_file}")
                self.current_index = (self.current_index + 1) % len(self.photo_files)
                continue

            cv2.imshow('Photo Viewer', current_image)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('y'):
                self.save_selection()
            elif key == ord('n'):
                self.current_index = (self.current_index + 1) % len(self.photo_files)
                self.update_cache()
            elif key == ord('b'):
                self.current_index = (self.current_index - 1) % len(self.photo_files)
                self.update_cache()

        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='Photo Viewer for Raspberry Pi')
    parser.add_argument('photo_dir', help='Directory containing photos')
    parser.add_argument('-o', '--output', help='Output file for selected photos')
    args = parser.parse_args()

    if not Path(args.photo_dir).is_dir():
        print(f"Error: {args.photo_dir} is not a valid directory")
        sys.exit(1)

    viewer = PhotoViewer(args.photo_dir, args.output)
    viewer.show_photos()


if __name__ == "__main__":
    main()
