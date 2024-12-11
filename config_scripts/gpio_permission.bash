#!/bin/bash

# Add user to gpio group
sudo usermod -a -G gpio $USER

# Create udev rules for GPIO access
sudo tee /etc/udev/rules.d/90-gpio.rules << EOF
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"
SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c '\
        chown -R root:gpio /sys/class/gpio && chmod -R 770 /sys/class/gpio;\
        chown -R root:gpio /sys/devices/platform/soc/*.gpio/gpio && chmod -R 770 /sys/devices/platform/soc/*.gpio/gpio;\
        chown -R root:gpio /sys/devices/platform/gpio-fan/gpio && chmod -R 770 /sys/devices/platform/gpio-fan/gpio;\
'"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Create GPIO group if it doesn't exist
getent group gpio || sudo groupadd gpio

# Set permissions for GPIO devices
sudo chown root:gpio /dev/gpiomem || true
sudo chmod g+rw /dev/gpiomem || true

echo "GPIO permissions have been set up. Please log out and log back in for changes to take effect."