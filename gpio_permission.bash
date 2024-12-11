# Add your user to the gpio group
sudo usermod -a -G gpio $USER

# Create a udev rule for GPIO access
echo 'SUBSYSTEM=="bcm2835-gpiomem", KERNEL=="gpiomem", GROUP="gpio", MODE="0660"' | sudo tee /etc/udev/rules.d/90-gpio.rules

# Reload udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Create the GPIO device with correct permissions
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem