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
    build-essential cmake git pkg-config \
    libjpeg-dev libtiff-dev libpng-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libxvidcore-dev libx264-dev \
    libgtk-3-dev libcanberra-gtk3-module \
    libatlas-base-dev gfortran python3-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-tools gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly librga-dev \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav

echo "=== Upgrading pip ==="
python3 -m pip install --upgrade pip

echo "=== Installing Python libraries (robotpy, ntcore, numpy) ==="
python3 -m pip install --upgrade \
    robotpy \
    numpy 

echo "=== Cloning and building OpenCV from source ==="
cd ~
git clone https://github.com/opencv/opencv.git
git clone https://github.com/opencv/opencv_contrib.git
cd opencv
git checkout 4.x
cd ../opencv_contrib
git checkout 4.x

echo "=== Configuring OpenCV build ==="
cd ~/opencv
mkdir -p build && cd build

cmake -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
      -D WITH_GSTREAMER=ON \
      -D WITH_GSTREAMER_1_0=ON \
      -D WITH_V4L=ON \
      -D WITH_LIBV4L=ON \
      -D WITH_FFMPEG=ON \
      -D WITH_TBB=ON \
      -D CPU_BASELINE="NEON" \
      -D CPU_DISPATCH="NEON_FP16,NEON_BF16,NEON_DOTPROD" \
      -D WITH_OPENMP=ON ..

echo "=== Compiling OpenCV (this will take a while) ==="
make -j$(nproc)

echo "=== Installing OpenCV ==="
sudo make install
sudo ldconfig

echo "=== Verifying OpenCV Installation ==="
python3 -c "import cv2; print('OpenCV Version:', cv2.__version__)"
python3 -c "print(cv2.getBuildInformation())" | grep -i gstreamer

echo "=== Setup completed successfully ==="