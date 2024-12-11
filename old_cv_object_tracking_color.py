#!/usr/bin/python3

# ------------------------------------------------------------------------------
# rpi-object-detection
# ------------------------------------------------------------------------------
# This is a blob detection program which intend to find the biggest blob
# in a given picture taken by a camera and return its central position.
#
# Key Steps:
# 1. Image Filtering
# 2. Image Segmentation
# 3. Detect Blobs
# 4. Filter Blobs using a criteria
# 5. Track Blobs
# ------------------------------------------------------------------------------
# automaticdai
# YF Robotics Labrotary
# Instagram: yfrobotics
# Twitter: @yfrobotics
# Website: https://yfrobotics.github.io/
# ------------------------------------------------------------------------------

# EECS 106A Theseus Project 12/7/24
# Cited from https://github.com/automaticdai/rpi-object-detection

import os
import sys
import cv2
import time
import numpy as np
import time
import math
import RPi.GPIO as GPIO


# Add src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.picamera_utils import is_raspberry_camera, get_picamera


# Camera configuration
CAMERA_DEVICE_ID = 0
IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
IS_RASPI_CAMERA = is_raspberry_camera()

# Servo configuration
SERVO_PIN = 11  # Physical pin number (GPIO17 maps to physical pin 11)
SERVO_FREQUENCY = 50  # Standard servo frequency in Hz
SERVO_OPEN_ANGLE = 2.5  # Duty cycle for open position
SERVO_CLOSE_ANGLE = 12.5  # Duty cycle for closed position
SERVO_MOVE_DELAY = 0.5  # Delay in seconds for servo movement
SERVO_TRIGGER_AREA = 1000  # Minimum area to trigger servo

# Detection parameters
DETECTION_THRESHOLD_AREA = 500  # Minimum area to consider valid detection
MAX_STORED_COLORS = 10  # Maximum number of colors to store
DEFAULT_WAIT_TIME = 33  # Wait time between frames in milliseconds
ESC_KEY = 27  # ASCII code for ESC key
MIN_AREA = 100  # Minimum area for valid blob detection

# Default HSV color range for blue
DEFAULT_HSV_MIN = np.array([0, 100, 100], dtype=np.uint8)  # Lower bound for blue in HSV
DEFAULT_HSV_MAX = np.array([10, 255, 255], dtype=np.uint8)  # Upper bound for blue in HSV

# Text overlay parameters
TEXT_COLOR_BGR = (0, 255, 0)  # Green color for text
TEXT_COLOR_GRAY = (255, 255, 255)  # White color for text in grayscale
TEXT_ROW_SIZE = 20  # pixels
TEXT_LEFT_MARGIN = 24  # pixels
TEXT_FONT_SIZE = 1
TEXT_FONT_THICKNESS = 1

# Color space configuration
USE_BGR_MODE = False  # Set to False if camera feed shows red as blue

# Initialize global variables
fps = 0
hsv_min = DEFAULT_HSV_MIN
hsv_max = DEFAULT_HSV_MAX
colors = []

print("Using raspi camera: ", IS_RASPI_CAMERA)


def move_servo_to(angle):
    """Move servo to specified angle."""
    servo.ChangeDutyCycle(angle)
    time.sleep(SERVO_MOVE_DELAY)  # Give the servo time to move
    servo.ChangeDutyCycle(0)  # Stop sending signal to avoid jitter

def close_claw():
    """Close the servo claw."""
    print("Closing claw...")
    move_servo_to(SERVO_CLOSE_ANGLE)

def open_claw():
    """Open the servo claw."""
    print("Opening claw...")
    move_servo_to(SERVO_OPEN_ANGLE)

def isset(v):
    try:
        type (eval(v))
    except:
        return 0
    else:
        return 1


def on_mouse_click(event, x, y, flags, frame):
    global colors
    
    if event == cv2.EVENT_LBUTTONUP:
        color_bgr = frame[y, x]
        color_rgb = tuple(reversed(color_bgr))
        
        color_hsv = rgb2hsv(color_rgb[0], color_rgb[1], color_rgb[2])
        print(f"RGB: {color_rgb}, HSV: {color_hsv}")
        
        colors.append(color_hsv)
        if len(colors) > MAX_STORED_COLORS:
            colors.pop(0)  # Remove oldest color if limit reached


# R, G, B values are [0, 255].
# Normally H value is [0, 359]. S, V values are [0, 1].
# However in opencv, H is [0,179], S, V values are [0, 255].
# Reference: https://docs.opencv.org/3.4/de/d25/imgproc_color_conversions.html
def hsv2rgb(h, s, v):
    h = float(h) * 2
    s = float(s) / 255
    v = float(v) / 255
    h60 = h / 60.0
    h60f = math.floor(h60)
    hi = int(h60f) % 6
    f = h60 - h60f
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = 0, 0, 0
    if hi == 0: r, g, b = v, t, p
    elif hi == 1: r, g, b = q, v, p
    elif hi == 2: r, g, b = p, v, t
    elif hi == 3: r, g, b = p, q, v
    elif hi == 4: r, g, b = t, p, v
    elif hi == 5: r, g, b = v, p, q
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return (r, g, b)


def rgb2hsv(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = df/mx
    v = mx

    h = int(h / 2)
    s = int(s * 255)
    v = int(v * 255)

    return (h, s, v)


def visualize_fps(image, fps: int):
    if len(np.shape(image)) < 3:
        text_color = TEXT_COLOR_GRAY
    else:
        text_color = TEXT_COLOR_BGR
    
    # Draw the FPS counter
    fps_text = 'FPS = {:.1f}'.format(fps)
    text_location = (TEXT_LEFT_MARGIN, TEXT_ROW_SIZE)
    cv2.putText(image, fps_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                TEXT_FONT_SIZE, text_color, TEXT_FONT_THICKNESS)

    return image


def process_frame(frame):
    # Swap red and blue channels for correct color
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Convert to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    
    # Find the color using a color threshold
    thresh = cv2.inRange(hsv, hsv_min, hsv_max)
    thresh2 = thresh.copy()

    # Find contours in the threshold image
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # Finding contour with maximum area
    max_area = 0
    best_cnt = None
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            best_cnt = cnt

    # Process the detected blob
    if best_cnt is not None and max_area > MIN_AREA:
        M = cv2.moments(best_cnt)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            
            # Draw the detection
            cv2.drawContours(frame, [best_cnt], -1, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, f'Area: {int(max_area)}', (cx, cy - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            print(f"Detected blob at ({cx}, {cy}) with area {max_area}")
            
            # Trigger servo if area is large enough
            if max_area > SERVO_TRIGGER_AREA:
                open_claw()
                time.sleep(2)
                close_claw()
    else:
        print("[Warning] No valid blob detected or too small")

    # Convert back to BGR for display
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    return frame, thresh2


if __name__ == "__main__":
    try:
        # Setup GPIO for servo
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        servo = GPIO.PWM(SERVO_PIN, SERVO_FREQUENCY)
        servo.start(SERVO_OPEN_ANGLE)

        # To capture video from webcam.
        if IS_RASPI_CAMERA:
            cap = get_picamera(IMAGE_WIDTH, IMAGE_HEIGHT)
            cap.start()
        else:
            # create video capture
            cap = cv2.VideoCapture(CAMERA_DEVICE_ID)
            if not cap.isOpened():
                raise Exception("Failed to open camera")
            # set resolution to 320x240 to reduce latency
            cap.set(3, IMAGE_WIDTH)
            cap.set(4, IMAGE_HEIGHT)

        start_time = time.time()
        frame_count = 0
        while True:
            # ----------------------------------------------------------------------
            # record start time
            start_time = time.time()
            # Read the frames frome a camera
            if IS_RASPI_CAMERA:
                frame = cap.capture_array()
            else:
                _, frame = cap.read()

            frame = cv2.blur(frame,(3,3))

            # Or get it from a JPEG
            # frame = cv2.imread('frame0010.jpg', 1)

            # Process frame
            processed_frame, thresh2 = process_frame(frame)
            
            # Show the original and processed image
            cv2.imshow('frame', visualize_fps(processed_frame, fps))
            cv2.imshow('thresh', visualize_fps(thresh2, fps))
            # ----------------------------------------------------------------------
            # record end time
            end_time = time.time()
            # calculate FPS
            seconds = end_time - start_time
            fps = 1.0 / seconds
            print("Estimated fps:{0:0.1f}".format(fps));
            # if key pressed is 'Esc' then exit the loop
            if cv2.waitKey(DEFAULT_WAIT_TIME) == ESC_KEY:
                break
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Cleanup
        if 'cap' in locals():
            if IS_RASPI_CAMERA:
                cap.stop()
            else:
                cap.release()
        cv2.destroyAllWindows()
        servo.stop()
        GPIO.cleanup()
