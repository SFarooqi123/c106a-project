# Autonomous Airdrop

![Plane at Berkeley Marina Cesar Chavez Park](plane_berkeley_marina.png)

![Theseus Logo](theseus_logo.png)

This repository contains code for the [Autonomous Airdrop](http://bit.ly/auto-airdrop) project- a fixed wing autonomous drone that can detect a color ground target and drop a payload (first-aid kit) onto it.

This project was built during the Fall 2024 semester at UC Berkeley in the [EECS 106A](https://pages.github.berkeley.edu/EECS-106/fa24-site/) robotics course. Our work was sponsored by [Theseus](https://www.ycombinator.com/launches/Ln6-theseus-gps-denied-navigation-for-drones), a Y Combinator company working on GPS-denied navigation for drones. 

The actual flight controls (rudder, elevator, ailerons, throttle) and navigation were handled by PX4, an open source autopilot platform for UAVs. We simply added a Raspberry Pi, Arducam color camera, and servo to the plane for automatic airdrop capability. The `flight_detection_servo.py` script would be run on the Pi during flight, where it would capture a stream of footage from the downward-facing camera on the plane's nose and trigger the servo to open and drop the payload (first-aid kit) when a specific target (red tarp) was detected according to our HSV target range.

We also include two scripts that we used to accelerate the process for tuning the HSV values based on previous flight footage (a series of images captured at 1 FPS) and setting up the Raspberry Pi network.

## Tools

### HSV Color Tuner
A tool for finding optimal HSV color ranges for object detection.

#### Features
- Interactive HSV and area threshold adjustment
- Real-time visualization
- Support for both image directories and live video
- Save/load configuration settings
- Object detection with area filtering
- Center point and bounding box visualization
- Photo navigation in directory mode

#### Usage
```bash
# For tuning with a directory of images
python3 hsv_tuner.py --image <path_to_image_directory>

# For tuning with live video
python3 hsv_tuner.py --video [camera_index]
```

### Network Configuration Script
A utility for setting up Raspberry Pi as a WiFi Access Point.

#### Features
- Automated setup of WiFi Access Point
- DHCP server configuration
- Network interface configuration
- Service management

#### Usage
```bash
sudo ./raspi_network_config.sh
```

## Installation

### Prerequisites
- Python 3.5 or higher
- OpenCV with Python bindings
- NumPy
- For Raspberry Pi configuration:
  - Raspbian/Raspberry Pi OS
  - `hostapd`
  - `dnsmasq`

### Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

3. Make scripts executable:
```bash
chmod +x raspi_network_config.sh
```

## Usage Examples

### Color Detection Tuning
1. Collect sample images of your target object
2. Run the HSV tuner:
```bash
python3 hsv_tuner.py --image ./sample_images
```
3. Use trackbars to adjust HSV ranges until object is properly detected
4. Save the configuration for use in your detection scripts

### Raspberry Pi Network Setup
1. Connect to your Raspberry Pi
2. Run the network configuration script:
```bash
sudo ./raspi_network_config.sh
```
3. Follow the prompts to configure your WiFi Access Point

## File Structure
```
.
├── hsv_tuner.py               # HSV color space tuning tool
├── flight_detection_servo.py  # Object detection and servo control
├── raspi_network_script.sh    # Network configuration utility
└── README.md
```

## Acknowledgments
- [Theseus](https://theseus.us) (YC S24) for sponsoring this project
- EECS 106A coursestaff
- UAVs @ Berkeley
- Alex Jordan for Berkeley MechE shop space
- OpenCV community for computer vision tools
- Raspberry Pi community for networking utilities
- AutomaticDAI, whose work our code was originally based off
- Windsurf Editor