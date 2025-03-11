#!/usr/bin/env bash
#
# setup.sh
#
# Usage:  ./setup.sh
#
# This script configures the IP address, installs required system packages,
# and then installs Python dependencies (including OpenCV with contrib modules,
# GStreamer plugins, and robotpy).

set -e  # Exit immediately if a command exits with a non-zero status

echo "=== Setting device IP to 10.85.61.30 and default gateway to 10.85.61.1 ==="
sudo ifconfig eth0 10.85.61.30 netmask 255.255.255.0 up
sudo route add default gw 10.85.61.1

echo "=== Updating and upgrading apt packages ==="
sudo apt-get update
sudo apt-get -y upgrade

echo "=== Installing system dependencies for Python, OpenCV, and GStreamer ==="
sudo apt-get install -y \
    python3-pip \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    python3-opencv \
    libopencv-dev

echo "=== Upgrading pip ==="
python3 -m pip install --upgrade pip

echo "=== Installing Python libraries (robotpy, ntcore, opencv-contrib-python, numpy) ==="
python3 -m pip install --upgrade \
    -U robotpy \
    numpy \

echo "=== Setup completed successfully ==="
