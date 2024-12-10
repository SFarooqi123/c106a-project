#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# Configuration variables
REPEAT_INTERVAL = 5  # Time in seconds between sweep cycles
TOTAL_DURATION_MINUTES = 60
TOTAL_DURATION = TOTAL_DURATION_MINUTES * 60  # Total time in seconds to run the program
SWEEP_STEP = 10     # Step size for servo movement in degrees
SWEEP_DELAY = 0.5   # Delay between each angle change in seconds
MIN_ANGLE = 0       # Minimum angle for servo
MAX_ANGLE = 180     # Maximum angle for servo
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
    # Create PWM instance for each pin at 50Hz (standard for servos)
    servos[pin] = GPIO.PWM(pin, 50)
    # Start PWM with neutral position (7.5% duty cycle)
    servos[pin].start(7.5)

def sweep_all_servos():
    try:
        start_time = time.time()
        while True:
            cycle_start = time.time()
            
            # Sweep from MIN to MAX degrees
            for angle in range(MIN_ANGLE, MAX_ANGLE + 1, SWEEP_STEP):
                if time.time() - start_time >= TOTAL_DURATION:
                    raise KeyboardInterrupt  # Use this to trigger cleanup
                
                duty = MIN_DUTY + (angle/180.0 * (MAX_DUTY - MIN_DUTY))
                print(f"Moving all servos to {angle} degrees")
                for servo in servos.values():
                    servo.ChangeDutyCycle(duty)
                time.sleep(SWEEP_DELAY)
            
            # Sweep back from MAX to MIN degrees
            for angle in range(MAX_ANGLE, MIN_ANGLE - 1, -SWEEP_STEP):
                if time.time() - start_time >= TOTAL_DURATION:
                    raise KeyboardInterrupt  # Use this to trigger cleanup
                    
                duty = MIN_DUTY + (angle/180.0 * (MAX_DUTY - MIN_DUTY))
                print(f"Moving all servos to {angle} degrees")
                for servo in servos.values():
                    servo.ChangeDutyCycle(duty)
                time.sleep(SWEEP_DELAY)
            
            # Wait for the next cycle
            elapsed_cycle = time.time() - cycle_start
            if elapsed_cycle < REPEAT_INTERVAL:
                time.sleep(REPEAT_INTERVAL - elapsed_cycle)
            
            if time.time() - start_time >= TOTAL_DURATION:
                raise KeyboardInterrupt  # Use this to trigger cleanup

    except KeyboardInterrupt:
        print("\nStopping servo movement")
        # Clean up
        for servo in servos.values():
            servo.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    print(f"Starting servo sweep on all GPIO pins")
    print(f"Will run for {TOTAL_DURATION} seconds, repeating every {REPEAT_INTERVAL} seconds")
    print("Press Ctrl+C to stop")
    sweep_all_servos()
