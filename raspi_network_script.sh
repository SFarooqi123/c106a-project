#!/bin/bash

# Variables (modify as needed)
INTERFACE="wlan0"      # Wi-Fi interface to use
SSID="RaspberryPi_AP"  # Access Point SSID
PASSWORD="raspberry"   # Access Point password
AP_IP="192.168.4.1"    # Static IP for the Access Point
DHCP_RANGE_START="192.168.4.2"  # Start of DHCP range
DHCP_RANGE_END="192.168.4.20"   # End of DHCP range
DHCP_LEASE_TIME="24h"  # DHCP lease time

# Function to check if the script is run as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi
}

# Function to print current network settings
print_network_settings() {
    echo "=== Current Network Settings ==="
    echo "IP Address and Network Interfaces:"
    ip addr show

    echo "Routing Table:"
    ip route show

    echo "DNS Configuration:"
    cat /etc/resolv.conf

    echo "Wi-Fi Interfaces:"
    iw dev
}

# Function to configure Wi-Fi Access Point
configure_ap() {
    echo "=== Configuring Wi-Fi Access Point ==="

    echo "Installing required packages..."
    apt update && apt install -y hostapd dnsmasq

    echo "Configuring hostapd..."
    cat > /etc/hostapd/hostapd.conf <<EOF
interface=$INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=7
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

    sed -i "s|#DAEMON_CONF=.*|DAEMON_CONF=\"/etc/hostapd/hostapd.conf\"|g" /etc/default/hostapd

    echo "Configuring dnsmasq..."
    mv /etc/dnsmasq.conf /etc/dnsmasq.conf.bak
    cat > /etc/dnsmasq.conf <<EOF
interface=$INTERFACE
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,255.255.255.0,$DHCP_LEASE_TIME
EOF

    echo "Configuring static IP for $INTERFACE..."
    cat >> /etc/dhcpcd.conf <<EOF

interface $INTERFACE
static ip_address=$AP_IP/24
nohook wpa_supplicant
EOF
    systemctl restart dhcpcd

    echo "Starting services..."
    systemctl unmask hostapd
    systemctl enable hostapd
    systemctl start hostapd
    systemctl restart dnsmasq

    echo "Wi-Fi Access Point configuration complete!"
    echo "SSID: $SSID"
    echo "Password: $PASSWORD"
}

# Main script execution
check_root
print_network_settings
read -p "Do you want to configure the Raspberry Pi as a Wi-Fi Access Point? (y/n): " choice
if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
    configure_ap
else
    echo "Access Point configuration skipped."
fi
