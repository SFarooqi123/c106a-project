"""
Mock implementation of RPi.GPIO for testing servo control without Raspberry Pi hardware
"""

BOARD = "BOARD"
BCM = "BCM"
OUT = "OUT"
IN = "IN"

_current_mode = None
_pin_states = {}

def setmode(mode):
    global _current_mode
    print(f"[Mock] Setting GPIO mode to: {mode}")
    _current_mode = mode

def setup(pin, mode):
    _pin_states[pin] = {"mode": mode, "value": 0}
    print(f"[Mock] Setup pin {pin} as {mode}")

def cleanup():
    global _current_mode, _pin_states
    print("[Mock] Cleaning up GPIO")
    _current_mode = None
    _pin_states = {}

class PWM:
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        print(f"[Mock] Initializing PWM on pin {pin} with frequency {frequency}Hz")
    
    def start(self, duty_cycle):
        self.duty_cycle = duty_cycle
        print(f"[Mock] Starting PWM on pin {self.pin} with duty cycle {duty_cycle}%")
    
    def ChangeDutyCycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
        print(f"[Mock] Changed duty cycle to {duty_cycle}%")
    
    def stop(self):
        print(f"[Mock] Stopping PWM on pin {self.pin}")
