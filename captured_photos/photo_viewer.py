#!/usr/bin/env python3
import cv2
import os
import sys
from pathlib import Path

class PhotoViewer:
    def __init__(self, photo_dir, output_file="selected_photos.txt"):
        self.photo_dir = Path(photo_dir)
        self.output_file = Path(output_file)
        self.photo_files = []
        self.current_index = 0
        
        # Load all image files
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        self.photo_files = [f for f in self.photo_dir.iterdir() 
                          if f.suffix.lower() in valid_extensions]
        self.photo_files.sort()
        
        # Create or load existing selections
        self.selected_photos = set()
        if self.output_file.exists():
            with open(self.output_file, 'r') as f:
                self.selected_photos = set(line.strip() for line in f)
    
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
        print("'q' - Quit")
        print(f"\nViewing photos from: {self.photo_dir}")
        print(f"Selected photos will be saved to: {self.output_file}\n")
        
        while True:
            if not (0 <= self.current_index < len(self.photo_files)):
                print("Reached end of photos!")
                break
                
            current_file = self.photo_files[self.current_index]
            img = cv2.imread(str(current_file))
            
            if img is None:
                print(f"Error loading image: {current_file}")
                self.current_index += 1
                continue
            
            # Display image info
            print(f"\nCurrent photo ({self.current_index + 1}/{len(self.photo_files)}):")
            print(f"Filename: {current_file.name}")
            print("Status: ", end='')
            if current_file.name in self.selected_photos:
                print("Already selected")
            else:
                print("Not selected")
            
            # Show image
            cv2.imshow('Photo Viewer', img)
            
            # Handle keyboard input with shorter wait time for rapid skipping
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('y'):
                self.save_selection(current_file.name)
                self.current_index += 1
            elif key == ord('n') or key == 32:  # 'n' or spacebar
                self.current_index += 1
                # Add a tiny sleep to prevent too rapid cycling that might freeze
                cv2.waitKey(5)
            elif key == ord('b'):
                self.current_index = max(0, self.current_index - 1)
                cv2.waitKey(5)
            elif key == 255:  # No key pressed
                # Add a small delay when no key is pressed to prevent CPU overload
                cv2.waitKey(50)
        
        cv2.destroyAllWindows()

def main():
    if len(sys.argv) < 2:
        print("Usage: python photo_viewer.py <photo_directory> [output_file]")
        sys.exit(1)
    
    photo_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "selected_photos.txt"
    
    if not os.path.isdir(photo_dir):
        print(f"Error: {photo_dir} is not a valid directory")
        sys.exit(1)
    
    viewer = PhotoViewer(photo_dir, output_file)
    viewer.show_photos()

if __name__ == "__main__":
    main()

