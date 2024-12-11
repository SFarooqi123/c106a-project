#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import argparse

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Control servos to switch between two positions.')
    parser.add_argument('-d', '--duration', type=int, default=60,
                      help='Total duration in minutes (default: 60)')
    parser.add_argument('-i', '--interval', type=float, default=5.0,
                      help='Time between position switches in seconds (default: 5.0)')
    parser.add_argument('-a', '--angle', type=int, default=100,
                      help='Maximum servo angle to switch to (default: 100)')
    return parser.parse_args()

# Servo Configuration
MIN_DUTY = 2.5      # Duty cycle for 0 degrees
MAX_DUTY = 12.5     # Duty cycle for 180 degrees
POSITION_A = 0      # First position angle (always 0)

# Set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define all available GPIO pins (excluding special purpose pins)
gpio_pins = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21]

def setup_servos():
    """Set up all pins as PWM outputs."""
    servos = {}
    for pin in gpio_pins:
        GPIO.setup(pin, GPIO.OUT)
        servos[pin] = GPIO.PWM(pin, 50)  # 50Hz frequency
        servos[pin].start(7.5)  # Start at middle position
    return servos

def angle_to_duty(angle):
    """Convert angle to duty cycle."""
    return MIN_DUTY + (angle/180.0 * (MAX_DUTY - MIN_DUTY))

def switch_positions(servos, duration_minutes, interval, max_angle):
    """Switch servos between two positions."""
    total_duration = duration_minutes * 60  # Convert to seconds
    
    try:
        start_time = time.time()
        current_position = POSITION_A
        
        print(f"\nStarting servo control:")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Interval: {interval} seconds")
        print(f"Switching between {POSITION_A}° and {max_angle}°")
        print("Press Ctrl+C to stop\n")
        
        while (time.time() - start_time) < total_duration:
            # Switch position
            current_position = max_angle if current_position == POSITION_A else POSITION_A
            duty = angle_to_duty(current_position)
            
            print(f"Moving to position: {current_position}°")
            for servo in servos.values():
                servo.ChangeDutyCycle(duty)
            
            # Wait for next switch
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nStopping servo movement")
    finally:
        # Clean up
        cleanup_servos(servos)

def cleanup_servos(servos):
    """Stop all servos and clean up GPIO."""
    for servo in servos.values():
        servo.stop()
    GPIO.cleanup()

def main():
    args = parse_args()
    servos = setup_servos()
    switch_positions(servos, args.duration, args.interval, args.angle)

if __name__ == "__main__":
    main()
