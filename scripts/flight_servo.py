from gpiozero import Servo
from time import sleep
import time

# Configuration variables
GPIO_PIN = 17          # GPIO pin number for servo
INTERVAL_SEC = 5.0     # Time between movements in seconds
TOTAL_MINUTES = 5.0    # Total duration to run in minutes
TARGET_ANGLE = 90      # Target angle to move to (in degrees)
START_ANGLE = 0        # Starting angle (in degrees)

# Convert angles to servo positions (-1 to 1)
def angle_to_value(angle):
    """Convert angle (0-180) to servo value (-1 to 1)"""
    return -1 + (angle / 90.0)  # Maps 0° to -1, 90° to 0, and 180° to 1

# Initialize servo
servo = Servo(GPIO_PIN)
print(f"Initialized servo on GPIO {GPIO_PIN}")

try:
    start_time = time.time()
    end_time = start_time + (TOTAL_MINUTES * 60)
    current_angle = START_ANGLE
    
    print(f"\nStarting servo control:")
    print(f"Duration: {TOTAL_MINUTES} minutes")
    print(f"Interval: {INTERVAL_SEC} seconds")
    print(f"Target angle: {TARGET_ANGLE}°")
    print("Press Ctrl+C to stop\n")
    
    while time.time() < end_time:
        # Switch between start and target angles
        if current_angle == START_ANGLE:
            current_angle = TARGET_ANGLE
            servo.value = angle_to_value(TARGET_ANGLE)
            print(f"Moving to {TARGET_ANGLE}°")
        else:
            current_angle = START_ANGLE
            servo.value = angle_to_value(START_ANGLE)
            print(f"Moving to {START_ANGLE}°")
        
        # Wait for next movement
        sleep(INTERVAL_SEC)
    
    # Return to start position when done
    servo.value = angle_to_value(START_ANGLE)
    print("\nFinished! Returning to start position.")
    
except KeyboardInterrupt:
    print("\nProgram stopped by user")
finally:
    # Cleanup
    servo.close()
    print("Servo cleanup completed")