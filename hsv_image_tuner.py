#!/usr/bin/env python3
import cv2
import numpy as np
import argparse

def nothing(x):
    pass

def create_trackbars():
    # Create window for trackbars
    cv2.namedWindow('HSV Tuner')
    
    # Create trackbars for HSV ranges
    cv2.createTrackbar('H min', 'HSV Tuner', 0, 179, nothing)
    cv2.createTrackbar('H max', 'HSV Tuner', 179, 179, nothing)
    cv2.createTrackbar('S min', 'HSV Tuner', 0, 255, nothing)
    cv2.createTrackbar('S max', 'HSV Tuner', 255, 255, nothing)
    cv2.createTrackbar('V min', 'HSV Tuner', 0, 255, nothing)
    cv2.createTrackbar('V max', 'HSV Tuner', 255, 255, nothing)
    
    # Create trackbars for area thresholds
    cv2.createTrackbar('Area min', 'HSV Tuner', 100, 10000, nothing)
    cv2.createTrackbar('Area max', 'HSV Tuner', 5000, 10000, nothing)

def get_trackbar_values():
    # Get current positions of trackbars
    h_min = cv2.getTrackbarPos('H min', 'HSV Tuner')
    h_max = cv2.getTrackbarPos('H max', 'HSV Tuner')
    s_min = cv2.getTrackbarPos('S min', 'HSV Tuner')
    s_max = cv2.getTrackbarPos('S max', 'HSV Tuner')
    v_min = cv2.getTrackbarPos('V min', 'HSV Tuner')
    v_max = cv2.getTrackbarPos('V max', 'HSV Tuner')
    area_min = cv2.getTrackbarPos('Area min', 'HSV Tuner')
    area_max = cv2.getTrackbarPos('Area max', 'HSV Tuner')
    
    return h_min, h_max, s_min, s_max, v_min, v_max, area_min, area_max

def process_image(image, h_min, h_max, s_min, s_max, v_min, v_max, area_min, area_max):
    # Convert BGR to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Create HSV range mask
    lower_hsv = np.array([h_min, s_min, v_min])
    upper_hsv = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create result image
    result = image.copy()
    
    # Draw contours that meet area threshold
    detected_areas = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area_min <= area <= area_max:
            # Draw contour
            cv2.drawContours(result, [cnt], -1, (0, 255, 0), 2)
            
            # Get and draw bounding rectangle
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(result, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            # Calculate center
            center_x = x + w//2
            center_y = y + h//2
            
            # Display area and center coordinates
            text = f'Area: {int(area)}, Center: ({center_x},{center_y})'
            cv2.putText(result, text, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            detected_areas.append({
                'area': area,
                'center': (center_x, center_y),
                'bbox': (x, y, w, h)
            })
    
    return mask, result, detected_areas

def main():
    parser = argparse.ArgumentParser(description='HSV Tuner for Images')
    parser.add_argument('image_path', help='Path to the image file')
    args = parser.parse_args()
    
    # Read image
    original = cv2.imread(args.image_path)
    if original is None:
        print(f"Error: Could not read image from {args.image_path}")
        return
    
    # Resize image if it's too large
    max_dimension = 800
    height, width = original.shape[:2]
    if height > max_dimension or width > max_dimension:
        scale = max_dimension / max(height, width)
        original = cv2.resize(original, None, fx=scale, fy=scale)
    
    # Create trackbars
    create_trackbars()
    
    while True:
        # Get current trackbar values
        h_min, h_max, s_min, s_max, v_min, v_max, area_min, area_max = get_trackbar_values()
        
        # Process image with current values
        mask, result, detected_areas = process_image(
            original, h_min, h_max, s_min, s_max, v_min, v_max, area_min, area_max
        )
        
        # Show images
        cv2.imshow('Original', original)
        cv2.imshow('Mask', mask)
        cv2.imshow('Result', result)
        
        # Display HSV values and detected areas
        print('\r' + '-'*80, end='')
        print(f'\rHSV Range: [{h_min},{s_min},{v_min}] to [{h_max},{s_max},{v_max}], ' + 
              f'Area Range: {area_min} to {area_max}', end='')
        print(f'\nDetected {len(detected_areas)} objects', end='')
        
        # Break loop on 'q' press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save the current values to a file
            with open('hsv_values.txt', 'w') as f:
                f.write(f"HSV Range: [{h_min},{s_min},{v_min}] to [{h_max},{s_max},{v_max}]\n")
                f.write(f"Area Range: {area_min} to {area_max}\n")
                f.write("\nDetected Objects:\n")
                for i, obj in enumerate(detected_areas, 1):
                    f.write(f"Object {i}:\n")
                    f.write(f"  Area: {obj['area']:.2f}\n")
                    f.write(f"  Center: {obj['center']}\n")
                    f.write(f"  Bounding Box: {obj['bbox']}\n")
            print("\nValues saved to hsv_values.txt")
    
    # Clean up
    cv2.destroyAllWindows()
    print("\nFinal HSV and Area values:")
    print(f"HSV Range: [{h_min},{s_min},{v_min}] to [{h_max},{s_max},{v_max}]")
    print(f"Area Range: {area_min} to {area_max}")

if __name__ == "__main__":
    main()
