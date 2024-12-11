#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# Configuration variables
SWITCH_INTERVAL = 5  # Time in seconds between position switches
TOTAL_DURATION_MINUTES = 60
TOTAL_DURATION = TOTAL_DURATION_MINUTES * 60  # Total time in seconds to run
POSITION_A = 0      # First position angle
POSITION_B = 100    # Second position angle
MIN_DUTY = 2.5      # Duty cycle for 0 degrees
MAX_DUTY = 12.5     # Duty cycle for 180 degrees

# Set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define all available GPIO pins (excluding special purpose pins)
gpio_pins = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21]

# Set up all pins as PWM outputs
servos = {}
for pin in gpio_pins:
    GPIO.setup(pin, GPIO.OUT)
    servos[pin] = GPIO.PWM(pin, 50)
    servos[pin].start(7.5)

def angle_to_duty(angle):
    """Convert angle to duty cycle."""
    return MIN_DUTY + (angle/180.0 * (MAX_DUTY - MIN_DUTY))

def switch_positions():
    """Switch servos between two positions."""
    try:
        start_time = time.time()
        current_position = POSITION_A
        
        print(f"Starting position switching for {TOTAL_DURATION_MINUTES} minutes")
        print(f"Switching between {POSITION_A}° and {POSITION_B}° every {SWITCH_INTERVAL} seconds")
        
        while (time.time() - start_time) < TOTAL_DURATION:
            # Switch position
            current_position = POSITION_B if current_position == POSITION_A else POSITION_A
            duty = angle_to_duty(current_position)
            
            print(f"Moving to position: {current_position}°")
            for servo in servos.values():
                servo.ChangeDutyCycle(duty)
            
            # Wait for next switch
            time.sleep(SWITCH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nStopping servo movement")
    finally:
        # Clean up
        for servo in servos.values():
            servo.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    switch_positions()
