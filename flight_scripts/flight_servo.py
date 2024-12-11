#!/usr/bin/env python3

import lgpio
import time
from time import sleep

# Configuration variables
GPIO_PIN = 17          # GPIO pin number for servo
INTERVAL_SEC = 5.0     # Time between movements in seconds
TOTAL_MINUTES = 5.0    # Total duration to run in minutes
TARGET_ANGLE = 90      # Target angle to move to (in degrees)
START_ANGLE = 0        # Starting angle (in degrees)

# PWM Configuration
FREQ = 50             # PWM frequency (Hz)
MIN_DUTY = 2.5        # Duty cycle for 0 degrees
MAX_DUTY = 12.5       # Duty cycle for 180 degrees

def angle_to_duty(angle):
    """Convert angle (0-180) to duty cycle (2.5-12.5)"""
    return MIN_DUTY + (angle / 180.0) * (MAX_DUTY - MIN_DUTY)

try:
    # Initialize lgpio
    h = lgpio.gpiochip_open(0)
    
    # Configure GPIO pin for PWM
    lgpio.gpio_claim_output(h, GPIO_PIN)
    
    # Start PWM at start angle
    start_duty = angle_to_duty(START_ANGLE)
    lgpio.tx_pwm(h, GPIO_PIN, FREQ, start_duty)
    print(f"Initialized servo on GPIO {GPIO_PIN}")
    
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
            duty = angle_to_duty(TARGET_ANGLE)
            lgpio.tx_pwm(h, GPIO_PIN, FREQ, duty)
            print(f"Moving to {TARGET_ANGLE}°")
        else:
            current_angle = START_ANGLE
            duty = angle_to_duty(START_ANGLE)
            lgpio.tx_pwm(h, GPIO_PIN, FREQ, duty)
            print(f"Moving to {START_ANGLE}°")
        
        # Wait for next movement
        sleep(INTERVAL_SEC)
    
    # Return to start position when done
    duty = angle_to_duty(START_ANGLE)
    lgpio.tx_pwm(h, GPIO_PIN, FREQ, duty)
    print("\nFinished! Returning to start position.")
    
except KeyboardInterrupt:
    print("\nProgram stopped by user")
finally:
    # Cleanup
    lgpio.gpio_free(h, GPIO_PIN)
    lgpio.gpiochip_close(h)
    print("Servo cleanup completed")