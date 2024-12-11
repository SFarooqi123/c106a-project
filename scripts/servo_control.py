#!/usr/bin/env python3
import time
import argparse
import sys
import platform
import os

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

def main():
    # Check if running as root
    if os.geteuid() != 0:
        print("Error: This script must be run as root (sudo)")
        print("Please run: sudo python3 servo_control.py")
        sys.exit(1)

    # Check if running on Raspberry Pi
    if not platform.machine().startswith('arm'):
        print("Error: This script must be run on a Raspberry Pi")
        print("Current platform:", platform.machine())
        sys.exit(1)
        
    # Import gpiod library
    try:
        import gpiod
    except ImportError:
        print("\nError: Could not import gpiod.")
        print("Please install required packages:")
        print("sudo apt-get update")
        print("sudo apt-get install gpiod python3-libgpiod")
        sys.exit(1)

    # Servo Configuration
    MIN_DUTY = 2.5      # Duty cycle for 0 degrees
    MAX_DUTY = 12.5     # Duty cycle for 180 degrees
    POSITION_A = 0      # First position angle (always 0)

    # Get command line arguments
    args = parse_args()

    # Get GPIO chip
    try:
        chip = gpiod.Chip('gpiochip0')
    except Exception as e:
        print(f"Error accessing GPIO chip: {str(e)}")
        print("Make sure you have the correct permissions and gpiod is properly installed.")
        sys.exit(1)

    # Define all available GPIO pins (excluding special purpose pins)
    gpio_pins = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21]
    
    # Configure GPIO lines
    lines = []
    try:
        for pin in gpio_pins:
            line = chip.get_line(pin)
            line.request(consumer="servo_control", type=gpiod.LINE_REQ_DIR_OUT)
            lines.append(line)
    except Exception as e:
        print(f"Error configuring GPIO lines: {str(e)}")
        sys.exit(1)

    def angle_to_value(angle):
        """Convert angle to GPIO value (0 or 1)."""
        # Simplified PWM simulation using digital signals
        return 1 if angle > 90 else 0

    def cleanup():
        """Release all GPIO lines."""
        for line in lines:
            try:
                line.release()
            except Exception as e:
                print(f"Warning: Error during cleanup: {str(e)}")

    def switch_positions(duration_minutes, interval, max_angle):
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
                value = angle_to_value(current_position)
                
                print(f"Moving to position: {current_position}°")
                for line in lines:
                    line.set_value(value)
                
                # Wait for next switch
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping servo movement")
        finally:
            cleanup()

    # Run the main control loop
    try:
        switch_positions(args.duration, args.interval, args.angle)
    except Exception as e:
        print(f"Error during servo control: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
