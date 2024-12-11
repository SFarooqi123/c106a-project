#!/bin/bash

# Function to check if the script is run as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi
}

# Function to undo Wi-Fi Access Point Configuration
undo_ap_configuration() {
    echo "=== Undoing Wi-Fi Access Point Configuration ==="

    # Remove hostapd configuration file
    echo "Removing /etc/hostapd/hostapd.conf..."
    rm -f /etc/hostapd/hostapd.conf

    # Restore original dnsmasq configuration
    echo "Restoring original dnsmasq configuration..."
    mv /etc/dnsmasq.conf.bak /etc/dnsmasq.conf

    # Disable and stop hostapd and dnsmasq services
    echo "Disabling and stopping hostapd and dnsmasq services..."
    systemctl stop hostapd
    systemctl disable hostapd
    systemctl stop dnsmasq
    systemctl disable dnsmasq

    # Remove static IP configuration for wlan0 in /etc/dhcpcd.conf
    echo "Removing static IP configuration for wlan0..."
    sed -i '/interface wlan0/,/nohook wpa_supplicant/d' /etc/dhcpcd.conf

    # Restart dhcpcd service to apply changes
    echo "Restarting dhcpcd service..."
    systemctl restart dhcpcd

    # Optionally, remove hostapd and dnsmasq if not needed
    echo "Removing hostapd and dnsmasq packages..."
    apt remove --purge -y hostapd dnsmasq

    # Reboot system to finalize the undo process
    echo "Rebooting system to apply all changes..."
    reboot
}

# Main script execution
check_root
undo_ap_configuration
