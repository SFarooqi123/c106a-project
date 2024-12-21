# Computer Vision Tools for Object Detection

This repository contains a collection of tools for computer vision-based object detection and tracking, specifically designed for robotics applications.

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
sudo ./config_scripts/raspi_network_script.sh
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
chmod +x config_scripts/raspi_network_script.sh
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
sudo ./config_scripts/raspi_network_script.sh
```
3. Follow the prompts to configure your WiFi Access Point

## File Structure
```
.
├── hsv_tuner.py              # HSV color space tuning tool
├── flight_detection_servo.py  # Object detection and servo control
├── config_scripts/
│   └── raspi_network_script.sh # Network configuration utility
└── README.md
```

## Contributing
Feel free to submit issues and enhancement requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- [Theseus](https://theseus.us) (YC S24) for sponsoring this project
- EECS 106A coursestaff
- UAVs @ Berkeley
- Alex Jordan for Berkeley MechE shop space
- OpenCV community for computer vision tools
- Raspberry Pi community for networking utilities
- AutomaticDAI, whose work our code was originally based off
- Windsurf Editor