#!/usr/bin/env python3

import lgpio
import time

# GPIO pin configuration
SERVO_PIN = 17
FREQ = 50        # PWM frequency (Hz)
RANGE = 20000    # PWM range (period in microseconds)

try:
    # Initialize lgpio
    h = lgpio.gpiochip_open(0)
    
    # Configure GPIO pin for PWM
    lgpio.gpio_claim_output(h, SERVO_PIN)
    
    # Configure PWM
    lgpio.tx_pwm(h, SERVO_PIN, FREQ, 7.5)  # Start at middle position (7.5% duty cycle)
    print(f"Initialized servo on GPIO {SERVO_PIN}")
    
    while True:
        # Move to minimum position (2.5% duty cycle)
        print("Moving to min position")
        lgpio.tx_pwm(h, SERVO_PIN, FREQ, 2.5)
        time.sleep(1)
        
        # Move to middle position (7.5% duty cycle)
        print("Moving to mid position")
        lgpio.tx_pwm(h, SERVO_PIN, FREQ, 7.5)
        time.sleep(1)
        
        # Move to maximum position (12.5% duty cycle)
        print("Moving to max position")
        lgpio.tx_pwm(h, SERVO_PIN, FREQ, 12.5)
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping servo")
finally:
    # Cleanup
    lgpio.gpio_free(h, SERVO_PIN)
    lgpio.gpiochip_close(h)
    print("Cleanup completed")