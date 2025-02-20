#!/bin/bash

echo "[INFO] Updating package lists..."
sudo apt update

echo "[INFO] Installing GStreamer and libcamera packages..."
sudo apt install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libcamera-apps

if [ $? -eq 0 ]; then
    echo "[INFO] GStreamer installation complete."
else
    echo "[ERROR] GStreamer installation encountered an error."
    exit 1
fi