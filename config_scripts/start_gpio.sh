#!/bin/bash

# Kill any existing pigpiod processes
sudo killall pigpiod 2>/dev/null

# Start pigpiod with verbose output
sudo pigpiod -v

# Wait a moment for the daemon to start
sleep 2

# Check if pigpiod is running
if pgrep pigpiod > /dev/null; then
    echo "pigpiod started successfully"
else
    echo "Failed to start pigpiod"
    exit 1
fi
