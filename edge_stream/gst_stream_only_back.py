import json
import subprocess
import os
import multiprocessing

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(script_dir, "config.json")

# Load JSON configuration file
with open(config_file, "r") as file:
    config = json.load(file)

# Extract parameters
width = config.get("width", 1456)
height = config.get("height", 1088)
framerate = config.get("framerate", 60)
target_ip = config.get("target_ip", "127.0.0.1")  # UDP destination IP
target_port = config.get("target_port", 5000)       # UDP destination port

# Define camera paths (Update these from `libcamera-hello --list-cameras`)
camera_paths = [
    "/base/axi/pcie@120000/rp1/i2c@80000/imx296@1a",
    "/base/axi/pcie@120000/rp1/i2c@88000/imx296@1a"
]

# Function to run GStreamer for each camera
def run_camera(camera_path):
    gst_command = (
        f"gst-launch-1.0 libcamerasrc camera-name={camera_path} ! "
        f"video/x-raw,format=BGRx,width={width},height={height},framerate={framerate}/1 ! "
        f"videoconvert ! tee name=t "
        # UDP branch: encode and stream the video over UDP
        f"! queue ! x264enc tune=zerolatency speed-preset=ultrafast ! rtph264pay config-interval=1 ! "
        f"udpsink host={target_ip} port={target_port} "
        # FPS branch: measure FPS and print to console (video output discarded)
        f"t. ! queue ! fpsdisplaysink video-sink=autovideosink text-overlay=true sync=false"
    )

    print(f"Running GStreamer for Camera {camera_path}:")
    print(gst_command)
    
    process = subprocess.Popen(
        gst_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    
    # Continuously read and print stderr so you can see the FPS stats
    while True:
        line = process.stderr.readline()
        if line == '' and process.poll() is not None:
            break
        if line:
            print(line.strip())
    
    process.wait()

# Run both cameras in parallel
if __name__ == "__main__":
    camera1 = multiprocessing.Process(target=run_camera, args=(camera_paths[0],))
    camera2 = multiprocessing.Process(target=run_camera, args=(camera_paths[1],))

    camera1.start()
    camera2.start()

    camera1.join()
    camera2.join()
