echo "=== Updating and upgrading apt packages ==="
sudo apt-get update
sudo apt-get -y upgrade

echo "=== Installing Python libraries (robotpy, ntcore, numpy) ==="
python3 -m pip install --break-system-packages --upgrade \
    --break-system-packages robotpy \
    --break-system-packages numpy 