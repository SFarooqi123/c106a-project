#!/usr/bin/python3

import time
import argparse
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory

class ServoController:
    def __init__(self, pin=17, freq=50):
        """
        Initialize servo on specified GPIO pin
        Default pin is 17 (same as in cv_object_tracking_color.py)
        """
        self.pin = pin
        # Use pigpio for better PWM control
        factory = PiGPIOFactory()
        self.servo = Servo(pin, pin_factory=factory)
        print(f"Initialized servo on GPIO pin {pin}")
    
    def angle_to_value(self, angle):
        """Convert angle (0-180) to gpiozero value (-1 to 1)"""
        return (angle / 90.0) - 1.0
    
    def set_angle(self, angle):
        """Set servo to specified angle (0-180 degrees)"""
        if not 0 <= angle <= 180:
            raise ValueError("Angle must be between 0 and 180 degrees")
        
        value = self.angle_to_value(angle)
        self.servo.value = value
        print(f"Moving to {angle} degrees (value: {value:.2f})")
    
    def sweep(self, start_angle=0, end_angle=180, step=10, delay=0.5):
        """
        Sweep servo from start_angle to end_angle
        step: angle increment
        delay: time to wait between movements (seconds)
        """
        if start_angle > end_angle:
            step = -abs(step)
        
        print(f"Sweeping from {start_angle} to {end_angle} degrees")
        for angle in range(start_angle, end_angle + (1 if step > 0 else -1), step):
            self.set_angle(angle)
            time.sleep(delay)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        self.servo.close()
        print("Cleaned up GPIO resources")

def main():
    parser = argparse.ArgumentParser(description='Test servo motor control')
    parser.add_argument('-p', '--pin', type=int, default=17,
                      help='GPIO pin number connected to servo (default: 17)')
    parser.add_argument('-m', '--mode', choices=['angle', 'sweep'], default='sweep',
                      help='Test mode: single angle or sweep (default: sweep)')
    parser.add_argument('-a', '--angle', type=float, default=90,
                      help='Angle to move to in angle mode (default: 90)')
    parser.add_argument('-d', '--delay', type=float, default=0.5,
                      help='Delay between movements in sweep mode (default: 0.5)')
    
    args = parser.parse_args()
    
    try:
        servo = ServoController(pin=args.pin)
        
        if args.mode == 'angle':
            print(f"Moving to {args.angle} degrees")
            servo.set_angle(args.angle)
            time.sleep(1)  # Hold position briefly
        else:  # sweep mode
            servo.sweep(delay=args.delay)
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'servo' in locals():
            servo.cleanup()

if __name__ == "__main__":
    main()
