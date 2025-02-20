#!/bin/bash


echo "[INFO] Updating package lists..."
sudo apt update

echo "[INFO] Installing GStreamer, libcamera, and related packages..."

sudo apt install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-libcamera \
    libcamera-apps \
    libcamera-dev \
    python3-libcamera \
    python3-kms++ \
    python3-picamera2

if [ $? -ne 0 ]; then
    echo "[ERROR] Installation of packages failed."
    exit 1
fi

echo "[INFO] GStreamer and libcamera installation complete."