#!/usr/bin/python3

import time
import argparse
import RPi.GPIO as GPIO

class ServoController:
    def __init__(self, pin=17, freq=50):
        """
        Initialize servo on specified GPIO pin
        Default pin is 17 (BCM numbering), and frequency is 50Hz
        """
        self.pin = pin
        self.freq = freq
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)  # Use BCM numbering
        GPIO.setup(self.pin, GPIO.OUT)
        
        # Setup PWM
        self.pwm = GPIO.PWM(self.pin, self.freq)
        self.pwm.start(0)  # Start with 0 duty cycle
        
        print(f"Initialized servo on GPIO pin {pin}")
    
    def angle_to_duty_cycle(self, angle):
        """Convert angle (0-180) to duty cycle (2-12)"""
        return ((angle / 180) * 10) + 2
    
    def set_angle(self, angle):
        """Set servo to specified angle (0-180 degrees)"""
        if not 0 <= angle <= 180:
            raise ValueError("Angle must be between 0 and 180 degrees")
        
        duty_cycle = self.angle_to_duty_cycle(angle)
        self.pwm.ChangeDutyCycle(duty_cycle)
        print(f"Moving to {angle} degrees (duty cycle: {duty_cycle:.1f})")
    
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
        self.pwm.stop()
        GPIO.cleanup()
        print("Cleaned up GPIO resources")

def main():
    parser = argparse.ArgumentParser(description='Test servo motor control')
    parser.add_argument('-p', '--pin', type=int, default=17,
                      help='GPIO pin number (BCM mode) connected to servo (default: 17)')
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
