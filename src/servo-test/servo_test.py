#!/usr/bin/python3

import time
import argparse
import pigpio

class ServoController:
    """Controls a servo motor using pigpio"""
    def __init__(self, pin=17, freq=50):
        """
        Initialize servo on specified GPIO pin
        Default pin is 17, and frequency is 50Hz
        """
        self.pin = pin
        self.freq = freq
        
        try:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise RuntimeError("Could not connect to pigpio daemon")
            
            # Set up PWM at specified frequency
            self.pi.set_PWM_frequency(self.pin, freq)
            # Start at open position (2.5% duty cycle)
            self.set_angle(2.5)
            print(f"Initialized servo on GPIO pin {pin}")
            
        except Exception as e:
            print(f"Error initializing servo: {e}")
            if hasattr(self, 'pi') and self.pi.connected:
                self.pi.stop()
            raise
    
    def set_angle(self, angle):
        """Set servo to specified duty cycle (2.5-12.5)"""
        if not 2.5 <= angle <= 12.5:
            raise ValueError("Angle must be between 2.5 and 12.5 (duty cycle)")
        
        # Convert duty cycle (2.5-12.5%) to pulse width (500-2500µs)
        pulse_width = int((angle * 2000 / 10) + 500)
        self.pi.set_servo_pulsewidth(self.pin, pulse_width)
    
    def sweep(self, start_angle=2.5, end_angle=12.5, step=1, delay=0.5):
        """
        Sweep servo from start to end duty cycle
        step: duty cycle increment
        delay: time to wait between movements (seconds)
        """
        if start_angle > end_angle:
            step = -abs(step)
        
        current = start_angle
        while (step > 0 and current <= end_angle) or (step < 0 and current >= end_angle):
            self.set_angle(current)
            current += step
            time.sleep(delay)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if hasattr(self, 'pi') and self.pi.connected:
            self.pi.set_servo_pulsewidth(self.pin, 0)  # Stop PWM
            self.pi.stop()  # Disconnect from pigpiod
        print("Cleaned up GPIO resources")

def main():
    parser = argparse.ArgumentParser(description='Test servo motor control')
    parser.add_argument('-p', '--pin', type=int, default=17,
                      help='GPIO pin number connected to servo (default: 17)')
    parser.add_argument('-m', '--mode', choices=['angle', 'sweep'], default='sweep',
                      help='Test mode: single angle or sweep (default: sweep)')
    parser.add_argument('-a', '--angle', type=float, default=7.5,
                      help='Duty cycle to move to in angle mode (default: 7.5)')
    parser.add_argument('-d', '--delay', type=float, default=0.5,
                      help='Delay between movements in sweep mode (default: 0.5)')
    
    args = parser.parse_args()
    
    try:
        servo = ServoController(pin=args.pin)
        
        if args.mode == 'angle':
            print(f"Moving to duty cycle {args.angle}")
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
