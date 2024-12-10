#!/usr/bin/env python3
import cv2
import numpy as np

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

def main():
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    # Create trackbars
    create_trackbars()
    
    while True:
        # Read frame from camera
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
            
        # Swap red and blue channels
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        
        # Get current trackbar values
        h_min, h_max, s_min, s_max, v_min, v_max, area_min, area_max = get_trackbar_values()
        
        # Create HSV range mask
        lower_hsv = np.array([h_min, s_min, v_min])
        upper_hsv = np.array([h_max, s_max, v_max])
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create result image
        result = frame.copy()
        
        # Draw contours that meet area threshold
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
        
        # Convert back to BGR for display
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        
        # Show images
        cv2.imshow('Original', frame)
        cv2.imshow('Mask', mask)
        cv2.imshow('Result', result)
        
        # Display HSV values
        print(f'\rHSV Range: [{h_min},{s_min},{v_min}] to [{h_max},{s_max},{v_max}], ' + 
              f'Area Range: {area_min} to {area_max}', end='')
        
        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print("\nFinal HSV and Area values:")
    print(f"HSV Range: [{h_min},{s_min},{v_min}] to [{h_max},{s_max},{v_max}]")
    print(f"Area Range: {area_min} to {area_max}")

if __name__ == "__main__":
    main()
