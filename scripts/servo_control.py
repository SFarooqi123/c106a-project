#!/usr/bin/env python3
import time
import sys
import argparse
import platform
import os

def parse_args():
    parser = argparse.ArgumentParser(description='Control servo motor positions')
    parser.add_argument('-d', '--duration', type=float, default=5.0,
                      help='Duration to run in minutes (default: 5.0)')
    parser.add_argument('-i', '--interval', type=float, default=5.0,
                      help='Time between position switches in seconds (default: 5.0)')
    parser.add_argument('-a', '--angle', type=int, default=100,
                      help='Maximum servo angle to switch to (default: 100)')
    parser.add_argument('-p', '--pin', type=int, default=18,
                      help='GPIO pin number (default: 18)')
    return parser.parse_args()

def main():
    # Check if running on Raspberry Pi
    if not os.path.exists('/sys/firmware/devicetree/base/model'):
        print("Error: This script must be run on a Raspberry Pi.")
        print("Current platform:", platform.machine())
        sys.exit(1)
    
    with open('/sys/firmware/devicetree/base/model', 'r') as f:
        model = f.read()
        if 'Raspberry Pi' not in model:
            print("Error: This script must be run on a Raspberry Pi.")
            print("Current device:", model)
            sys.exit(1)

    try:
        import gpiod
    except ImportError:
        print("\nError: Could not import gpiod.")
        print("Please install required packages:")
        print("sudo apt-get update")
        print("sudo apt-get install python3-libgpiod gpiod")
        sys.exit(1)

    # Get command line arguments
    args = parse_args()

    try:
        # Open GPIO chip
        chip = gpiod.Chip('gpiochip0')
        
        # Get GPIO line
        line = chip.get_line(args.pin)
        
        # Request GPIO line
        config = gpiod.LineRequest()
        config.request_type = gpiod.LINE_REQ_DIR_OUT
        config.consumer = "servo_control"
        line.request(config)
        
    except Exception as e:
        print(f"Error setting up GPIO: {str(e)}")
        print("Make sure you have the correct permissions and gpiod is properly installed.")
        sys.exit(1)

    def cleanup():
        """Release GPIO line"""
        try:
            line.release()
        except:
            pass

    try:
        start_time = time.time()
        total_duration = args.duration * 60  # Convert to seconds
        current_position = 0
        
        print("\nStarting servo control:")
        print(f"Duration: {args.duration} minutes")
        print(f"Interval: {args.interval} seconds")
        print(f"Switching between 0° and {args.angle}°")
        print(f"Using GPIO pin: {args.pin}")
        print("Press Ctrl+C to stop\n")
        
        while (time.time() - start_time) < total_duration:
            # Switch between positions
            current_position = args.angle if current_position == 0 else 0
            
            # For servos, we'll simulate PWM by toggling quickly
            print(f"Moving to position: {current_position}°")
            
            # Simple digital output for testing
            line.set_value(1 if current_position > 90 else 0)
            
            # Wait for next switch
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nStopping servo movement")
    except Exception as e:
        print(f"Error during servo control: {str(e)}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
