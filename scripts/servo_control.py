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

    # Constants for PWM
    PWM_CHIP = 0  # PWM chip number
    PWM_CHANNEL = 1  # PWM channel for GPIO 17
    FREQUENCY = 50  # 50Hz for servos
    MIN_DUTY = 2.5  # 2.5% duty cycle for 0 degrees
    MAX_DUTY = 12.5  # 12.5% duty cycle for 180 degrees

    try:
        # First try to use the PWM interface
        pwm_path = f"/sys/class/pwm/pwmchip{PWM_CHIP}/pwm{PWM_CHANNEL}"
        
        # Export PWM channel if not already exported
        if not os.path.exists(pwm_path):
            with open(f"/sys/class/pwm/pwmchip{PWM_CHIP}/export", 'w') as f:
                f.write(str(PWM_CHANNEL))
            time.sleep(0.1)  # Wait for export
        
        # Set period (in nanoseconds) for 50Hz
        period_ns = int(1e9 / FREQUENCY)  # 20ms period for 50Hz
        with open(f"{pwm_path}/period", 'w') as f:
            f.write(str(period_ns))
        
        # Enable PWM
        with open(f"{pwm_path}/enable", 'w') as f:
            f.write('1')
            
        print("Successfully set up PWM for servo control")
        
    except Exception as e:
        print(f"Error setting up PWM: {str(e)}")
        print("\nDebug information:")
        print("PWM devices available:")
        os.system("ls -l /sys/class/pwm/")
        sys.exit(1)

    def set_angle(angle):
        """Convert angle to duty cycle and set PWM"""
        try:
            # Convert angle to duty cycle (2.5% - 12.5%)
            duty_cycle = MIN_DUTY + (angle / 180.0 * (MAX_DUTY - MIN_DUTY))
            # Convert duty cycle to nanoseconds
            duty_ns = int(period_ns * duty_cycle / 100)
            
            # Set duty cycle
            with open(f"{pwm_path}/duty_cycle", 'w') as f:
                f.write(str(duty_ns))
                
        except Exception as e:
            print(f"Error setting servo angle: {str(e)}")

    def cleanup():
        """Cleanup PWM"""
        try:
            # Disable PWM
            with open(f"{pwm_path}/enable", 'w') as f:
                f.write('0')
            
            # Unexport PWM channel
            with open(f"/sys/class/pwm/pwmchip{PWM_CHIP}/unexport", 'w') as f:
                f.write(str(PWM_CHANNEL))
        except:
            pass

    # Get command line arguments
    args = parse_args()

    try:
        start_time = time.time()
        total_duration = args.duration * 60  # Convert to seconds
        current_position = 0
        
        print("\nStarting servo control:")
        print(f"Duration: {args.duration} minutes")
        print(f"Interval: {args.interval} seconds")
        print(f"Switching between 0° and {args.angle}°")
        print(f"Using GPIO 17 with hardware PWM")
        print("Press Ctrl+C to stop\n")
        
        while (time.time() - start_time) < total_duration:
            # Switch between positions
            current_position = args.angle if current_position == 0 else 0
            
            print(f"Moving to position: {current_position}°")
            set_angle(current_position)
            
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
