import json
import subprocess
import os
import multiprocessing
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(script_dir, "config.json")

with open(config_file, "r") as file:
    config = json.load(file)

width = config.get("width", 1456)
height = config.get("height", 1088)
framerate = config.get("framerate", 60)
target_ip = config.get("host", "10.85.61.30")  # UDP destination IP
target_port0 = config.get("port0", 5000)       # UDP destination port
target_port1 = config.get("port1", 5001) 

camera_paths = [
    "/base/axi/pcie@120000/rp1/i2c@80000/imx296@1a",
    "/base/axi/pcie@120000/rp1/i2c@88000/imx296@1a"
]

def run_camera(camera_path, port):
    while True:
        print(f"[INFO] Starting GStreamer for Camera {camera_path} on port {port}...")
        gst_command = (
            f"gst-launch-1.0 libcamerasrc camera-name={camera_path} ! "
            f"video/x-raw,format=BGRx,width={width},height={height},framerate={framerate}/1 ! "
            f"videoconvert ! tee name=t "
            # UDP branch: encode and stream the video over UDP
            f"! queue ! x264enc tune=zerolatency speed-preset=ultrafast ! rtph264pay config-interval=1 ! "
            f"udpsink host={target_ip} port={port} "
            # FPS branch: measure FPS and print to console (video output discarded)
            f"t. ! queue ! fpsdisplaysink video-sink=fakesink text-overlay=true sync=false"
        )

        process = subprocess.Popen(
            gst_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        print(f"[INFO] Camera {camera_path} stream is running...")

        while True:
            line = process.stderr.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                print(line.strip())

        exit_code = process.wait()
        print(f"[ERROR] Camera {camera_path} process ended with exit code {exit_code}. Restarting quickly...")
        time.sleep(0.1)

if __name__ == "__main__":
    camera1 = multiprocessing.Process(target=run_camera, args=(camera_paths[0], target_port0))
    camera2 = multiprocessing.Process(target=run_camera, args=(camera_paths[1], target_port1))

    camera1.start()
    camera2.start()

    camera1.join()
    camera2.join()
